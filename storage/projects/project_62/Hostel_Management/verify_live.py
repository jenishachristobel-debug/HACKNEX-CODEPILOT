import urllib.request
import json

BASE_URL = 'http://127.0.0.1:5000'

def http_get(url):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, resp.read().decode('utf-8')

def http_post(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def http_patch(url, data):
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='PATCH'
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

def verify_all():
    print("==================================================")
    print("RUNNING LIVE END-TO-END HTTP API & WEB VERIFICATION")
    print("==================================================")

    # 1. Verify Web Pages
    pages = ['/', '/login', '/student', '/admin']
    for p in pages:
        status, html = http_get(f"{BASE_URL}{p}")
        assert status == 200, f"Page {p} returned {status}"
        print(f"[OK] Web Page '{p}' rendered successfully (Status 200, {len(html)} bytes).")

    # 2. Verify Stats
    status, stats = http_get(f"{BASE_URL}/api/stats/dashboard")
    stats_data = json.loads(stats)['data']
    print(f"[OK] Dashboard Stats API: {stats_data['total_students']} students, {stats_data['total_rooms']} rooms, {stats_data['occupied_beds']}/{stats_data['total_capacity']} beds occupied ({stats_data['occupancy_rate']}%).")

    # 3. Verify Admin Authentication
    status, admin_auth = http_post(f"{BASE_URL}/api/auth/admin/login", {
        "username": "admin",
        "password": "admin123"
    })
    assert admin_auth["success"] is True
    print(f"[OK] Admin Authentication: Verified {admin_auth['user']['full_name']} ({admin_auth['user']['role']}).")

    # 4. Verify Student Authentication
    status, student_auth = http_post(f"{BASE_URL}/api/auth/student/login", {
        "identifier": "STU202401",
        "password": "student123"
    })
    assert student_auth["success"] is True
    print(f"[OK] Student Authentication: Verified {student_auth['user']['full_name']} (Roll: {student_auth['user']['roll_number']}).")

    import time
    timestamp = int(time.time())
    new_roll = f"STU_{timestamp}"
    status, reg_res = http_post(f"{BASE_URL}/api/students", {
        "roll_number": new_roll,
        "full_name": f"Candidate {timestamp}",
        "email": f"student_{timestamp}@hostel.edu",
        "password": "mypassword123",
        "phone": "+91 98111 22233",
        "department": "Aerospace Engineering",
        "gender": "Male",
        "emergency_contact": "Guardian (+91 98111 22234)"
    })
    assert reg_res["success"] is True
    new_student_id = reg_res["data"]["student_id"]
    print(f"[OK] Student Registration: Created student ID {new_student_id} ({new_roll}).")

    # 6. Verify Room Listing & Allocation
    status, rooms_res = http_get(f"{BASE_URL}/api/rooms?available_only=true&room_type=Single")
    single_rooms = json.loads(rooms_res)["data"]
    assert len(single_rooms) > 0, "No single rooms found"
    room_to_book = single_rooms[0]
    initial_occ = room_to_book["current_occupancy"]

    status, alloc_res = http_post(f"{BASE_URL}/api/bookings/allocate", {
        "student_id": new_student_id,
        "room_id": room_to_book["room_id"],
        "allocation_date": "2026-08-26",
        "remarks": "Live Verification Move-in"
    })
    assert alloc_res["success"] is True
    booking_id = alloc_res["data"]["booking_id"]
    print(f"[OK] Room Allocation: Allocated Student ID {new_student_id} to Room {room_to_book['room_number']} (Booking #{booking_id}).")

    # Verify occupancy incremented
    status, room_check = http_get(f"{BASE_URL}/api/rooms/{room_to_book['room_id']}")
    updated_room = json.loads(room_check)["data"]
    assert updated_room["current_occupancy"] == initial_occ + 1
    print(f"[OK] Room Occupancy Sync: Room {room_to_book['room_number']} occupancy updated from {initial_occ} to {updated_room['current_occupancy']} (Status: {updated_room['status']}).")

    # 7. Verify Complaint Filing & Resolution
    status, comp_res = http_post(f"{BASE_URL}/api/complaints", {
        "student_id": new_student_id,
        "room_id": room_to_book["room_id"],
        "title": "Air Conditioner cooling efficiency low",
        "category": "Electrical",
        "priority": "High",
        "description": "The AC in the single room blows room-temperature air. Filter may need cleaning."
    })
    assert comp_res["success"] is True
    complaint_id = comp_res["data"]["complaint_id"]
    print(f"[OK] Complaint Ticket: Created Ticket #{complaint_id} for Room {room_to_book['room_number']}.")

    status, resolve_res = http_patch(f"{BASE_URL}/api/complaints/{complaint_id}", {
        "status": "Resolved",
        "admin_remarks": "HVAC technician serviced compressor and cleaned air filter on 2026-08-26."
    })
    assert resolve_res["success"] is True
    print(f"[OK] Complaint Resolution: Updated Ticket #{complaint_id} to 'Resolved' with warden remarks.")

    # 8. Verify Room Vacate Workflow
    status, vacate_res = http_post(f"{BASE_URL}/api/bookings/vacate", {
        "booking_id": booking_id,
        "remarks": "Live Verification End-of-Term Vacate"
    })
    assert vacate_res["success"] is True
    
    # Verify room occupancy decremented back
    status, room_check2 = http_get(f"{BASE_URL}/api/rooms/{room_to_book['room_id']}")
    vacated_room = json.loads(room_check2)["data"]
    assert vacated_room["current_occupancy"] == initial_occ
    print(f"[OK] Room Vacating: Booking #{booking_id} vacated. Room {vacated_room['room_number']} occupancy decreased to {vacated_room['current_occupancy']} (Status: {vacated_room['status']}).")

    print("==================================================")
    print("ALL LIVE VERIFICATION TESTS PASSED SUCCESSFULLY! [SUCCESS]")
    print("==================================================")

if __name__ == '__main__':
    verify_all()
