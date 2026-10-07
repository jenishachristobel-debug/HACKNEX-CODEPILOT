from flask import Blueprint, request, jsonify, session
from models import Admin, Student

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password are required."}), 400

    admin = Admin.get_by_username(username)
    if not admin or not Admin.verify_password(admin['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid admin username or password."}), 401

    # Store in session
    session['user_id'] = admin['admin_id']
    session['role'] = 'admin'
    session['username'] = admin['username']
    session['full_name'] = admin['full_name']

    return jsonify({
        "success": True,
        "message": f"Welcome back, {admin['full_name']}!",
        "user": {
            "admin_id": admin['admin_id'],
            "username": admin['username'],
            "full_name": admin['full_name'],
            "email": admin['email'],
            "role": "admin",
            "title": admin.get('role', 'Chief Warden')
        }
    }), 200

@auth_bp.route('/student/login', methods=['POST'])
def student_login():
    data = request.get_json() or {}
    identifier = data.get('identifier', '').strip()
    password = data.get('password', '')

    if not identifier or not password:
        return jsonify({"success": False, "message": "Roll Number/Email and password are required."}), 400

    student = Student.get_by_roll_or_email(identifier)
    if not student or not Student.verify_password(student['password_hash'], password):
        return jsonify({"success": False, "message": "Invalid credentials. Please verify your Roll Number/Email and password."}), 401

    session['user_id'] = student['student_id']
    session['role'] = 'student'
    session['roll_number'] = student['roll_number']
    session['full_name'] = student['full_name']

    return jsonify({
        "success": True,
        "message": f"Welcome back, {student['full_name']}!",
        "user": {
            "student_id": student['student_id'],
            "roll_number": student['roll_number'],
            "full_name": student['full_name'],
            "email": student['email'],
            "department": student['department'],
            "gender": student['gender'],
            "role": "student"
        }
    }), 200

@auth_bp.route('/current-user', methods=['GET'])
def get_current_user():
    user_id = session.get('user_id')
    role = session.get('role')

    if not user_id or not role:
        return jsonify({"authenticated": False, "user": None}), 200

    if role == 'admin':
        admin = Admin.get_by_id(user_id)
        if admin:
            admin['role'] = 'admin'
            return jsonify({"authenticated": True, "user": admin}), 200
    elif role == 'student':
        student = Student.get_by_id(user_id)
        if student:
            student_info = {
                "student_id": student["student_id"],
                "roll_number": student["roll_number"],
                "full_name": student["full_name"],
                "email": student["email"],
                "department": student["department"],
                "phone": student["phone"],
                "gender": student["gender"],
                "booking_id": student["booking_id"],
                "room_id": student["room_id"],
                "room_number": student["room_number"],
                "block_name": student["block_name"],
                "booking_status": student["booking_status"],
                "role": "student"
            }
            return jsonify({"authenticated": True, "user": student_info}), 200

    session.clear()
    return jsonify({"authenticated": False, "user": None}), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True, "message": "Successfully logged out."}), 200
