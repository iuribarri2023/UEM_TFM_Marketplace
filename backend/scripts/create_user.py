from __future__ import annotations

import argparse
import getpass

from app.core.config import load_settings
from app.core.security import hash_password
from app.db.models.commercial import User
from app.db.session import create_db_engine, create_session_factory
from app.db.transaction import transactional
from app.repositories.commercial import ManufacturerRepository, UserRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an AVRA VIVA administrator/manufacturer user.")
    parser.add_argument("email")
    parser.add_argument("--role", required=True, choices=("ADMIN", "MANUFACTURER"))
    parser.add_argument("--manufacturer-code")
    args = parser.parse_args()

    if args.role == "MANUFACTURER" and not args.manufacturer_code:
        parser.error("--manufacturer-code is required for MANUFACTURER users")
    if args.role == "ADMIN" and args.manufacturer_code:
        parser.error("ADMIN users must not have --manufacturer-code")

    password = getpass.getpass("Password: ")
    if len(password) < 12:
        parser.error("Password must contain at least 12 characters")

    settings = load_settings()
    engine = create_db_engine(settings)
    session_factory = create_session_factory(engine)
    try:
        with session_factory() as session, transactional(session):
            users = UserRepository(session)
            if users.get_by_email(args.email):
                raise SystemExit("User already exists")

            manufacturer_id = None
            if args.manufacturer_code:
                manufacturer = ManufacturerRepository(session).get_by_code(args.manufacturer_code)
                if not manufacturer:
                    raise SystemExit("Manufacturer does not exist; import/create it first")
                manufacturer_id = manufacturer.id

            user = User(
                email=args.email.lower(),
                password_hash=hash_password(password),
                role=args.role,
                manufacturer_id=manufacturer_id,
                is_active=True,
            )
            users.add(user)
            session.flush()
            print(f"Created {args.role} user {user.email} ({user.id})")
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
