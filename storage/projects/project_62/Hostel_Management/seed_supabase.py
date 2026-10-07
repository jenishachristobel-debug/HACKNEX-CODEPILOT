import os
from dotenv import load_dotenv
from supabase import create_client, Client
from werkzeug.security import generate_password_hash

load_dotenv(r'd:\sem3\Hostel_Management\.env', override=True)

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

def seed_supabase_live():
    if not url or not key:
        print("[INFO] No Supabase URL or Key found.")
        return False

    supabase: Client = create_client(url, key)
    print(f"[INFO] Connected to live Supabase project at: {url}")

    # 1. Admin
    admin_check = supabase.table('admins').select('admin_id').eq('username', 'admin').execute()
    if not admin_check.data:
        admin_pwd = generate_password_hash('admin123')
        supabase.table('admins').insert({
            "username": "admin",
            "password_hash": admin_pwd,
            "full_name": "Prof. Robert Vance (Chief Warden)",
            "email": "warden@hostel.edu",
            "role": "Chief Warden"
        }).execute()
        print("[OK] Seeded Admin account in Supabase (admin / admin123)")
    else:
        print("[OK] Admin account active in Supabase.")

    # 2. Rooms
    rooms_check = supabase.table('rooms').select('*').execute()
    if not rooms_check.data or len(rooms_check.data) == 0:
        rooms_data = [
            {"room_number": "A-101", "block_name": "Block A (North)", "room_type": "Single", "capacity": 1, "current_occupancy": 0, "status": "Available", "price_per_term": 35000, "amenities": "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"},
            {"room_number": "A-102", "block_name": "Block A (North)", "room_type": "Single", "capacity": 1, "current_occupancy": 0, "status": "Available", "price_per_term": 35000, "amenities": "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"},
            {"room_number": "A-103", "block_name": "Block A (North)", "room_type": "Double", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 24000, "amenities": "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Ceiling Fan"},
            {"room_number": "A-104", "block_name": "Block A (North)", "room_type": "Double", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 24000, "amenities": "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Ceiling Fan"},
            {"room_number": "A-201", "block_name": "Block A (North)", "room_type": "Triple", "capacity": 3, "current_occupancy": 0, "status": "Available", "price_per_term": 18000, "amenities": "3 Single Beds, 3 Wardrobes, Balcony, Wi-Fi, Fan"},
            {"room_number": "A-202", "block_name": "Block A (North)", "room_type": "Deluxe Suite", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 45000, "amenities": "Dual AC, Refrigerator, Sofa, Attached Luxury Bath, Wi-Fi"},
            {"room_number": "B-101", "block_name": "Block B (South)", "room_type": "Single", "capacity": 1, "current_occupancy": 0, "status": "Available", "price_per_term": 35000, "amenities": "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"},
            {"room_number": "B-102", "block_name": "Block B (South)", "room_type": "Double", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 24000, "amenities": "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Balcony"},
            {"room_number": "B-103", "block_name": "Block B (South)", "room_type": "Double", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 24000, "amenities": "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Balcony"},
            {"room_number": "B-201", "block_name": "Block B (South)", "room_type": "Triple", "capacity": 3, "current_occupancy": 0, "status": "Available", "price_per_term": 18000, "amenities": "3 Beds, 3 Lockers, Spacious Hallway, High-Speed Wi-Fi"},
            {"room_number": "B-202", "block_name": "Block B (South)", "room_type": "Deluxe Suite", "capacity": 2, "current_occupancy": 0, "status": "Available", "price_per_term": 45000, "amenities": "Dual AC, Mini Fridge, Study Lounge, Balcony, Wi-Fi"}
        ]
        supabase.table('rooms').insert(rooms_data).execute()
        print(f"[OK] Seeded {len(rooms_data)} hostel rooms.")
        rooms_check = supabase.table('rooms').select('*').execute()

    # 3. Students
    stu_check = supabase.table('students').select('*').execute()
    if not stu_check.data or len(stu_check.data) == 0:
        stu_pwd = generate_password_hash('student123')
        students_data = [
            {"roll_number": "STU202401", "full_name": "Aarav Sharma", "email": "aarav@hostel.edu", "password_hash": stu_pwd, "phone": "+91 98765 43210", "department": "Computer Science & Engg", "gender": "Male", "emergency_contact": "Mr. S. Sharma (+91 98765 43211)"},
            {"roll_number": "STU202402", "full_name": "Rohan Mehta", "email": "rohan@hostel.edu", "password_hash": stu_pwd, "phone": "+91 98765 43212", "department": "Information Technology", "gender": "Male", "emergency_contact": "Mrs. K. Mehta (+91 98765 43213)"},
            {"roll_number": "STU202403", "full_name": "Priya Patel", "email": "priya@hostel.edu", "password_hash": stu_pwd, "phone": "+91 98765 43214", "department": "Electronics & Communication", "gender": "Female", "emergency_contact": "Dr. A. Patel (+91 98765 43215)"},
            {"roll_number": "STU202404", "full_name": "Sneha Reddy", "email": "sneha@hostel.edu", "password_hash": stu_pwd, "phone": "+91 98765 43216", "department": "Mechanical Engineering", "gender": "Female", "emergency_contact": "Mr. V. Reddy (+91 98765 43217)"},
            {"roll_number": "STU202405", "full_name": "Vikram Singh", "email": "vikram@hostel.edu", "password_hash": stu_pwd, "phone": "+91 98765 43218", "department": "Civil Engineering", "gender": "Male", "emergency_contact": "Capt. H. Singh (+91 98765 43219)"}
        ]
        supabase.table('students').insert(students_data).execute()
        print(f"[OK] Seeded {len(students_data)} demo students.")
        stu_check = supabase.table('students').select('*').execute()

    # Map student rolls to IDs
    student_map = {s['roll_number']: s['student_id'] for s in stu_check.data}
    room_map = {r['room_number']: r for r in rooms_check.data}

    # 4. Bookings Seed
    bookings_check = supabase.table('bookings').select('*').execute()
    if not bookings_check.data or len(bookings_check.data) == 0:
        bookings_to_create = []
        if 'STU202401' in student_map and 'A-103' in room_map:
            bookings_to_create.append({"student_id": student_map['STU202401'], "room_id": room_map['A-103']['room_id'], "allocation_date": "2026-08-01", "status": "Active", "remarks": "Fall 2026 Term Allocation"})
        if 'STU202402' in student_map and 'A-103' in room_map:
            bookings_to_create.append({"student_id": student_map['STU202402'], "room_id": room_map['A-103']['room_id'], "allocation_date": "2026-08-02", "status": "Active", "remarks": "Fall 2026 Term Allocation"})
        if 'STU202403' in student_map and 'B-102' in room_map:
            bookings_to_create.append({"student_id": student_map['STU202403'], "room_id": room_map['B-102']['room_id'], "allocation_date": "2026-08-05", "status": "Active", "remarks": "Fall 2026 Term Allocation"})
        if 'STU202405' in student_map and 'A-201' in room_map:
            bookings_to_create.append({"student_id": student_map['STU202405'], "room_id": room_map['A-201']['room_id'], "allocation_date": "2026-08-10", "status": "Active", "remarks": "Fall 2026 Term Allocation"})

        if bookings_to_create:
            supabase.table('bookings').insert(bookings_to_create).execute()
            print(f"[OK] Seeded {len(bookings_to_create)} room allocations.")

            # Update room occupancies in Supabase
            if 'A-103' in room_map:
                supabase.table('rooms').update({"current_occupancy": 2, "status": "Full"}).eq('room_id', room_map['A-103']['room_id']).execute()
            if 'B-102' in room_map:
                supabase.table('rooms').update({"current_occupancy": 1, "status": "Available"}).eq('room_id', room_map['B-102']['room_id']).execute()
            if 'A-201' in room_map:
                supabase.table('rooms').update({"current_occupancy": 1, "status": "Available"}).eq('room_id', room_map['A-201']['room_id']).execute()

    # 5. Complaints Seed
    complaints_check = supabase.table('complaints').select('*').execute()
    if not complaints_check.data or len(complaints_check.data) == 0:
        complaints_data = []
        if 'STU202401' in student_map and 'A-103' in room_map:
            complaints_data.append({
                "student_id": student_map['STU202401'],
                "room_id": room_map['A-103']['room_id'],
                "title": "Ceiling fan speed regulator broken",
                "category": "Electrical",
                "priority": "Medium",
                "description": "The ceiling fan only runs at maximum speed #5, regulator knob does not lower speed.",
                "status": "Pending"
            })
        if 'STU202403' in student_map and 'B-102' in room_map:
            complaints_data.append({
                "student_id": student_map['STU202403'],
                "room_id": room_map['B-102']['room_id'],
                "title": "Water geyser valve leakage in washroom",
                "category": "Plumbing",
                "priority": "High",
                "description": "Minor water leakage from geyser safety valve when heating.",
                "status": "In Progress",
                "admin_remarks": "Hostel maintenance plumber notified. Service scheduled for tomorrow morning."
            })
        if 'STU202405' in student_map and 'A-201' in room_map:
            complaints_data.append({
                "student_id": student_map['STU202405'],
                "room_id": room_map['A-201']['room_id'],
                "title": "Study chair wheel caster loose",
                "category": "Furniture",
                "priority": "Low",
                "description": "One caster wheel on the study chair came off.",
                "status": "Resolved",
                "admin_remarks": "Replaced with brand new heavy-duty wheel caster on 2026-08-15."
            })

        if complaints_data:
            supabase.table('complaints').insert(complaints_data).execute()
            print(f"[OK] Seeded {len(complaints_data)} sample complaints into Supabase.")

    print("[SUCCESS] Live Supabase Database is fully seeded and synchronized!")
    return True

if __name__ == '__main__':
    seed_supabase_live()
