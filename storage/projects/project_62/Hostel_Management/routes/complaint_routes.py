from flask import Blueprint, request, jsonify
from models import Complaint, Student, Room

complaint_bp = Blueprint('complaints', __name__, url_prefix='/api/complaints')

@complaint_bp.route('', methods=['GET'])
def list_complaints():
    status = request.args.get('status', '').strip() or None
    student_id = request.args.get('student_id', type=int)
    room_id = request.args.get('room_id', type=int)
    priority = request.args.get('priority', '').strip() or None

    complaints = Complaint.get_all(status=status, student_id=student_id, room_id=room_id, priority=priority)
    return jsonify({"success": True, "count": len(complaints), "data": complaints}), 200

@complaint_bp.route('/<int:complaint_id>', methods=['GET'])
def get_complaint(complaint_id):
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        return jsonify({"success": False, "message": f"Complaint ID {complaint_id} not found."}), 404
    return jsonify({"success": True, "data": complaint}), 200

@complaint_bp.route('', methods=['POST'])
def create_complaint():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    room_id = data.get('room_id')
    title = str(data.get('title', '')).strip()
    category = str(data.get('category', 'Other')).strip()
    description = str(data.get('description', '')).strip()
    priority = str(data.get('priority', 'Medium')).strip()

    errors = []
    if not student_id:
        errors.append("Student ID is required.")
    if not room_id:
        errors.append("Room ID is required.")
    if not title or len(title) < 5:
        errors.append("Title must be at least 5 characters long.")
    if not description or len(description) < 10:
        errors.append("Please provide a detailed description (minimum 10 characters).")
    if category not in ['Electrical', 'Plumbing', 'Furniture', 'Cleanliness', 'Internet', 'Other']:
        category = 'Other'
    if priority not in ['Low', 'Medium', 'High', 'Urgent']:
        priority = 'Medium'

    if errors:
        return jsonify({"success": False, "message": "Validation failed.", "errors": errors}), 400

    student = Student.get_by_id(student_id)
    if not student:
        return jsonify({"success": False, "message": f"Student ID {student_id} not found."}), 404

    room = Room.get_by_id(room_id)
    if not room:
        return jsonify({"success": False, "message": f"Room ID {room_id} not found."}), 404

    try:
        complaint_id = Complaint.create(
            student_id=int(student_id),
            room_id=int(room_id),
            title=title,
            category=category,
            description=description,
            priority=priority
        )
        created_complaint = Complaint.get_by_id(complaint_id)
        return jsonify({
            "success": True,
            "message": f"Complaint '#{complaint_id}' submitted successfully. Our maintenance team will review it shortly.",
            "data": created_complaint
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Error registering complaint: {str(e)}"}), 500

@complaint_bp.route('/<int:complaint_id>', methods=['PATCH', 'PUT'])
def update_complaint_status(complaint_id):
    complaint = Complaint.get_by_id(complaint_id)
    if not complaint:
        return jsonify({"success": False, "message": f"Complaint ID {complaint_id} not found."}), 404

    data = request.get_json() or {}
    status = data.get('status', complaint['status'])
    admin_remarks = data.get('admin_remarks', complaint.get('admin_remarks', ''))

    if status not in ['Pending', 'In Progress', 'Resolved']:
        return jsonify({"success": False, "message": "Invalid status value. Must be 'Pending', 'In Progress', or 'Resolved'."}), 400

    try:
        Complaint.update_status(complaint_id, status, admin_remarks)
        updated_complaint = Complaint.get_by_id(complaint_id)
        return jsonify({
            "success": True,
            "message": f"Complaint #{complaint_id} updated to '{status}'.",
            "data": updated_complaint
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating complaint: {str(e)}"}), 500
