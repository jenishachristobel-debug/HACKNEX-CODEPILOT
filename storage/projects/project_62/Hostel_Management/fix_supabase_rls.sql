-- ==========================================================================
-- SUPABASE SQL EDITOR SCRIPT: DISABLE RLS OR ENABLE FULL ACCESS POLICIES
-- Run this in Supabase Dashboard -> SQL Editor to allow backend API access
-- ==========================================================================

-- Option A: Disable RLS for full backend API access (Recommended for custom Flask backend)
ALTER TABLE IF EXISTS admins DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS students DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS rooms DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS bookings DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS complaints DISABLE ROW LEVEL SECURITY;

-- Option B: Alternatively, add open access policies (if you prefer RLS enabled)
DO $$
BEGIN
    DROP POLICY IF EXISTS "Allow All admins" ON admins;
    DROP POLICY IF EXISTS "Allow All students" ON students;
    DROP POLICY IF EXISTS "Allow All rooms" ON rooms;
    DROP POLICY IF EXISTS "Allow All bookings" ON bookings;
    DROP POLICY IF EXISTS "Allow All complaints" ON complaints;

    CREATE POLICY "Allow All admins" ON admins FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY "Allow All students" ON students FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY "Allow All rooms" ON rooms FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY "Allow All bookings" ON bookings FOR ALL USING (true) WITH CHECK (true);
    CREATE POLICY "Allow All complaints" ON complaints FOR ALL USING (true) WITH CHECK (true);
EXCEPTION WHEN OTHERS THEN
    NULL;
END $$;
