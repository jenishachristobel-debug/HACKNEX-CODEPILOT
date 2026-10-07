import re
from flask import Blueprint, request, jsonify, session
from models import Student

student_bp = Blueprint('students', __name__, url_prefix='/api/students')

EMAIL_REGEX = r'^[\w\.-]+@[\w\.-]+\.\w+$'
PHONE_REGEX = r'^[0-9\+\-\s\(\)]{7,20}$'

@student_bp.route('', methods=['GET'])
def list_students():
    search = request.args.get('search', '').strip() or None
    department = request.args.get('department', '').strip() or None
    students = Student.get_all(search=search, department=department)
    return jsonify({"success": True, "count": len(students), "data": students}), 200

@student_bp.route('/<int:student_id>', methods=['GET'])
def get_student(student_id):
    student = Student.get_by_id(student_id)
    if not student:
        return jsonify({"success": False, "message": f"Student with ID {student_id} not found."}), 404
    return jsonify({"success": True, "data": student}), 200

@student_bp.route('/<int:student_id>/room', methods=['GET'])
def get_student_room(student_id):
    room_info = Student.get_current_room_and_roommates(student_id)
    if not room_info:
        return jsonify({"success": True, "allocated": False, "data": None, "message": "No active room allocation found for this student."}), 200
    return jsonify({"success": True, "allocated": True, "data": room_info}), 200

@student_bp.route('', methods=['POST'])
def register_student():
    data = request.get_json() or {}
    roll_number = str(data.get('roll_number', '')).strip().upper()
    full_name = str(data.get('full_name', '')).strip()
    email = str(data.get('email', '')).strip().lower()
    password = str(data.get('password', ''))
    phone = str(data.get('phone', '')).strip()
    department = str(data.get('department', '')).strip()
    gender = str(data.get('gender', '')).strip()
    emergency_contact = str(data.get('emergency_contact', '')).strip() or None

    # Validation
    errors = []
    if not roll_number:
        errors.append("Roll number / Registration number is required.")
    if not full_name or len(full_name) < 2:
        errors.append("Full name is required (minimum 2 characters).")
    if not email or not re.match(EMAIL_REGEX, email):
        errors.append("A valid email address is required.")
    if not password or len(password) < 6:
        errors.append("Password is required and must be at least 6 characters.")
    if not phone or not re.match(PHONE_REGEX, phone):
        errors.append("A valid phone number is required.")
    if not department:
        errors.append("Department / Course is required.")
    if not gender or gender not in ['Male', 'Female', 'Other']:
        errors.append("Gender selection is required (Male, Female, Other).")

    if errors:
        return jsonify({"success": False, "message": "Validation failed.", "errors": errors}), 400

    # Check duplicates
    existing = Student.get_by_roll_or_email(roll_number)
    if existing:
        return jsonify({"success": False, "message": f"A student with Roll Number '{roll_number}' already exists."}), 409

    existing_email = Student.get_by_roll_or_email(email)
    if existing_email:
        return jsonify({"success": False, "message": f"A student with Email '{email}' is already registered."}), 409

    try:
        student_id = Student.create(
            roll_number=roll_number,
            full_name=full_name,
            email=email,
            password=password,
            phone=phone,
            department=department,
            gender=gender,
            emergency_contact=emergency_contact
        )

        new_student = Student.get_by_id(student_id)
        return jsonify({
            "success": True,
            "message": "Student registration successful!",
            "data": new_student
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error during registration: {str(e)}"}), 500
