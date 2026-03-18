import os
from datetime import date, timedelta

from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, login_required, current_user

from models import db, User, Employee
from auth import auth_bp

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///sanko_connect.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.init_app(app)

app.register_blueprint(auth_bp)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_employee_context():
    employee = None
    if current_user.is_authenticated:
        employee = Employee.query.filter_by(emp_id=current_user.emp_id).first()
    return {"current_employee": employee}


@app.route("/")
def root():
    return redirect(url_for("dashboard"))


@app.route("/dashboard")
@login_required
def dashboard():
    employee = Employee.query.filter_by(emp_id=current_user.emp_id).first()
    if not employee:
        flash("ไม่พบข้อมูลพนักงานในระบบหลัก", "danger")
        return redirect(url_for("auth.logout"))

    if (employee.status or "").strip().lower() != "active":
        flash("บัญชีนี้ไม่สามารถเข้าใช้งานได้ เนื่องจากพนักงานพ้นสภาพแล้ว", "danger")
        return redirect(url_for("auth.logout"))

    return render_template("dashboard/index.html", employee=employee)


@app.route("/profile")
@login_required
def profile():
    employee = Employee.query.filter_by(emp_id=current_user.emp_id).first()
    if not employee:
        flash("ไม่พบข้อมูลพนักงานในระบบหลัก", "danger")
        return redirect(url_for("auth.logout"))

    return render_template("profile/index.html", employee=employee)


# สำหรับรอบแรก ใช้ route นี้เช็กคนลาออกครบ 30 วันแบบ manual ได้
@app.route("/admin/cleanup-resigned-users")
def cleanup_resigned_users():
    employees = Employee.query.filter_by(status="Resigned").all()
    deleted_count = 0

    for emp in employees:
        if emp.resign_date and date.today() >= (emp.resign_date + timedelta(days=30)):
            user = User.query.filter_by(emp_id=emp.emp_id).first()
            if user:
                db.session.delete(user)
                deleted_count += 1

    db.session.commit()
    return f"Deleted {deleted_count} resigned user account(s)."


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)
