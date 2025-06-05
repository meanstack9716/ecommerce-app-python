from flask import render_template, request, redirect, session, url_for, jsonify
from app.models import User
from app.models.role import Role
from . import admin_api
from constants import ALL_USER_LIST_WEB_URL, ADD_NEW_USER_LIST_WEB_URL, GENDER_CHOICES, EDIT_USER_WEB_URL
from app.utils.validation import validate_email, validate_required_fields
from app.utils.utils import create_error_response

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
            "id": str(u.get("_id")),
            "first_name": u.get("first_name", "---") or "---",
            "last_name": u.get("last_name", "---") or "---",
            "email": u.get("email", "---") or "---",
            "phone_number": u.get("phone_number", "---") or "---",
            "status": u.get("status", False) or False,
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


@admin_api.route(ADD_NEW_USER_LIST_WEB_URL, methods=['GET', 'POST'])
def add_new_user():
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    if request.method == 'POST':
        try:
            data = request.form
            
            required_fields = ['email', 'first_name', 'status']
            is_valid, validation_errors = validate_required_fields(data, required_fields)
            if not is_valid:
                return create_error_response(validation_errors, 400)
           
            is_valid_email, email_error = validate_email(data['email'])
            if not is_valid_email:
                return create_error_response({"email": email_error}, 400)
           
            if User.objects(email=data['email']).first():
                return create_error_response({'error': 'Email already exists'}, 409)

            user_role = Role.objects(name='user').first()
            if not user_role:
                return create_error_response({'error': 'Default user role not found'}, 400)

            new_user = User(
                email=data['email'],
                first_name=data['first_name'],
                last_name=data.get('last_name', ''),
                phone_number=data.get('phone_number'),
                role=user_role,
                status=data['status']
            )
            
            password = data.get('password', 'defaultPassword123')
            new_user.password = password
            new_user.hash_password()
            
            new_user.save()
            
            return jsonify({
                'message': 'User created successfully',
                'user_id': str(new_user.id)
            }), 201
        
        except Exception as e:
            return create_error_response({'error': str(e)}, 500)
    
    return render_template("admin/users/addNewUser.html")


@admin_api.route(EDIT_USER_WEB_URL, methods=['GET', 'POST'])
def edit_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for('admin_api.login_page'))
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return create_error_response({'error': 'User not found'}, 404)

    if request.method == 'POST':
        try:
            data = {
                'first_name': request.form.get('first_name'),
                'last_name': request.form.get('last_name'),
                'email': request.form.get('email'),
                'phone_number': request.form.get('phone_number'),
                'status': request.form.get('status')
            }

            required_fields = ['email', 'first_name', 'status']
            is_valid, validation_errors = validate_required_fields(data, required_fields)
            if not is_valid:
                return create_error_response(validation_errors, 400)
            
            is_valid_email, email_error = validate_email(data['email'])
            if not is_valid_email:
                return create_error_response({"email": email_error}, 400)

            existing_user = User.objects(email=data['email']).first()
            if existing_user and str(existing_user.id) != user_id:
                return create_error_response({"email": "This email is already registered"}, 400)

            user.update(
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data['email'].lower(),
                phone_number=data['phone_number'] if data['phone_number'] else None,
                status=data['status']
            )

            return jsonify({
                'success': True,
                'message': 'User updated successfully',
                'user_id': str(user.id)
            }), 200

        except Exception as e:
            return create_error_response({'error': str(e)}, 500)

    return render_template("admin/users/editUser.html", user=user)

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