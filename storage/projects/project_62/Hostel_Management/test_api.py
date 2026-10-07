import unittest
import json
import time
from app import create_app
from setup_database import setup_all

class HostelAPITestCase(unittest.TestCase):
    def setUp(self):
        setup_all()
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_01_dashboard_stats(self):
        res = self.client.get('/api/stats/dashboard')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreater(data['data']['total_rooms'], 0)
        self.assertGreater(data['data']['total_students'], 0)

    def test_02_admin_login(self):
        res = self.client.post('/api/auth/admin/login', json={
            'username': 'admin',
            'password': 'admin123'
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['role'], 'admin')

    def test_03_student_login(self):
        res = self.client.post('/api/auth/student/login', json={
            'identifier': 'STU202401',
            'password': 'student123'
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['user']['roll_number'], 'STU202401')

    def test_04_student_registration(self):
        ts = int(time.time() * 1000)
        res = self.client.post('/api/students', json={
            'roll_number': f'STUTEST_{ts}',
            'full_name': 'Test Candidate',
            'email': f'testcandidate_{ts}@hostel.edu',
            'password': 'password123',
            'phone': '+91 99999 88888',
            'department': 'Robotics Engineering',
            'gender': 'Male',
            'emergency_contact': 'Guardian (+91 99999 77777)'
        })
        self.assertEqual(res.status_code, 201)
        data = json.loads(res.data)
        self.assertTrue(data['success'])

    def test_05_room_listing_and_allocation(self):
        # 1. Fetch available rooms
        res = self.client.get('/api/rooms?available_only=true')
        self.assertEqual(res.status_code, 200)
        rooms = json.loads(res.data)['data']
        self.assertGreater(len(rooms), 0)
        target_room = rooms[0]

        # 2. Allocate unallocated student (STU202404 - Sneha Reddy)
        stu_res = self.client.get('/api/students?search=STU202404')
        students = json.loads(stu_res.data)['data']
        sneha = students[0]

        alloc_res = self.client.post('/api/bookings/allocate', json={
            'student_id': sneha['student_id'],
            'room_id': target_room['room_id'],
            'allocation_date': '2026-08-26',
            'remarks': 'Unit Test Allocation'
        })
        self.assertEqual(alloc_res.status_code, 201)

        # 3. Raise Complaint
        comp_res = self.client.post('/api/complaints', json={
            'student_id': sneha['student_id'],
            'room_id': target_room['room_id'],
            'title': 'Test Room Light Flickering',
            'category': 'Electrical',
            'priority': 'Medium',
            'description': 'Main fluorescent tube light flickers on startup.'
        })
        self.assertEqual(comp_res.status_code, 201)
        comp_data = json.loads(comp_res.data)['data']

        # 4. Resolve Complaint
        patch_res = self.client.patch(f"/api/complaints/{comp_data['complaint_id']}", json={
            'status': 'Resolved',
            'admin_remarks': 'Choke replaced by maintenance.'
        })
        self.assertEqual(patch_res.status_code, 200)

        # 5. Vacate Room
        vacate_res = self.client.post('/api/bookings/vacate', json={
            'student_id': sneha['student_id'],
            'remarks': 'Unit Test Vacate'
        })
        self.assertEqual(vacate_res.status_code, 200)

if __name__ == '__main__':
    unittest.main()
