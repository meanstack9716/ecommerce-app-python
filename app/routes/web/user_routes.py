from flask import render_template, request, redirect, session, url_for
from app.models import User
from . import admin_api
from constants import ALL_USER_LIST_WEB_URL
from app.models.seller import Seller
from app.models.role import Role


@admin_api.route(ALL_USER_LIST_WEB_URL)
def all_users():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search = request.args.get('search', '')
    users_data = []

    if search:
        raw_users = User.objects.aggregate([
            {
                "$lookup": {
                    "from": "role",
                    "localField": "role",
                    "foreignField": "_id",
                    "as": "role_info"
                }
            },
            {
                "$unwind": {
                    "path": "$role_info",
                    "preserveNullAndEmptyArrays": True
                }
            },
            {
                "$match": {
                    "$or": [
                        {"first_name": {"$regex": search, "$options": "i"}},
                        {"last_name": {"$regex": search, "$options": "i"}},
                        {"email": {"$regex": search, "$options": "i"}},
                        {"role_info.name": {"$regex": search, "$options": "i"}}
                    ]
                }
            }
        ])
    else:
        raw_users = User.objects()

    for u in raw_users:
        if isinstance(u, dict):
            users_data.append({
                "first_name": u.get("first_name", "---") or "---",
                "last_name": u.get("last_name", "---") or "---",
                "email": u.get("email", "---") or "---",
                "phone_number": u.get("phone_number", "---") or "---",
                "role": u.get("role_info", {}).get("name", "---") if u.get("role_info") else "---"
            })
        else:
            users_data.append({
                "first_name": u.first_name or "---",
                "last_name": u.last_name or "---",
                "email": u.email or "---",
                "phone_number": u.phone_number or "---",
                "role": u.role.name if u.role and u.role.name else "---"
            })

    return render_template("admin/users/allUserList.html", allUsersList=users_data, filters={'search': search})


@admin_api.route('/users/add/seller')
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    return render_template("admin/users/addUser.html")
