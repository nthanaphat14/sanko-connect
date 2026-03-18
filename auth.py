import secrets
import os
import secrets
from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, Employee, EmailVerificationToken, PasswordResetToken
from email_utils import send_email

auth_bp = Blueprint("auth", __name__)


def build_url(path: str) -> str:
    base = os.getenv("APP_BASE_URL", "http://127.0.0.1:5000").rstrip("/")
    return f"{base}{path}"


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()

        if not emp_id or not email or not password:
            flash("กรุณากรอกข้อมูลให้ครบ", "danger")
            return redirect(url_for("auth.register"))

        emp_id_input = request.form.get("emp_id")

        # 🔥 แปลงรหัสพนักงาน
        emp_id = emp_id_input.strip().upper()

        if emp_id.isdigit():
            emp_id = f"M{emp_id.zfill(7)}"

        # 🔍 หา employee
        employee = Employee.query.filter_by(emp_id=emp_id).first()

        print("INPUT:", emp_id_input)
        print("NORMALIZED:", emp_id)
        print("RESULT:", employee)

        if not employee:
            flash("ไม่พบรหัสพนักงานในระบบ", "danger")
            return redirect(url_for("auth.register"))

        if (employee.status or "").strip().lower() != "active":
            flash("ไม่สามารถสมัครได้ เนื่องจากพนักงานไม่อยู่ในสถานะ Active", "danger")
            return redirect(url_for("auth.register"))

        existing_emp = User.query.filter_by(emp_id=emp_id).first()
        if existing_emp:
            flash("รหัสพนักงานนี้ถูกใช้งานแล้ว", "warning")
            return redirect(url_for("auth.login"))

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("อีเมลนี้ถูกใช้งานแล้ว", "warning")
            return redirect(url_for("auth.login"))

        user = User(emp_id=emp_id, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        token = secrets.token_urlsafe(32)
        verify = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(verify)
        db.session.commit()

        verify_link = build_url(f"/verify-email/{token}")
        send_email(
            subject="ยืนยันอีเมล SANKO CONNECT",
            recipient=user.email,
            html_body=f"""
            <p>สวัสดี</p>
            <p>กรุณากดลิงก์ด้านล่างเพื่อยืนยันอีเมลของคุณ:</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>ลิงก์นี้มีอายุ 24 ชั่วโมง</p>
            """
        )

        flash("สมัครสำเร็จ กรุณาตรวจสอบอีเมลเพื่อยืนยันตัวตน", "success")
        return redirect(url_for("auth.verify_pending"))

    return render_template("auth/register.html")


@auth_bp.route("/verify-pending")
def verify_pending():
    return render_template("auth/verify_pending.html")


@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    record = EmailVerificationToken.query.filter_by(token=token, used=False).first()
    if not record or record.expires_at < datetime.utcnow():
        flash("ลิงก์ยืนยันอีเมลไม่ถูกต้องหรือหมดอายุ", "danger")
        return redirect(url_for("auth.login"))

    user = User.query.get(record.user_id)
    if not user:
        flash("ไม่พบบัญชีผู้ใช้", "danger")
        return redirect(url_for("auth.login"))

    user.is_verified = True
    record.used = True
    db.session.commit()

    flash("ยืนยันอีเมลสำเร็จ กรุณาเข้าสู่ระบบ", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/resend-verification", methods=["GET", "POST"])
def resend_verification():
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        email = request.form.get("email", "").strip().lower()

        user = User.query.filter_by(emp_id=emp_id, email=email).first()

        if not user:
            flash("ไม่พบบัญชีผู้ใช้ตามข้อมูลที่ระบุ", "danger")
            return redirect(url_for("auth.resend_verification"))

        if user.is_verified:
            flash("บัญชีนี้ยืนยันอีเมลแล้ว สามารถเข้าสู่ระบบได้เลย", "info")
            return redirect(url_for("auth.login"))

        token = secrets.token_urlsafe(32)
        verify = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(verify)
        db.session.commit()

        verify_link = build_url(f"/verify-email/{token}")
        send_email(
            subject="ส่งอีเมลยืนยันใหม่ - SANKO CONNECT",
            recipient=user.email,
            html_body=f"""
            <p>คุณได้ร้องขอส่งอีเมลยืนยันใหม่</p>
            <p>กรุณากดลิงก์ด้านล่างเพื่อยืนยันอีเมล:</p>
            <p><a href="{verify_link}">{verify_link}</a></p>
            <p>ลิงก์นี้มีอายุ 24 ชั่วโมง</p>
            """
        )

        flash("ระบบส่งอีเมลยืนยันใหม่แล้ว กรุณาตรวจสอบอีเมล", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/resend_verification.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        password = request.form.get("password", "").strip()

        user = User.query.filter_by(emp_id=emp_id).first()
        if not user or not user.check_password(password):
            flash("รหัสพนักงานหรือรหัสผ่านไม่ถูกต้อง", "danger")
            return redirect(url_for("auth.login"))

        if not user.is_verified:
            flash("กรุณายืนยันอีเมลก่อนเข้าสู่ระบบ", "warning")
            return redirect(url_for("auth.login"))

        if not user.is_active_account:
            flash("บัญชีนี้ถูกปิดการใช้งาน", "danger")
            return redirect(url_for("auth.login"))

        employee = Employee.query.filter_by(emp_id=user.emp_id).first()
        if not employee:
            flash("ไม่พบข้อมูลพนักงานในระบบหลัก", "danger")
            return redirect(url_for("auth.login"))

        emp_status = (employee.status or "").strip().lower()
        if emp_status != "active":
            logout_user()
            session.clear()
            flash("บัญชีนี้ไม่สามารถเข้าใช้งานได้ เนื่องจากพนักงานพ้นสภาพแล้ว", "danger")
            return redirect(url_for("auth.login"))

        login_user(user)
        return redirect(url_for("dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear()
    flash("ออกจากระบบเรียบร้อย", "success")
    return redirect(url_for("auth.login"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        emp_id = request.form.get("emp_id", "").strip()
        email = request.form.get("email", "").strip().lower()

        user = User.query.filter_by(emp_id=emp_id, email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            reset = PasswordResetToken(
                user_id=user.id,
                token=token,
                expires_at=datetime.utcnow() + timedelta(hours=1)
            )
            db.session.add(reset)
            db.session.commit()

            reset_link = build_url(f"/reset-password/{token}")
            send_email(
                subject="รีเซ็ตรหัสผ่าน SANKO CONNECT",
                recipient=user.email,
                html_body=f"""
                <p>กรุณากดลิงก์ด้านล่างเพื่อรีเซ็ตรหัสผ่าน:</p>
                <p><a href="{reset_link}">{reset_link}</a></p>
                <p>ลิงก์นี้มีอายุ 1 ชั่วโมง</p>
                """
            )

        flash("หากข้อมูลถูกต้อง ระบบได้ส่งลิงก์รีเซ็ตรหัสผ่านไปยังอีเมลแล้ว", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    record = PasswordResetToken.query.filter_by(token=token, used=False).first()
    if not record or record.expires_at < datetime.utcnow():
        flash("ลิงก์รีเซ็ตรหัสผ่านไม่ถูกต้องหรือหมดอายุ", "danger")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        password = request.form.get("password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()

        if not password or not confirm_password:
            flash("กรุณากรอกรหัสผ่านให้ครบ", "danger")
            return redirect(request.url)

        if password != confirm_password:
            flash("รหัสผ่านไม่ตรงกัน", "danger")
            return redirect(request.url)

        user = User.query.get(record.user_id)
        if not user:
            flash("ไม่พบบัญชีผู้ใช้", "danger")
            return redirect(url_for("auth.login"))

        user.set_password(password)
        record.used = True
        db.session.commit()

        flash("เปลี่ยนรหัสผ่านเรียบร้อย กรุณาเข้าสู่ระบบ", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html")
