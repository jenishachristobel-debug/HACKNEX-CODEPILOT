from flask import Blueprint, request, jsonify
from models import Room

room_bp = Blueprint('rooms', __name__, url_prefix='/api/rooms')

@room_bp.route('', methods=['GET'])
def list_rooms():
    room_type = request.args.get('room_type', '').strip() or None
    status = request.args.get('status', '').strip() or None
    block = request.args.get('block', '').strip() or None
    available_only = request.args.get('available_only', 'false').lower() in ('true', '1', 'yes')

    rooms = Room.get_all(room_type=room_type, status=status, block=block, available_only=available_only)
    return jsonify({"success": True, "count": len(rooms), "data": rooms}), 200

@room_bp.route('/<int:room_id>', methods=['GET'])
def get_room(room_id):
    room = Room.get_by_id(room_id)
    if not room:
        return jsonify({"success": False, "message": f"Room with ID {room_id} not found."}), 404
    return jsonify({"success": True, "data": room}), 200

@room_bp.route('', methods=['POST'])
def create_room():
    data = request.get_json() or {}
    room_number = str(data.get('room_number', '')).strip().upper()
    block_name = str(data.get('block_name', '')).strip()
    room_type = str(data.get('room_type', '')).strip()
    capacity = data.get('capacity')
    price_per_term = data.get('price_per_term', 0.00)
    amenities = str(data.get('amenities', '')).strip()

    errors = []
    if not room_number:
        errors.append("Room number is required.")
    if not block_name:
        errors.append("Block/Wing name is required.")
    if not room_type:
        errors.append("Room type is required (e.g., Single, Double, Triple, Deluxe Suite).")
    try:
        capacity = int(capacity)
        if capacity <= 0 or capacity > 10:
            errors.append("Capacity must be an integer between 1 and 10.")
    except (ValueError, TypeError):
        errors.append("Valid integer capacity is required.")

    if errors:
        return jsonify({"success": False, "message": "Validation failed.", "errors": errors}), 400

    existing = Room.get_by_room_number(room_number)
    if existing:
        return jsonify({"success": False, "message": f"Room number '{room_number}' already exists."}), 409

    try:
        room_id = Room.create(
            room_number=room_number,
            block_name=block_name,
            room_type=room_type,
            capacity=capacity,
            price_per_term=price_per_term,
            amenities=amenities
        )
        created_room = Room.get_by_id(room_id)
        return jsonify({
            "success": True,
            "message": f"Room {room_number} created successfully.",
            "data": created_room
        }), 201
    except Exception as e:
        return jsonify({"success": False, "message": f"Database error creating room: {str(e)}"}), 500

@room_bp.route('/<int:room_id>', methods=['PUT'])
def update_room(room_id):
    room = Room.get_by_id(room_id)
    if not room:
        return jsonify({"success": False, "message": f"Room with ID {room_id} not found."}), 404

    data = request.get_json() or {}
    block_name = data.get('block_name', room['block_name'])
    room_type = data.get('room_type', room['room_type'])
    capacity = int(data.get('capacity', room['capacity']))
    status = data.get('status', room['status'])
    price_per_term = float(data.get('price_per_term', room['price_per_term']))
    amenities = data.get('amenities', room['amenities'])

    try:
        Room.update(room_id, block_name, room_type, capacity, status, price_per_term, amenities)
        updated_room = Room.get_by_id(room_id)
        return jsonify({"success": True, "message": f"Room {room['room_number']} updated successfully.", "data": updated_room}), 200
    except Exception as e:
        return jsonify({"success": False, "message": f"Error updating room: {str(e)}"}), 500
