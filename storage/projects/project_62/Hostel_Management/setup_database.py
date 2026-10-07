import os
import sys
import sqlite3
import psycopg2
from werkzeug.security import generate_password_hash
from config import Config

def init_supabase_database():
    """Initializes Supabase PostgreSQL database schema."""
    try:
        conn = None
        if Config.DATABASE_URL:
            conn = psycopg2.connect(Config.DATABASE_URL)
        elif Config.DB_HOST and Config.DB_PASSWORD:
            conn = psycopg2.connect(
                host=Config.DB_HOST,
                port=Config.DB_PORT,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME
            )

        if not conn:
            print("[INFO] No Supabase DATABASE_URL configured in .env.")
            return False

        cursor = conn.cursor()
        schema_path = os.path.join(os.path.dirname(__file__), 'supabase_schema.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_content = f.read()

        cursor.execute(sql_content)
        conn.commit()
        cursor.close()
        conn.close()
        print("[OK] Supabase PostgreSQL Schema initialized successfully.")
        return True
    except Exception as err:
        print(f"[INFO] Supabase connection note: {err}")
        return False

def init_sqlite_database():
    """Initializes SQLite fallback database with equivalent schema."""
    db_path = Config.SQLITE_DB_PATH
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Admins
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            role TEXT DEFAULT 'Chief Warden',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Students
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            roll_number TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            phone TEXT NOT NULL,
            department TEXT NOT NULL,
            gender TEXT NOT NULL,
            emergency_contact TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 3. Rooms
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            room_id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT NOT NULL UNIQUE,
            block_name TEXT NOT NULL,
            room_type TEXT NOT NULL,
            capacity INTEGER NOT NULL DEFAULT 1,
            current_occupancy INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Available',
            price_per_term REAL DEFAULT 0.0,
            amenities TEXT
        );
    """)

    # 4. Bookings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            allocation_date TEXT NOT NULL,
            vacate_date TEXT,
            status TEXT NOT NULL DEFAULT 'Active',
            remarks TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
        );
    """)

    # 5. Complaints
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            complaint_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            room_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL DEFAULT 'Medium',
            date_raised TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'Pending',
            admin_remarks TEXT,
            resolved_date TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
            FOREIGN KEY (room_id) REFERENCES rooms(room_id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()
    print("[OK] Local Database schema initialized.")
    return True

def seed_data():
    """Seeds rich sample data into active database (Supabase / Local)."""
    from models import Admin, Student, Room, Booking, Complaint
    from db import fetch_one

    # 1. Admin Seed
    admin_exists = fetch_one("SELECT admin_id FROM admins WHERE username = %s", ("admin",))
    if not admin_exists:
        Admin.create(
            username="admin",
            password="admin123",
            full_name="Prof. Robert Vance (Chief Warden)",
            email="warden@hostel.edu",
            role="Chief Warden"
        )
        print("[OK] Created Demo Admin: username='admin', password='admin123'")

    # 2. Rooms Seed
    existing_rooms = fetch_one("SELECT COUNT(*) AS count FROM rooms")
    if not existing_rooms or existing_rooms["count"] == 0:
        rooms_data = [
            # Block A - Boys Hostel / North Wing
            ("A-101", "Block A (North)", "Single", 1, 35000, "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"),
            ("A-102", "Block A (North)", "Single", 1, 35000, "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"),
            ("A-103", "Block A (North)", "Double", 2, 24000, "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Ceiling Fan"),
            ("A-104", "Block A (North)", "Double", 2, 24000, "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Ceiling Fan"),
            ("A-201", "Block A (North)", "Triple", 3, 18000, "3 Single Beds, 3 Wardrobes, Balcony, Wi-Fi, Fan"),
            ("A-202", "Block A (North)", "Deluxe Suite", 2, 45000, "Dual AC, Refrigerator, Sofa, Attached Luxury Bath, Wi-Fi"),
            
            # Block B - Girls Hostel / South Wing
            ("B-101", "Block B (South)", "Single", 1, 35000, "Attached Washroom, Study Table, AC, Balcony, Wi-Fi"),
            ("B-102", "Block B (South)", "Double", 2, 24000, "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Balcony"),
            ("B-103", "Block B (South)", "Double", 2, 24000, "2 Study Desks, Wardrobes, High-Speed Wi-Fi, Balcony"),
            ("B-201", "Block B (South)", "Triple", 3, 18000, "3 Beds, 3 Lockers, Spacious Hallway, High-Speed Wi-Fi"),
            ("B-202", "Block B (South)", "Deluxe Suite", 2, 45000, "Dual AC, Mini Fridge, Study Lounge, Balcony, Wi-Fi"),
        ]
        for r_num, blk, r_type, cap, price, amen in rooms_data:
            Room.create(r_num, blk, r_type, cap, price, amen)
        print(f"[OK] Seeded {len(rooms_data)} hostel rooms across Block A & Block B.")

    # 3. Students Seed
    existing_students = fetch_one("SELECT COUNT(*) AS count FROM students")
    if not existing_students or existing_students["count"] == 0:
        students_data = [
            ("STU202401", "Aarav Sharma", "aarav@hostel.edu", "student123", "+91 98765 43210", "Computer Science & Engg", "Male", "Mr. S. Sharma (+91 98765 43211)"),
            ("STU202402", "Rohan Mehta", "rohan@hostel.edu", "student123", "+91 98765 43212", "Information Technology", "Male", "Mrs. K. Mehta (+91 98765 43213)"),
            ("STU202403", "Priya Patel", "priya@hostel.edu", "student123", "+91 98765 43214", "Electronics & Communication", "Female", "Dr. A. Patel (+91 98765 43215)"),
            ("STU202404", "Sneha Reddy", "sneha@hostel.edu", "student123", "+91 98765 43216", "Mechanical Engineering", "Female", "Mr. V. Reddy (+91 98765 43217)"),
            ("STU202405", "Vikram Singh", "vikram@hostel.edu", "student123", "+91 98765 43218", "Civil Engineering", "Male", "Capt. H. Singh (+91 98765 43219)")
        ]
        student_id_map = {}
        for roll, name, email, pwd, phone, dept, gender, emg in students_data:
            sid = Student.create(roll, name, email, pwd, phone, dept, gender, emg)
            student_id_map[roll] = sid
        print(f"[OK] Seeded {len(students_data)} demo students (Password: 'student123').")

        # 4. Allocations / Bookings Seed
        r_a103 = Room.get_by_room_number("A-103")
        r_b102 = Room.get_by_room_number("B-102")
        r_a201 = Room.get_by_room_number("A-201")
        
        if r_a103 and "STU202401" in student_id_map and "STU202402" in student_id_map:
            Booking.allocate(student_id_map["STU202401"], r_a103["room_id"], "2026-08-01", "Fall 2026 Room Allocation")
            Booking.allocate(student_id_map["STU202402"], r_a103["room_id"], "2026-08-02", "Fall 2026 Room Allocation")
        
        if r_b102 and "STU202403" in student_id_map:
            Booking.allocate(student_id_map["STU202403"], r_b102["room_id"], "2026-08-05", "Fall 2026 Room Allocation")

        if r_a201 and "STU202405" in student_id_map:
            Booking.allocate(student_id_map["STU202405"], r_a201["room_id"], "2026-08-10", "Fall 2026 Room Allocation")

        print("[OK] Created sample room bookings with real-time occupancy updates.")

        # 5. Complaints Seed
        if "STU202401" in student_id_map and r_a103:
            Complaint.create(student_id_map["STU202401"], r_a103["room_id"], "Ceiling fan speed regulator broken", "Electrical", "The ceiling fan only runs at maximum speed #5, regulator knob does not lower speed.", "Medium")
        
        if "STU202403" in student_id_map and r_b102:
            cid = Complaint.create(student_id_map["STU202403"], r_b102["room_id"], "Water geyser valve leakage in washroom", "Plumbing", "Minor water leakage from geyser safety valve when heating.", "High")
            Complaint.update_status(cid, "In Progress", "Hostel maintenance plumber notified. Service scheduled for tomorrow morning.")

        if "STU202405" in student_id_map and r_a201:
            cid2 = Complaint.create(student_id_map["STU202405"], r_a201["room_id"], "Study chair wheel caster loose", "Furniture", "One caster wheel on the study chair came off.", "Low")
            Complaint.update_status(cid2, "Resolved", "Replaced with brand new heavy-duty wheel caster on 2026-08-15.")

        print("[OK] Created sample complaints across Pending, In Progress, and Resolved states.")

def setup_all():
    print("==================================================")
    print("Hostel Management System - Supabase Database Initializer")
    print("==================================================")
    supabase_ok = init_supabase_database()
    if not supabase_ok:
        print("[INFO] Initializing local database schema...")
        init_sqlite_database()
    
    seed_data()
    print("==================================================")
    print("[SUCCESS] Setup Complete! System is ready to run.")
    print("Demo Accounts:")
    print("  * Admin:   username: admin     | password: admin123")
    print("  * Student: roll: STU202401     | password: student123")
    print("  * Student: roll: STU202404     | password: student123 (Unallocated)")
    print("==================================================")

if __name__ == '__main__':
    setup_all()
