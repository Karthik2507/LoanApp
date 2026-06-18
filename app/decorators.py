from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

def get_user_home_url():
    if not current_user.is_authenticated:
        return url_for("auth.login")
    if current_user.has_permission("page_dashboard"):
        return url_for("dashboard.index")
    if current_user.has_permission("page_loans"):
        return url_for("loans.list_loans")
    if current_user.has_permission("page_reports"):
        return url_for("reports.index")
    if current_user.has_permission("page_schedule"):
        return url_for("schedule.index")
    if current_user.has_permission("page_recalculate"):
        return url_for("recalc.index")
    if current_user.has_permission("page_settings"):
        return url_for("settings.index")
    if current_user.is_super_admin:
        return url_for("super_admin.users")
    return url_for("auth.logout")

def super_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_super_admin:
            flash("Access restricted to Super Administrators only.", "danger")
            return redirect(get_user_home_url())
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission_key):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login"))
            if not current_user.has_permission(permission_key):
                flash("Access restricted: This feature is disabled by the administrator.", "warning")
                return redirect(get_user_home_url())
            return f(*args, **kwargs)
        return decorated_function
    return decorator
