from app import create_app


def test_create_app_builds_flask_app(tmp_path):
    app = create_app(
        {
            "APP_ENV": "testing",
            "TESTING": True,
            "DATABASE_URL": "postgresql+psycopg://invalid",
            "STORAGE_ROOT": str(tmp_path),
            "JWT_SECRET_KEY": "test-secret",
        }
    )
    assert app.name == "app.factory"
    assert "session_factory" in app.extensions

