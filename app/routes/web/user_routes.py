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

    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()

    users_data = []

    # Fetch all roles to populate the dropdown
    roles = list(Role.objects.only('name'))

    pipeline = [
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
        }
    ]

    match_conditions = []

    if search:
        match_conditions.append({
            "$or": [
                {"first_name": {"$regex": search, "$options": "i"}},
                {"last_name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
                {"phone_number": {"$regex": search, "$options": "i"}},
            ]
        })

    if role_filter:
        match_conditions.append({
            "role_info.name": role_filter
        })

    if match_conditions:
        pipeline.append({
            "$match": {
                "$and": match_conditions
            }
        })

    raw_users = User.objects.aggregate(pipeline) if match_conditions else User.objects.aggregate(pipeline)

    for u in raw_users:
        users_data.append({
            "first_name": u.get("first_name", "---") or "---",
            "last_name": u.get("last_name", "---") or "---",
            "email": u.get("email", "---") or "---",
            "phone_number": u.get("phone_number", "---") or "---",
            "role": u.get("role_info", {}).get("name", "---") if u.get("role_info") else "---"
        })

    return render_template("admin/users/allUserList.html", allUsersList=users_data, filters={'search': search, 'role': role_filter}, roles=roles)
