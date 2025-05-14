from flask import render_template, request, redirect, session, url_for, jsonify
from app.models import User
from app.models.role import Role
from . import admin_api
from constants import ALL_USER_LIST_WEB_URL

def fetch_users_data(search='', role_filter='', page=1, per_page=10):
    roles = [{'name': role.name} for role in Role.objects.only('name')]

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

    count_pipeline = pipeline.copy()
    count_pipeline.append({"$count": "total"})
    total_count = next(User.objects.aggregate(*count_pipeline), {}).get('total', 0)

    pipeline.extend([
        {"$skip": (page - 1) * per_page},
        {"$limit": per_page}
    ])

    raw_users = User.objects.aggregate(*pipeline)
    users_data = []

    for idx, u in enumerate(raw_users, start=(page - 1) * per_page + 1):
        users_data.append({
            "index": idx,
            "first_name": u.get("first_name", "---") or "---",
            "last_name": u.get("last_name", "---") or "---",
            "email": u.get("email", "---") or "---",
            "phone_number": u.get("phone_number", "---") or "---",
            "role": u.get("role_info", {}).get("name", "---") if u.get("role_info") else "---"
        })

    total_pages = (total_count + per_page - 1) // per_page

    return {
        'users': users_data,
        'roles': roles,
        'pagination': {
            'page': page,
            'pages': total_pages,
            'has_prev': page > 1,
            'has_next': page < total_pages,
            'prev_num': page - 1 if page > 1 else None,
            'next_num': page + 1 if page < total_pages else None,
            'total': total_count,
            'per_page': per_page
        }
    }

@admin_api.route(ALL_USER_LIST_WEB_URL)
def all_users():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))

    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_users_data(search, role_filter, page, per_page)

    return render_template(
        "admin/users/allUserList.html",
        allUsersList=data['users'],
        filters={'search': search, 'role': role_filter},
        roles=[{'name': role['name']} for role in data['roles']],
        pagination=data['pagination']
    )

@admin_api.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '').strip()
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('limit', 10))

    data = fetch_users_data(search, role_filter, page, per_page)

    return jsonify({
        'users': data['users'],
        'pagination': data['pagination'],
        'roles': data['roles']
    })