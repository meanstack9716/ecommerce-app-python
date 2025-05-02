from flask import render_template, session, redirect, url_for, request
from . import admin_api
from app.models import User
from constants import Login_WEB_URL, SIGNUP_WEB_URL, FORGOT_PASSWORD_WEB_URL, VERIFY_OTP_WEB_URL, RESET_PASSWORD_WEB_URL


@admin_api.route(Login_WEB_URL, methods=["GET", "POST"])
def login_page():
    if 'access_token' in session:
        return redirect(url_for('admin_api.dashboard'))

    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']
        user = User.objects(username=username, password=password).first()

        if user:
            session['access_token'] = user.access_token
            session['user_id'] = str(user.id)
            return redirect(url_for('admin_api.dashboard'))
        else:
            return render_template("admin/authFlow/login.html", error="Invalid credentials")

    return render_template("admin/authFlow/login.html")


@admin_api.route(SIGNUP_WEB_URL)
def signup_page():
    return render_template('admin/authFlow/signup.html')


@admin_api.route(FORGOT_PASSWORD_WEB_URL)
def forgot_password():
    return render_template('admin/authFlow/forgot_password.html')


@admin_api.route(VERIFY_OTP_WEB_URL)
def verify_otp():
    return render_template('admin/authFlow/verify-otp.html')


@admin_api.route(RESET_PASSWORD_WEB_URL)
def reset_password():
    return render_template('admin/authFlow/reset-password.html')
