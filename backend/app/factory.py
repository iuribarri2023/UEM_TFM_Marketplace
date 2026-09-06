from __future__ import annotations

import logging
from http import HTTPStatus
from pathlib import Path

from flask import Flask, Response, g, jsonify, redirect
from flask_cors import CORS
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app.api.v1 import api_v1
from app.core.config import load_settings
from app.core.exceptions import AppError
from app.core.logging import configure_logging
from app.db.session import create_db_engine, create_session_factory
from app.infrastructure.bim.ifc import IfcOpenShellAdapter
from app.infrastructure.storage.local import LocalFileStorage
from app.schemas.envelope import error_response

logger = logging.getLogger(__name__)
OPENAPI_PATH = Path(__file__).resolve().parent.parent / "docs" / "openapi.yaml"


def create_app(config: dict | None = None) -> Flask:
    configure_logging()
    settings = load_settings(config)
    app = Flask(__name__)
    app.config.update(
        SETTINGS=settings,
        MAX_CONTENT_LENGTH=settings.max_upload_size,
        TESTING=settings.testing,
    )

    engine = create_db_engine(settings)
    app.extensions["db_engine"] = engine
    app.extensions["session_factory"] = create_session_factory(engine)
    app.extensions["file_storage"] = LocalFileStorage(
        settings.storage_root, settings.max_upload_size
    )
    app.extensions["bim_adapter"] = IfcOpenShellAdapter()

    if settings.cors_origins:
        CORS(app, origins=settings.cors_origins)

    @app.before_request
    def open_session() -> None:
        g.db = app.extensions["session_factory"]()

    @app.teardown_request
    def close_session(exc: BaseException | None) -> None:
        session = getattr(g, "db", None)
        if session is None:
            return
        if exc:
            session.rollback()
        session.close()

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/")
    def index():
        return redirect("/docs")

    @app.get("/openapi.yaml")
    def openapi_yaml():
        return Response(OPENAPI_PATH.read_text(encoding="utf-8"), mimetype="application/yaml")

    @app.get("/docs")
    def swagger_ui():
        return Response(
            """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>AVRA VIVA API Docs</title>
    <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
  </head>
  <body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
    <script>
      window.onload = () => {
        window.ui = SwaggerUIBundle({
          url: "/openapi.yaml",
          dom_id: "#swagger-ui",
          deepLinking: true,
          persistAuthorization: true
        });
      };
    </script>
  </body>
</html>
""".strip(),
            mimetype="text/html",
        )

    app.register_blueprint(api_v1)
    register_error_handlers(app)
    return app


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(AppError)
    def handle_app_error(exc: AppError):
        return jsonify(error_response(exc.code, exc.message)), exc.status_code

    @app.errorhandler(PydanticValidationError)
    def handle_validation_error(exc: PydanticValidationError):
        first_error = exc.errors(include_url=False)[0]
        return (
            jsonify(error_response("VALIDATION_FAILED", first_error["msg"])),
            HTTPStatus.BAD_REQUEST,
        )

    @app.errorhandler(ValueError)
    def handle_value_error(exc: ValueError):
        return jsonify(error_response("VALIDATION_FAILED", str(exc))), HTTPStatus.BAD_REQUEST

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(_exc: IntegrityError):
        session = getattr(g, "db", None)
        if session is not None:
            session.rollback()
        return (
            jsonify(error_response("INTEGRITY_ERROR", "Database constraint violation.")),
            HTTPStatus.CONFLICT,
        )

    @app.errorhandler(RequestEntityTooLarge)
    def handle_too_large(_exc: RequestEntityTooLarge):
        return (
            jsonify(error_response("FILE_TOO_LARGE", "Request exceeds MAX_UPLOAD_SIZE.")),
            HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
        )

    @app.errorhandler(404)
    def handle_not_found(_exc):
        return jsonify(error_response("NOT_FOUND", "Endpoint not found.")), HTTPStatus.NOT_FOUND

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        status = exc.code or HTTPStatus.INTERNAL_SERVER_ERROR
        code = (exc.name or "HTTP_ERROR").upper().replace(" ", "_")
        return jsonify(error_response(code, exc.description)), status

    @app.errorhandler(Exception)
    def handle_unexpected_error(exc: Exception):
        if app.testing:
            raise exc
        logger.exception("Unhandled application error", exc_info=exc)
        return (
            jsonify(error_response("INTERNAL_SERVER_ERROR", "Unexpected server error.")),
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
