from datetime import datetime, date, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    is_verified = db.Column(db.Boolean, default=False, nullable=False)
    is_active_account = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def get_id(self):
        return str(self.id)


class EmailVerificationToken(db.Model):
    __tablename__ = "email_verification_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


class PasswordResetToken(db.Model):
    __tablename__ = "password_reset_tokens"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    token = db.Column(db.String(255), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)


# -----------------------------
# Employee master from Training System
# IMPORTANT:
# แก้ชื่อ table/field ให้ตรงของจริงใน sanko-training-system
# -----------------------------
class Employee(db.Model):
    __tablename__ = "employees"   # <-- แก้ตรงนี้ถ้าตารางจริงไม่ใช่ employees

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), unique=True, nullable=False, index=True)  # <-- ชื่อ field จริง
    full_name = db.Column(db.String(255), nullable=True)                         # <-- ชื่อ field จริง
    department = db.Column(db.String(255), nullable=True)                        # <-- ชื่อ field จริง
    position = db.Column(db.String(255), nullable=True)                          # <-- ชื่อ field จริง
    status = db.Column(db.String(50), nullable=True)                             # <-- Active / Resigned
    resign_date = db.Column(db.Date, nullable=True)                              # <-- ชื่อ field จริง

    @property
    def can_login(self) -> bool:
        return (self.status or "").strip().lower() == "active"

    @property
    def delete_account_due(self) -> bool:
        if (self.status or "").strip().lower() != "resigned":
            return False
        if not self.resign_date:
            return False
        return date.today() >= (self.resign_date + timedelta(days=30))
