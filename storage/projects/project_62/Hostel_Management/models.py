from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from db import get_supabase_client, fetch_all, fetch_one, execute_query

class Admin:
    """Admin entity and authentication operations."""
    
    @staticmethod
    def get_by_username(username):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('admins').select('*').eq('username', username).execute()
                return res.data[0] if res.data else None
            except Exception:
                pass
        return fetch_one("SELECT * FROM admins WHERE username = %s", (username,))
    
    @staticmethod
    def get_by_id(admin_id):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('admins').select('admin_id, username, full_name, email, role, created_at').eq('admin_id', admin_id).execute()
                return res.data[0] if res.data else None
            except Exception:
                pass
        return fetch_one("SELECT admin_id, username, full_name, email, role, created_at FROM admins WHERE admin_id = %s", (admin_id,))

    @staticmethod
    def create(username, password, full_name, email, role="Chief Warden"):
        password_hash = generate_password_hash(password)
        client = get_supabase_client()
        if client:
            try:
                res = client.table('admins').insert({
                    "username": username,
                    "password_hash": password_hash,
                    "full_name": full_name,
                    "email": email,
                    "role": role
                }).execute()
                return res.data[0]["admin_id"] if res.data else 1
            except Exception:
                pass
        query = "INSERT INTO admins (username, password_hash, full_name, email, role) VALUES (%s, %s, %s, %s, %s)"
        res = execute_query(query, (username, password_hash, full_name, email, role))
        return res["lastrowid"]

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)


class Student:
    """Student entity management and profile operations."""

    @staticmethod
    def get_all(search=None, department=None):
        client = get_supabase_client()
        if client:
            try:
                # Fetch students, active bookings, and rooms from Supabase
                students_res = client.table('students').select('*').order('registration_date', desc=True).execute()
                students = students_res.data or []
                
                bookings_res = client.table('bookings').select('*, rooms(*)').eq('status', 'Active').execute()
                active_bookings = {b['student_id']: b for b in (bookings_res.data or [])}

                results = []
                for s in students:
                    b = active_bookings.get(s['student_id'])
                    s_data = dict(s)
                    if b:
                        s_data['booking_id'] = b.get('booking_id')
                        s_data['room_id'] = b.get('room_id')
                        s_data['allocation_date'] = b.get('allocation_date')
                        s_data['booking_status'] = b.get('status')
                        room = b.get('rooms') or {}
                        s_data['room_number'] = room.get('room_number')
                        s_data['block_name'] = room.get('block_name')
                        s_data['room_type'] = room.get('room_type')
                    else:
                        s_data['booking_id'] = None
                        s_data['room_id'] = None
                        s_data['allocation_date'] = None
                        s_data['booking_status'] = None
                        s_data['room_number'] = None
                        s_data['block_name'] = None
                        s_data['room_type'] = None

                    # Apply search filter
                    if search:
                        q = search.lower()
                        match = (q in s_data.get('full_name', '').lower() or
                                 q in s_data.get('roll_number', '').lower() or
                                 q in s_data.get('email', '').lower())
                        if not match:
                            continue

                    if department and s_data.get('department') != department:
                        continue

                    results.append(s_data)
                return results
            except Exception:
                pass

        query = """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone,
                   s.department, s.gender, s.emergency_contact, s.registration_date,
                   b.booking_id, b.room_id, b.allocation_date, b.status AS booking_status,
                   r.room_number, r.block_name, r.room_type
            FROM students s
            LEFT JOIN bookings b ON s.student_id = b.student_id AND b.status = 'Active'
            LEFT JOIN rooms r ON b.room_id = r.room_id
            WHERE 1=1
        """
        params = []
        if search:
            query += " AND (s.full_name LIKE %s OR s.roll_number LIKE %s OR s.email LIKE %s)"
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
        if department:
            query += " AND s.department = %s"
            params.append(department)
        query += " ORDER BY s.registration_date DESC"
        return fetch_all(query, tuple(params) if params else None)

    @staticmethod
    def get_by_id(student_id):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('students').select('*').eq('student_id', student_id).execute()
                if not res.data:
                    return None
                student = res.data[0]
                
                b_res = client.table('bookings').select('*, rooms(*)').eq('student_id', student_id).eq('status', 'Active').execute()
                if b_res.data:
                    b = b_res.data[0]
                    student['booking_id'] = b.get('booking_id')
                    student['room_id'] = b.get('room_id')
                    student['allocation_date'] = b.get('allocation_date')
                    student['booking_status'] = b.get('status')
                    room = b.get('rooms') or {}
                    student['room_number'] = room.get('room_number')
                    student['block_name'] = room.get('block_name')
                    student['room_type'] = room.get('room_type')
                    student['capacity'] = room.get('capacity')
                    student['amenities'] = room.get('amenities')
                else:
                    student['booking_id'] = None
                    student['room_id'] = None
                    student['booking_status'] = None
                    student['room_number'] = None
                return student
            except Exception:
                pass

        query = """
            SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone,
                   s.department, s.gender, s.emergency_contact, s.registration_date,
                   b.booking_id, b.room_id, b.allocation_date, b.status AS booking_status,
                   r.room_number, r.block_name, r.room_type, r.capacity, r.amenities
            FROM students s
            LEFT JOIN bookings b ON s.student_id = b.student_id AND b.status = 'Active'
            LEFT JOIN rooms r ON b.room_id = r.room_id
            WHERE s.student_id = %s
        """
        return fetch_one(query, (student_id,))

    @staticmethod
    def get_by_roll_or_email(identifier):
        client = get_supabase_client()
        identifier_upper = identifier.upper()
        identifier_lower = identifier.lower()
        if client:
            try:
                res_roll = client.table('students').select('*').eq('roll_number', identifier_upper).execute()
                if res_roll.data:
                    return res_roll.data[0]
                res_email = client.table('students').select('*').eq('email', identifier_lower).execute()
                if res_email.data:
                    return res_email.data[0]
                return None
            except Exception:
                pass
        return fetch_one("SELECT * FROM students WHERE roll_number = %s OR email = %s", (identifier_upper, identifier_lower))

    @staticmethod
    def create(roll_number, full_name, email, password, phone, department, gender, emergency_contact=None):
        password_hash = generate_password_hash(password)
        client = get_supabase_client()
        if client:
            try:
                res = client.table('students').insert({
                    "roll_number": roll_number.strip().upper(),
                    "full_name": full_name.strip(),
                    "email": email.strip().lower(),
                    "password_hash": password_hash,
                    "phone": phone.strip(),
                    "department": department.strip(),
                    "gender": gender,
                    "emergency_contact": emergency_contact
                }).execute()
                return res.data[0]["student_id"] if res.data else 1
            except Exception:
                pass

        query = """
            INSERT INTO students (roll_number, full_name, email, password_hash, phone, department, gender, emergency_contact)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        res = execute_query(query, (roll_number.strip().upper(), full_name.strip(), email.strip().lower(),
                                   password_hash, phone.strip(), department.strip(), gender, emergency_contact))
        return res["lastrowid"]

    @staticmethod
    def verify_password(stored_hash, password):
        return check_password_hash(stored_hash, password)

    @staticmethod
    def get_current_room_and_roommates(student_id):
        client = get_supabase_client()
        if client:
            try:
                b_res = client.table('bookings').select('*, rooms(*)').eq('student_id', student_id).eq('status', 'Active').execute()
                if not b_res.data:
                    return None
                b = b_res.data[0]
                room = b.get('rooms') or {}
                
                room_info = {
                    "booking_id": b.get('booking_id'),
                    "allocation_date": b.get('allocation_date'),
                    "booking_status": b.get('status'),
                    "room_id": room.get('room_id'),
                    "room_number": room.get('room_number'),
                    "block_name": room.get('block_name'),
                    "room_type": room.get('room_type'),
                    "capacity": room.get('capacity'),
                    "current_occupancy": room.get('current_occupancy'),
                    "price_per_term": room.get('price_per_term'),
                    "amenities": room.get('amenities')
                }

                # Fetch roommates in the same room
                rms_res = client.table('bookings').select('*, students(*)').eq('room_id', room['room_id']).eq('status', 'Active').neq('student_id', student_id).execute()
                roommates = []
                for rm in (rms_res.data or []):
                    s = rm.get('students') or {}
                    roommates.append({
                        "student_id": s.get('student_id'),
                        "roll_number": s.get('roll_number'),
                        "full_name": s.get('full_name'),
                        "department": s.get('department'),
                        "phone": s.get('phone'),
                        "email": s.get('email'),
                        "allocation_date": rm.get('allocation_date')
                    })
                room_info["roommates"] = roommates
                return room_info
            except Exception:
                pass

        current_booking_query = """
            SELECT b.booking_id, b.allocation_date, b.status AS booking_status,
                   r.room_id, r.room_number, r.block_name, r.room_type, r.capacity,
                   r.current_occupancy, r.price_per_term, r.amenities
            FROM bookings b
            JOIN rooms r ON b.room_id = r.room_id
            WHERE b.student_id = %s AND b.status = 'Active'
            LIMIT 1
        """
        room_info = fetch_one(current_booking_query, (student_id,))
        if not room_info:
            return None

        roommates_query = """
            SELECT s.student_id, s.roll_number, s.full_name, s.department, s.phone, s.email, b.allocation_date
            FROM bookings b
            JOIN students s ON b.student_id = s.student_id
            WHERE b.room_id = %s AND b.status = 'Active' AND s.student_id != %s
        """
        roommates = fetch_all(roommates_query, (room_info["room_id"], student_id))
        room_info["roommates"] = roommates
        return room_info


class Room:
    """Room inventory management and occupancy calculations."""

    @staticmethod
    def get_all(room_type=None, status=None, block=None, available_only=False):
        client = get_supabase_client()
        if client:
            try:
                query = client.table('rooms').select('*')
                if room_type:
                    query = query.eq('room_type', room_type)
                if status:
                    query = query.eq('status', status)
                if block:
                    query = query.eq('block_name', block)
                
                res = query.order('block_name').order('room_number').execute()
                rooms = res.data or []
                for r in rooms:
                    r['available_beds'] = max(0, r.get('capacity', 1) - r.get('current_occupancy', 0))

                if available_only:
                    rooms = [r for r in rooms if r['current_occupancy'] < r['capacity'] and r['status'] == 'Available']
                return rooms
            except Exception:
                pass

        query = """
            SELECT room_id, room_number, block_name, room_type, capacity,
                   current_occupancy, status, price_per_term, amenities,
                   (capacity - current_occupancy) AS available_beds
            FROM rooms
            WHERE 1=1
        """
        params = []
        if room_type:
            query += " AND room_type = %s"
            params.append(room_type)
        if status:
            query += " AND status = %s"
            params.append(status)
        if block:
            query += " AND block_name = %s"
            params.append(block)
        if available_only:
            query += " AND current_occupancy < capacity AND status = 'Available'"
        query += " ORDER BY block_name ASC, room_number ASC"
        return fetch_all(query, tuple(params) if params else None)

    @staticmethod
    def get_by_id(room_id):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('rooms').select('*').eq('room_id', room_id).execute()
                if not res.data:
                    return None
                room = res.data[0]
                room['available_beds'] = max(0, room.get('capacity', 1) - room.get('current_occupancy', 0))
                
                # Fetch occupants
                b_res = client.table('bookings').select('*, students(*)').eq('room_id', room_id).eq('status', 'Active').execute()
                occupants = []
                for b in (b_res.data or []):
                    s = b.get('students') or {}
                    occupants.append({
                        "student_id": s.get('student_id'),
                        "roll_number": s.get('roll_number'),
                        "full_name": s.get('full_name'),
                        "email": s.get('email'),
                        "phone": s.get('phone'),
                        "department": s.get('department'),
                        "allocation_date": b.get('allocation_date'),
                        "booking_id": b.get('booking_id')
                    })
                room["occupants"] = occupants
                return room
            except Exception:
                pass

        query = """
            SELECT room_id, room_number, block_name, room_type, capacity,
                   current_occupancy, status, price_per_term, amenities,
                   (capacity - current_occupancy) AS available_beds
            FROM rooms
            WHERE room_id = %s
        """
        room = fetch_one(query, (room_id,))
        if room:
            occupants_query = """
                SELECT s.student_id, s.roll_number, s.full_name, s.email, s.phone, s.department, b.allocation_date, b.booking_id
                FROM bookings b
                JOIN students s ON b.student_id = s.student_id
                WHERE b.room_id = %s AND b.status = 'Active'
            """
            room["occupants"] = fetch_all(occupants_query, (room_id,))
        return room

    @staticmethod
    def get_by_room_number(room_number):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('rooms').select('*').eq('room_number', room_number).execute()
                return res.data[0] if res.data else None
            except Exception:
                pass
        return fetch_one("SELECT * FROM rooms WHERE room_number = %s", (room_number,))

    @staticmethod
    def create(room_number, block_name, room_type, capacity, price_per_term=0.00, amenities=""):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('rooms').insert({
                    "room_number": room_number.strip().upper(),
                    "block_name": block_name.strip(),
                    "room_type": room_type,
                    "capacity": int(capacity),
                    "current_occupancy": 0,
                    "status": "Available",
                    "price_per_term": float(price_per_term),
                    "amenities": amenities.strip()
                }).execute()
                return res.data[0]["room_id"] if res.data else 1
            except Exception:
                pass

        query = """
            INSERT INTO rooms (room_number, block_name, room_type, capacity, current_occupancy, status, price_per_term, amenities)
            VALUES (%s, %s, %s, %s, 0, 'Available', %s, %s)
        """
        res = execute_query(query, (room_number.strip().upper(), block_name.strip(),
                                   room_type, int(capacity), float(price_per_term), amenities.strip()))
        return res["lastrowid"]

    @staticmethod
    def update(room_id, block_name, room_type, capacity, status, price_per_term, amenities):
        client = get_supabase_client()
        if client:
            try:
                client.table('rooms').update({
                    "block_name": block_name,
                    "room_type": room_type,
                    "capacity": int(capacity),
                    "status": status,
                    "price_per_term": float(price_per_term),
                    "amenities": amenities
                }).eq('room_id', room_id).execute()
                Room.sync_room_occupancy(room_id)
                return True
            except Exception:
                pass

        query = """
            UPDATE rooms
            SET block_name = %s, room_type = %s, capacity = %s, status = %s,
                price_per_term = %s, amenities = %s
            WHERE room_id = %s
        """
        execute_query(query, (block_name, room_type, int(capacity), status, float(price_per_term), amenities, room_id))
        Room.sync_room_occupancy(room_id)

    @staticmethod
    def sync_room_occupancy(room_id):
        client = get_supabase_client()
        if client:
            try:
                b_res = client.table('bookings').select('booking_id').eq('room_id', room_id).eq('status', 'Active').execute()
                count = len(b_res.data or [])
                r_res = client.table('rooms').select('capacity, status').eq('room_id', room_id).execute()
                if r_res.data:
                    room = r_res.data[0]
                    capacity = room.get('capacity', 1)
                    new_status = room.get('status', 'Available')
                    if new_status != "Maintenance":
                        new_status = "Full" if count >= capacity else "Available"
                    client.table('rooms').update({
                        "current_occupancy": count,
                        "status": new_status
                    }).eq('room_id', room_id).execute()
                    return
            except Exception:
                pass

        count_query = "SELECT COUNT(*) as occupant_count FROM bookings WHERE room_id = %s AND status = 'Active'"
        res = fetch_one(count_query, (room_id,))
        count = res["occupant_count"] if res else 0

        room = fetch_one("SELECT capacity, status FROM rooms WHERE room_id = %s", (room_id,))
        if room:
            capacity = room["capacity"]
            new_status = room["status"]
            if new_status != "Maintenance":
                new_status = "Full" if count >= capacity else "Available"
            execute_query("UPDATE rooms SET current_occupancy = %s, status = %s WHERE room_id = %s", (count, new_status, room_id))


class Booking:
    """Booking entity managing allocations and vacating workflows."""

    @staticmethod
    def get_all(status=None, student_id=None, room_id=None):
        client = get_supabase_client()
        if client:
            try:
                query = client.table('bookings').select('*, students(*), rooms(*)')
                if status:
                    query = query.eq('status', status)
                if student_id:
                    query = query.eq('student_id', student_id)
                if room_id:
                    query = query.eq('room_id', room_id)

                res = query.order('created_at', desc=True).execute()
                bookings = []
                for b in (res.data or []):
                    s = b.get('students') or {}
                    r = b.get('rooms') or {}
                    b_data = dict(b)
                    b_data['roll_number'] = s.get('roll_number')
                    b_data['student_name'] = s.get('full_name')
                    b_data['department'] = s.get('department')
                    b_data['phone'] = s.get('phone')
                    b_data['email'] = s.get('email')
                    b_data['room_number'] = r.get('room_number')
                    b_data['block_name'] = r.get('block_name')
                    b_data['room_type'] = r.get('room_type')
                    bookings.append(b_data)
                return bookings
            except Exception:
                pass

        query = """
            SELECT b.booking_id, b.student_id, b.room_id, b.allocation_date,
                   b.vacate_date, b.status, b.remarks, b.created_at,
                   s.roll_number, s.full_name AS student_name, s.department, s.phone, s.email,
                   r.room_number, r.block_name, r.room_type
            FROM bookings b
            JOIN students s ON b.student_id = s.student_id
            JOIN rooms r ON b.room_id = r.room_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND b.status = %s"
            params.append(status)
        if student_id:
            query += " AND b.student_id = %s"
            params.append(student_id)
        if room_id:
            query += " AND b.room_id = %s"
            params.append(room_id)
        query += " ORDER BY b.created_at DESC"
        return fetch_all(query, tuple(params) if params else None)

    @staticmethod
    def get_by_id(booking_id):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('bookings').select('*, students(*), rooms(*)').eq('booking_id', booking_id).execute()
                if res.data:
                    b = res.data[0]
                    s = b.get('students') or {}
                    r = b.get('rooms') or {}
                    b_data = dict(b)
                    b_data['roll_number'] = s.get('roll_number')
                    b_data['student_name'] = s.get('full_name')
                    b_data['department'] = s.get('department')
                    b_data['phone'] = s.get('phone')
                    b_data['email'] = s.get('email')
                    b_data['room_number'] = r.get('room_number')
                    b_data['block_name'] = r.get('block_name')
                    b_data['room_type'] = r.get('room_type')
                    return b_data
            except Exception:
                pass

        query = """
            SELECT b.*, s.roll_number, s.full_name AS student_name, s.department, s.phone, s.email,
                   r.room_number, r.block_name, r.room_type
            FROM bookings b
            JOIN students s ON b.student_id = s.student_id
            JOIN rooms r ON b.room_id = r.room_id
            WHERE b.booking_id = %s
        """
        return fetch_one(query, (booking_id,))

    @staticmethod
    def allocate(student_id, room_id, allocation_date=None, remarks="Allocated"):
        client = get_supabase_client()
        if client:
            try:
                # 1. Check active booking
                b_res = client.table('bookings').select('booking_id, room_id').eq('student_id', student_id).eq('status', 'Active').execute()
                if b_res.data:
                    raise ValueError(f"Student already has an active room allocation (Room ID {b_res.data[0]['room_id']}).")

                # 2. Check room capacity
                r_res = client.table('rooms').select('*').eq('room_id', room_id).execute()
                if not r_res.data:
                    raise ValueError("Selected room does not exist.")
                room = r_res.data[0]
                if room.get('status') == 'Maintenance':
                    raise ValueError(f"Room {room['room_number']} is under maintenance.")
                if room.get('current_occupancy', 0) >= room.get('capacity', 1):
                    raise ValueError(f"Room {room['room_number']} is at full capacity.")

                alloc_date = allocation_date or date.today().isoformat()
                new_b = client.table('bookings').insert({
                    "student_id": int(student_id),
                    "room_id": int(room_id),
                    "allocation_date": alloc_date,
                    "status": "Active",
                    "remarks": remarks
                }).execute()

                Room.sync_room_occupancy(room_id)
                return new_b.data[0]["booking_id"] if new_b.data else 1
            except ValueError:
                raise
            except Exception as e:
                pass

        active_booking = fetch_one("SELECT booking_id, room_id FROM bookings WHERE student_id = %s AND status = 'Active'", (student_id,))
        if active_booking:
            raise ValueError(f"Student is already allocated to Room ID {active_booking['room_id']}. Please vacate the existing room first.")

        room = fetch_one("SELECT capacity, current_occupancy, status, room_number FROM rooms WHERE room_id = %s", (room_id,))
        if not room:
            raise ValueError("Selected room does not exist.")
        if room["status"] == "Maintenance":
            raise ValueError(f"Room {room['room_number']} is currently under maintenance.")
        if room["current_occupancy"] >= room["capacity"]:
            raise ValueError(f"Room {room['room_number']} has reached its full capacity.")

        alloc_date = allocation_date or date.today().isoformat()
        res = execute_query("INSERT INTO bookings (student_id, room_id, allocation_date, status, remarks) VALUES (%s, %s, %s, 'Active', %s)",
                            (student_id, room_id, alloc_date, remarks))
        booking_id = res["lastrowid"]
        Room.sync_room_occupancy(room_id)
        return booking_id

    @staticmethod
    def vacate(booking_id, vacate_date=None, remarks="Vacated"):
        client = get_supabase_client()
        if client:
            try:
                b_res = client.table('bookings').select('*').eq('booking_id', booking_id).execute()
                if not b_res.data:
                    raise ValueError("Booking record not found.")
                booking = b_res.data[0]
                if booking.get('status') != 'Active':
                    raise ValueError("This booking is not currently active.")

                v_date = vacate_date or date.today().isoformat()
                client.table('bookings').update({
                    "status": "Vacated",
                    "vacate_date": v_date,
                    "remarks": remarks
                }).eq('booking_id', booking_id).execute()

                Room.sync_room_occupancy(booking['room_id'])
                return True
            except ValueError:
                raise
            except Exception:
                pass

        booking = fetch_one("SELECT booking_id, room_id, status FROM bookings WHERE booking_id = %s", (booking_id,))
        if not booking:
            raise ValueError("Booking record not found.")
        if booking["status"] != "Active":
            raise ValueError("This booking is not currently active.")

        v_date = vacate_date or date.today().isoformat()
        execute_query("UPDATE bookings SET status = 'Vacated', vacate_date = %s, remarks = %s WHERE booking_id = %s",
                      (v_date, remarks, booking_id))
        Room.sync_room_occupancy(booking["room_id"])
        return True


class Complaint:
    """Complaint handling and resolution lifecycle."""

    @staticmethod
    def get_all(status=None, student_id=None, room_id=None, priority=None):
        client = get_supabase_client()
        if client:
            try:
                query = client.table('complaints').select('*, students(*), rooms(*)')
                if status:
                    query = query.eq('status', status)
                if student_id:
                    query = query.eq('student_id', student_id)
                if room_id:
                    query = query.eq('room_id', room_id)
                if priority:
                    query = query.eq('priority', priority)

                res = query.order('date_raised', desc=True).execute()
                complaints = []
                for c in (res.data or []):
                    s = c.get('students') or {}
                    r = c.get('rooms') or {}
                    c_data = dict(c)
                    c_data['roll_number'] = s.get('roll_number')
                    c_data['student_name'] = s.get('full_name')
                    c_data['department'] = s.get('department')
                    c_data['phone'] = s.get('phone')
                    c_data['room_number'] = r.get('room_number')
                    c_data['block_name'] = r.get('block_name')
                    complaints.append(c_data)
                return complaints
            except Exception:
                pass

        query = """
            SELECT c.complaint_id, c.student_id, c.room_id, c.title, c.category,
                   c.description, c.priority, c.date_raised, c.status, c.admin_remarks, c.resolved_date,
                   s.roll_number, s.full_name AS student_name, s.department, s.phone,
                   r.room_number, r.block_name
            FROM complaints c
            JOIN students s ON c.student_id = s.student_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE 1=1
        """
        params = []
        if status:
            query += " AND c.status = %s"
            params.append(status)
        if student_id:
            query += " AND c.student_id = %s"
            params.append(student_id)
        if room_id:
            query += " AND c.room_id = %s"
            params.append(room_id)
        if priority:
            query += " AND c.priority = %s"
            params.append(priority)
        query += " ORDER BY c.date_raised DESC"
        return fetch_all(query, tuple(params) if params else None)

    @staticmethod
    def get_by_id(complaint_id):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('complaints').select('*, students(*), rooms(*)').eq('complaint_id', complaint_id).execute()
                if res.data:
                    c = res.data[0]
                    s = c.get('students') or {}
                    r = c.get('rooms') or {}
                    c_data = dict(c)
                    c_data['roll_number'] = s.get('roll_number')
                    c_data['student_name'] = s.get('full_name')
                    c_data['department'] = s.get('department')
                    c_data['phone'] = s.get('phone')
                    c_data['room_number'] = r.get('room_number')
                    c_data['block_name'] = r.get('block_name')
                    return c_data
            except Exception:
                pass

        query = """
            SELECT c.*, s.roll_number, s.full_name AS student_name, s.department, s.phone,
                   r.room_number, r.block_name
            FROM complaints c
            JOIN students s ON c.student_id = s.student_id
            JOIN rooms r ON c.room_id = r.room_id
            WHERE c.complaint_id = %s
        """
        return fetch_one(query, (complaint_id,))

    @staticmethod
    def create(student_id, room_id, title, category, description, priority="Medium"):
        client = get_supabase_client()
        if client:
            try:
                res = client.table('complaints').insert({
                    "student_id": int(student_id),
                    "room_id": int(room_id),
                    "title": title.strip(),
                    "category": category,
                    "description": description.strip(),
                    "priority": priority,
                    "status": "Pending"
                }).execute()
                return res.data[0]["complaint_id"] if res.data else 1
            except Exception:
                pass

        query = """
            INSERT INTO complaints (student_id, room_id, title, category, description, priority, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'Pending')
        """
        res = execute_query(query, (student_id, room_id, title.strip(), category, description.strip(), priority))
        return res["lastrowid"]

    @staticmethod
    def update_status(complaint_id, status, admin_remarks=""):
        resolved_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if status == 'Resolved' else None
        client = get_supabase_client()
        if client:
            try:
                client.table('complaints').update({
                    "status": status,
                    "admin_remarks": admin_remarks.strip() if admin_remarks else None,
                    "resolved_date": resolved_date
                }).eq('complaint_id', complaint_id).execute()
                return True
            except Exception:
                pass

        query = """
            UPDATE complaints
            SET status = %s, admin_remarks = %s, resolved_date = %s
            WHERE complaint_id = %s
        """
        execute_query(query, (status, admin_remarks.strip() if admin_remarks else None, resolved_date, complaint_id))
        return True


class DashboardStats:
    """Analytics aggregation for Admin Dashboard and Metrics Cards."""

    @staticmethod
    def get_metrics():
        client = get_supabase_client()
        if client:
            try:
                stu_res = client.table('students').select('student_id').execute()
                total_students = len(stu_res.data or [])

                rooms_res = client.table('rooms').select('*').execute()
                rooms = rooms_res.data or []
                total_rooms = len(rooms)
                total_capacity = sum(r.get('capacity', 0) for r in rooms)
                total_occupied = sum(r.get('current_occupancy', 0) for r in rooms)
                available_beds = max(0, total_capacity - total_occupied)
                occupancy_rate = round((total_occupied / total_capacity * 100), 1) if total_capacity > 0 else 0

                comp_res = client.table('complaints').select('status').execute()
                complaints = comp_res.data or []
                complaint_counts = {"Pending": 0, "In Progress": 0, "Resolved": 0}
                for c in complaints:
                    st = c.get('status')
                    if st in complaint_counts:
                        complaint_counts[st] += 1

                bkg_res = client.table('bookings').select('booking_id').eq('status', 'Active').execute()
                active_bookings = len(bkg_res.data or [])

                # Room types breakdown
                type_map = {}
                for r in rooms:
                    t = r.get('room_type', 'Standard')
                    if t not in type_map:
                        type_map[t] = {"room_type": t, "count": 0, "capacity": 0, "occupied": 0}
                    type_map[t]["count"] += 1
                    type_map[t]["capacity"] += r.get('capacity', 0)
                    type_map[t]["occupied"] += r.get('current_occupancy', 0)

                recent_bookings = Booking.get_all()[:5]
                recent_complaints = Complaint.get_all()[:5]

                return {
                    "total_students": total_students,
                    "total_rooms": total_rooms,
                    "total_capacity": total_capacity,
                    "occupied_beds": total_occupied,
                    "available_beds": available_beds,
                    "occupancy_rate": occupancy_rate,
                    "pending_complaints": complaint_counts["Pending"],
                    "in_progress_complaints": complaint_counts["In Progress"],
                    "resolved_complaints": complaint_counts["Resolved"],
                    "active_bookings": active_bookings,
                    "room_types": list(type_map.values()),
                    "recent_bookings": recent_bookings,
                    "recent_complaints": recent_complaints
                }
            except Exception:
                pass

        students_res = fetch_one("SELECT COUNT(*) AS total_students FROM students")
        total_students = students_res["total_students"] if students_res else 0

        rooms_res = fetch_one("""
            SELECT COUNT(*) AS total_rooms,
                   COALESCE(SUM(capacity), 0) AS total_capacity,
                   COALESCE(SUM(current_occupancy), 0) AS total_occupied
            FROM rooms
        """)
        total_rooms = rooms_res["total_rooms"] if rooms_res else 0
        total_capacity = rooms_res["total_capacity"] if rooms_res else 0
        total_occupied = rooms_res["total_occupied"] if rooms_res else 0
        available_beds = max(0, total_capacity - total_occupied)
        occupancy_rate = round((total_occupied / total_capacity * 100), 1) if total_capacity > 0 else 0

        complaints_res = fetch_all("SELECT status, COUNT(*) AS count FROM complaints GROUP BY status")
        complaint_counts = {"Pending": 0, "In Progress": 0, "Resolved": 0}
        for item in complaints_res:
            if item["status"] in complaint_counts:
                complaint_counts[item["status"]] = item["count"]

        bookings_res = fetch_one("SELECT COUNT(*) AS active_bookings FROM bookings WHERE status = 'Active'")
        active_bookings = bookings_res["active_bookings"] if bookings_res else 0

        room_types = fetch_all("""
            SELECT room_type, COUNT(*) as count,
                   COALESCE(SUM(capacity), 0) as capacity,
                   COALESCE(SUM(current_occupancy), 0) as occupied
            FROM rooms
            GROUP BY room_type
        """)

        recent_bookings = Booking.get_all()[:5]
        recent_complaints = Complaint.get_all()[:5]

        return {
            "total_students": total_students,
            "total_rooms": total_rooms,
            "total_capacity": total_capacity,
            "occupied_beds": total_occupied,
            "available_beds": available_beds,
            "occupancy_rate": occupancy_rate,
            "pending_complaints": complaint_counts["Pending"],
            "in_progress_complaints": complaint_counts["In Progress"],
            "resolved_complaints": complaint_counts["Resolved"],
            "active_bookings": active_bookings,
            "room_types": room_types,
            "recent_bookings": recent_bookings,
            "recent_complaints": recent_complaints
        }
