from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, UserPermission, ActivityLog
from app.forms import RegisterForm
from app.decorators import super_admin_required

super_admin_bp = Blueprint("super_admin", __name__, url_prefix="/super-admin")

ALL_PERMISSIONS = {
    "Pages": [
        ("page_dashboard", "Dashboard Page"),
        ("page_loans", "Loans Page"),
        ("page_schedule", "Schedule Page"),
        ("page_recalculate", "Recalculate Page"),
        ("page_reports", "Reports Page"),
        ("page_settings", "Settings Page"),
    ],
    "Charts": [
        ("chart_dashboard_dist", "Dashboard: Loan Status Distribution Chart"),
        ("chart_dashboard_cat", "Dashboard: Category Breakdown Chart"),
        ("chart_dashboard_cash", "Dashboard: Cash Flow Forecast Chart"),
        ("chart_dashboard_paid", "Dashboard: Paid vs Outstanding Chart"),
        ("chart_dashboard_debt", "Dashboard: Debt Snowball Payoff Chart"),
        ("chart_dashboard_burden", "Dashboard: Debt Burden Ratio Gauge"),
        ("chart_schedule_amort", "Schedule: Amortization Chart"),
        ("chart_reports_risk", "Reports: Risk & Exposure Chart"),
        ("chart_recalc_sandbox", "Recalculate: Sandbox Compare Chart"),
    ],
    "Tables": [
        ("table_dashboard_loans", "Dashboard: Active Loans Table"),
        ("table_loans_list", "Loans Page: Loans Table"),
        ("table_schedule_installments", "Schedule Page: Installments Table"),
        ("table_details_history", "Loan Details: Payment Logs & History"),
        ("table_reports_activity", "Reports Page: Activity Logs Table"),
    ],
    "Features": [
        ("feature_chatbot", "Gemini Chat Assistant"),
        ("feature_bulk_upload", "Bulk CSV Loans Upload"),
        ("feature_downloads", "Amortization CSV/PDF Downloads"),
        ("feature_backup_restore", "Settings: Database Backup & Restore"),
    ]
}

@super_admin_bp.route("/users")
@login_required
@super_admin_required
def users():
    users_list = User.query.filter(User.id != current_user.id).order_by(User.id.desc()).all()
    return render_template("super_admin/users.html", users=users_list)

@super_admin_bp.route("/users/<int:user_pk>/permissions", methods=["GET", "POST"])
@login_required
@super_admin_required
def permissions(user_pk):
    user = User.query.get_or_404(user_pk)
    if user.is_super_admin:
        flash("Super Administrators always have full access.", "info")
        return redirect(url_for("super_admin.users"))

    if request.method == "POST":
        # Clear existing permissions for this user
        UserPermission.query.filter_by(user_id=user.id).delete()
        
        # Collect allowed permissions from post data
        allowed_keys = request.form.getlist("allowed_permissions")
        
        # Insert permissions configurations
        for category, perms in ALL_PERMISSIONS.items():
            for key, name in perms:
                is_allowed = key in allowed_keys
                db.session.add(UserPermission(user_id=user.id, permission_key=key, is_allowed=is_allowed))
                
        db.session.add(ActivityLog(
            user_id=current_user.id,
            action="UPDATE_PERMISSIONS",
            detail=f"Updated permissions for user {user.username} ({user.full_name})"
        ))
        db.session.commit()
        flash(f"Permissions updated successfully for {user.username}.", "success")
        return redirect(url_for("super_admin.users"))

    # Load current allowed permissions
    allowed_perms = set()
    for key_tuple in UserPermission.query.filter_by(user_id=user.id, is_allowed=True).all():
        allowed_perms.add(key_tuple.permission_key)
        
    # If no permission records exist yet, fallback to all True
    has_records = UserPermission.query.filter_by(user_id=user.id).first() is not None
    if not has_records:
        for cat, perms in ALL_PERMISSIONS.items():
            for key, name in perms:
                allowed_perms.add(key)

    return render_template("super_admin/permissions.html", user=user, permissions_groups=ALL_PERMISSIONS, allowed_perms=allowed_perms)

@super_admin_bp.route("/create-admin", methods=["GET", "POST"])
@login_required
@super_admin_required
def create_admin():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter((User.username == form.username.data) | (User.email == form.email.data.lower())).first():
            flash("Username or email already in use.", "danger")
            return render_template("super_admin/create_admin.html", form=form)
        user = User(
            full_name=form.full_name.data.strip(),
            username=form.username.data.strip(),
            email=form.email.data.strip().lower(),
            role="super_admin"
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        db.session.add(ActivityLog(
            user_id=current_user.id,
            action="CREATE_SUPER_ADMIN",
            detail=f"Created Super Admin account: {user.username}"
        ))
        db.session.commit()
        flash(f"Super Admin account '{user.username}' created successfully.", "success")
        return redirect(url_for("super_admin.users"))
    return render_template("super_admin/create_admin.html", form=form)
