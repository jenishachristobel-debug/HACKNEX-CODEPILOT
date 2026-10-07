# Hostel Management System (HostelEase) — Supabase & PostgreSQL Edition

A complete, full-stack **Hostel Management Web Application** designed for university housing administration and student residents. Built with **Python (Flask)** RESTful backend, **Supabase** (PostgreSQL) cloud database, and modern responsive **Vanilla HTML5/CSS3/JavaScript** frontend.

---

## ⚡ Supabase Database Architecture

The application is configured to connect to **Supabase** via PostgreSQL connection pooling or direct connection strings using `psycopg2` and `supabase-py`.

### Schema Design (`supabase_schema.sql`):
1. **`admins` Table**: Warden accounts with PBKDF2 SHA-256 hashed passwords.
2. **`students` Table**: Student resident profiles, roll numbers, departments, and credentials.
3. **`rooms` Table**: Real-time room inventory with bed capacities, amenities, and occupancy counts.
4. **`bookings` Table**: Active allocations, move-in dates, vacate dates, and status (`Active`, `Vacated`).
5. **`complaints` Table**: Categorized maintenance tickets (*Electrical, Plumbing, Furniture, Cleanliness, Internet*) with resolution lifecycle.

---

## 🚀 Setting Up with Supabase

### Step 1: Create a Supabase Project
1. Log in to [supabase.com](https://supabase.com) and create a new project (e.g., `hostel-management`).
2. Go to **Project Settings** $\rightarrow$ **Database**.
3. Under **Connection string**, select **URI** (or **Session Pooler**).
   Example format:
   ```
   postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
   ```

### Step 2: Configure Environment (`.env`)
Update [`.env`](file:///d:/sem3/Hostel_Management/.env) with your Supabase connection string:
```env
# Paste your Supabase Connection URI here:
DATABASE_URL=postgresql://postgres.yourprojectref:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# (Optional) Supabase API credentials
SUPABASE_URL=https://yourprojectref.supabase.co
SUPABASE_KEY=your-anon-or-service-role-key

SECRET_KEY=hostel_management_supabase_secret_key_2026
```

### Step 3: Run Database Setup & Seeder
Execute the automated initialization script:
```bash
python setup_database.py
```
This automatically creates the schema in Supabase (or local fallback if offline) and seeds default rooms, student accounts, active allocations, and maintenance tickets.

### Step 4: Start the Web Server
```bash
python app.py
```
Open [`http://127.0.0.1:5000`](http://127.0.0.1:5000) in your browser.

---

## 🔑 Default Demo Accounts

Access [`http://127.0.0.1:5000/login`](http://127.0.0.1:5000/login) (with 1-click quick demo buttons):

| Portal | Username / Identifier | Password | Description |
|---|---|---|---|
| **Warden Admin** | `admin` | `admin123` | Prof. Robert Vance (Chief Warden) |
| **Allocated Student** | `STU202401` | `student123` | Aarav Sharma (Room A-103, active roommates & complaints) |
| **Unallocated Student** | `STU202404` | `student123` | Sneha Reddy (Ready to browse and book an available bed) |

---

## 🧪 Testing & Verification

Run automated test suites anytime:
- Unit tests: `python test_api.py`
- Live HTTP end-to-end tests: `python verify_live.py`
