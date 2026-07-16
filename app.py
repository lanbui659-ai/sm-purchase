import os
from datetime import datetime
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key-change-me")

database_url = os.environ.get("DATABASE_URL", "sqlite:///purchase_requests.db")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="employee")


class PurchaseRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(30), unique=True)
    department = db.Column(db.String(100), nullable=False)
    requester_name = db.Column(db.String(150), nullable=False)
    item_name = db.Column(db.String(255), nullable=False)
    specification = db.Column(db.Text)
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    estimated_budget = db.Column(db.Float, default=0)
    priority = db.Column(db.String(30), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    required_date = db.Column(db.Date)
    supplier_suggestion = db.Column(db.String(255))
    status = db.Column(db.String(30), nullable=False, default="Chờ duyệt")
    manager_comment = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    approved_by = db.Column(db.Integer, db.ForeignKey("user.id"))
    approved_at = db.Column(db.DateTime)

    creator = db.relationship("User", foreign_keys=[created_by])
    approver = db.relationship("User", foreign_keys=[approved_by])


def login_required(role=None):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Bạn không có quyền thực hiện chức năng này.", "error")
                return redirect(url_for("index"))
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def seed_users():
    if User.query.count() == 0:
        db.session.add_all([
            User(
                username=os.environ.get("EMPLOYEE_USERNAME", "nhanvien"),
                password_hash=generate_password_hash(
                    os.environ.get("EMPLOYEE_PASSWORD", "123456")
                ),
                full_name="Nhân viên mẫu",
                role="employee",
            ),
            User(
                username=os.environ.get("MANAGER_USERNAME", "sep"),
                password_hash=generate_password_hash(
                    os.environ.get("MANAGER_PASSWORD", "123456")
                ),
                full_name="Người phê duyệt",
                role="manager",
            ),
        ])
        db.session.commit()


@app.cli.command("init-db")
def init_db_command():
    db.create_all()
    seed_users()
    print("Database initialized.")


@app.get("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session.clear()
            session.update(
                user_id=user.id,
                username=user.username,
                full_name=user.full_name,
                role=user.role,
            )
            return redirect(url_for("index"))
        flash("Sai tài khoản hoặc mật khẩu.", "error")
    return render_template("login.html")


@app.get("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.get("/")
@login_required()
def index():
    query = PurchaseRequest.query.order_by(PurchaseRequest.id.desc())
    if session["role"] != "manager":
        query = query.filter_by(created_by=session["user_id"])
    return render_template("index.html", rows=query.all())


@app.route("/request/new", methods=["GET", "POST"])
@login_required()
def new_request():
    if request.method == "POST":
        required_date = request.form.get("required_date")
        row = PurchaseRequest(
            department=request.form["department"].strip(),
            requester_name=request.form["requester_name"].strip(),
            item_name=request.form["item_name"].strip(),
            specification=request.form.get("specification", "").strip(),
            quantity=float(request.form["quantity"]),
            unit=request.form["unit"].strip(),
            estimated_budget=float(request.form.get("estimated_budget") or 0),
            priority=request.form["priority"],
            reason=request.form["reason"].strip(),
            required_date=(
                datetime.strptime(required_date, "%Y-%m-%d").date()
                if required_date else None
            ),
            supplier_suggestion=request.form.get("supplier_suggestion", "").strip(),
            created_by=session["user_id"],
        )
        db.session.add(row)
        db.session.flush()
        row.request_code = f"PR-{datetime.now().year}-{row.id:04d}"
        db.session.commit()
        flash("Đã gửi yêu cầu mua hàng.", "success")
        return redirect(url_for("index"))
    return render_template("new_request.html")


@app.get("/request/<int:request_id>")
@login_required()
def request_detail(request_id):
    row = db.get_or_404(PurchaseRequest, request_id)
    if session["role"] != "manager" and row.created_by != session["user_id"]:
        flash("Bạn không có quyền xem yêu cầu này.", "error")
        return redirect(url_for("index"))
    return render_template("detail.html", row=row)


def update_approval(request_id, status, require_comment=False):
    row = db.get_or_404(PurchaseRequest, request_id)
    comment = request.form.get("manager_comment", "").strip()
    if require_comment and not comment:
        flash("Cần nhập lý do từ chối.", "error")
        return redirect(url_for("request_detail", request_id=request_id))
    row.status = status
    row.manager_comment = comment
    row.approved_by = session["user_id"]
    row.approved_at = datetime.utcnow()
    db.session.commit()
    flash(f"Đã cập nhật trạng thái: {status}.", "success")
    return redirect(url_for("request_detail", request_id=request_id))


@app.post("/request/<int:request_id>/approve")
@login_required("manager")
def approve_request(request_id):
    return update_approval(request_id, "Đã duyệt")


@app.post("/request/<int:request_id>/reject")
@login_required("manager")
def reject_request(request_id):
    return update_approval(request_id, "Từ chối", require_comment=True)


@app.post("/request/<int:request_id>/complete")
@login_required("manager")
def complete_request(request_id):
    return update_approval(request_id, "Hoàn thành")


with app.app_context():
    db.create_all()
    seed_users()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)
