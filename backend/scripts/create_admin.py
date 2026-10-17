import getpass

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User


def create_admin():
    print("=== Dock Appointment Scheduling ===")
    print("Initial administrator setup\n")

    email = input("Admin email: ").strip().lower()
    full_name = input("Full name: ").strip()

    password = getpass.getpass("Password: ")
    password_confirmation = getpass.getpass("Confirm password: ")

    if not email or not full_name:
        print("Error: Email and full name are required.")
        return

    if len(password) < 8:
        print("Error: Password must contain at least 8 characters.")
        return

    if password != password_confirmation:
        print("Error: Passwords do not match.")
        return

    db = SessionLocal()

    try:
        existing_admin = db.scalar(
            select(User).where(User.role == "ADMIN")
        )

        if existing_admin:
            print("Error: An administrator already exists.")
            return

        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print("Error: This email is already registered.")
            return

        admin = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role="ADMIN",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("\nAdministrator created successfully.")
        print(f"User ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Role: {admin.role}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()