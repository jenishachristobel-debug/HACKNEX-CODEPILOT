from flask import Blueprint, request, jsonify
from models import Booking, Room, Student

booking_bp = Blueprint('bookings', __name__, url_prefix='/api/bookings')

@booking_bp.route('', methods=['GET'])
def list_bookings():
    status = request.args.get('status', '').strip() or None
    student_id = request.args.get('student_id', type=int)
    room_id = request.args.get('room_id', type=int)

    bookings = Booking.get_all(status=status, student_id=student_id, room_id=room_id)
    return jsonify({"success": True, "count": len(bookings), "data": bookings}), 200

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    booking = Booking.get_by_id(booking_id)
    if not booking:
        return jsonify({"success": False, "message": f"Booking ID {booking_id} not found."}), 404
    return jsonify({"success": True, "data": booking}), 200

@booking_bp.route('/allocate', methods=['POST'])
def allocate_room():
    data = request.get_json() or {}
    student_id = data.get('student_id')
    room_id = data.get('room_id')
    allocation_date = data.get('allocation_date')
    remarks = data.get('remarks', 'Allocated via Hostel Management Portal')

    if not student_id or not room_id:
        return jsonify({"success": False, "message": "Both student_id and room_id are required."}), 400

    # Verify student exists
    student = Student.get_by_id(student_id)
    if not student:
        return jsonify({"success": False, "message": f"Student ID {student_id} not found."}), 404

    # Verify room exists
    room = Room.get_by_id(room_id)
    if not room:
        return jsonify({"success": False, "message": f"Room ID {room_id} not found."}), 404

    try:
        booking_id = Booking.allocate(
            student_id=int(student_id),
            room_id=int(room_id),
            allocation_date=allocation_date,
            remarks=remarks
        )
        created_booking = Booking.get_by_id(booking_id)
        return jsonify({
            "success": True,
            "message": f"Room {room['room_number']} allocated successfully to {student['full_name']} ({student['roll_number']})!",
            "data": created_booking
        }), 201
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error during allocation: {str(e)}"}), 500

@booking_bp.route('/vacate', methods=['POST'])
def vacate_room():
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    student_id = data.get('student_id')
    vacate_date = data.get('vacate_date')
    remarks = data.get('remarks', 'Room vacated successfully')

    # If student_id is provided, find active booking
    if not booking_id and student_id:
        active_b = Booking.get_all(status='Active', student_id=int(student_id))
        if active_b:
            booking_id = active_b[0]['booking_id']
        else:
            return jsonify({"success": False, "message": "No active room booking found for this student."}), 404

    if not booking_id:
        return jsonify({"success": False, "message": "Booking ID or Student ID is required."}), 400

    try:
        Booking.vacate(booking_id=int(booking_id), vacate_date=vacate_date, remarks=remarks)
        updated_booking = Booking.get_by_id(booking_id)
        return jsonify({
            "success": True,
            "message": f"Student vacated from room {updated_booking['room_number']} successfully.",
            "data": updated_booking
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "message": f"Error during vacate process: {str(e)}"}), 500
