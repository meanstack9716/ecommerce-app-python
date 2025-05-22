from flask import render_template, session, redirect, url_for, request, jsonify
from . import admin_api
from app.models import User
from constants import ADD_PROMO_CODE_WEB_URL
from app.utils.utils import create_error_response


@admin_api.route(ADD_PROMO_CODE_WEB_URL)
def add_promo_code():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template('admin/promo_codes/add_promo_code.html')