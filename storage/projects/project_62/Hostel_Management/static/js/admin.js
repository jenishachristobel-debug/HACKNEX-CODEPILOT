/**
 * Admin Dashboard & Management Portal Controller
 * Manages Stats, Rooms, Students, Allocations, Vacating, and Complaint Resolution.
 */

let currentAdmin = null;
let allRoomsList = [];
let allStudentsList = [];
let allBookingsList = [];
let allComplaintsList = [];

let activeComplaintFilter = '';
let activePriorityFilter = '';

document.addEventListener('DOMContentLoaded', async () => {
  currentAdmin = await API.checkAuthGuard('admin');
  if (!currentAdmin) return;

  renderAdminNavProfile();
  initAdminTabs();
  initAdminModals();

  // Load initial data
  await loadDashboardStats();
  await loadRoomsTable();
  await loadStudentsTable();
  await loadBookingsTable();
  await loadComplaintsTable();
});

function renderAdminNavProfile() {
  const nameEl = document.getElementById('admin-nav-name');
  if (nameEl) nameEl.innerText = currentAdmin.full_name;

  const roleEl = document.getElementById('admin-nav-role');
  if (roleEl) roleEl.innerText = currentAdmin.title || 'Chief Warden';
}

function initAdminTabs() {
  const tabs = document.querySelectorAll('.admin-tab-btn');
  const sections = {
    'overview': document.getElementById('section-overview'),
    'rooms': document.getElementById('section-rooms'),
    'students': document.getElementById('section-students'),
    'bookings': document.getElementById('section-bookings'),
    'complaints': document.getElementById('section-complaints')
  };

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.dataset.tab;
      Object.keys(sections).forEach(key => {
        if (sections[key]) {
          sections[key].style.display = (key === target) ? 'block' : 'none';
        }
      });

      // Reload section specific data
      if (target === 'overview') loadDashboardStats();
      if (target === 'rooms') loadRoomsTable();
      if (target === 'students') loadStudentsTable();
      if (target === 'bookings') loadBookingsTable();
      if (target === 'complaints') loadComplaintsTable();
    });
  });
}

/**
 * Loads Dashboard Metrics & Visuals
 */
async function loadDashboardStats() {
  try {
    const res = await API.get('/api/stats/dashboard');
    const data = res.data;

    // Stat Cards
    document.getElementById('stat-total-students').innerText = data.total_students;
    document.getElementById('stat-total-rooms').innerText = data.total_rooms;
    document.getElementById('stat-occupied-beds').innerText = `${data.occupied_beds} / ${data.total_capacity}`;
    document.getElementById('stat-available-beds').innerText = data.available_beds;
    document.getElementById('stat-occupancy-rate').innerText = `${data.occupancy_rate}%`;
    document.getElementById('stat-pending-complaints').innerText = data.pending_complaints;

    // Occupancy Meter in Stat Card
    const bar = document.getElementById('stat-occupancy-bar');
    if (bar) bar.style.width = `${data.occupancy_rate}%`;

    // Room Distribution
    const distContainer = document.getElementById('room-distribution-container');
    if (distContainer && data.room_types) {
      distContainer.innerHTML = data.room_types.map(rt => {
        const rate = rt.capacity > 0 ? Math.round((rt.occupied / rt.capacity) * 100) : 0;
        return `
          <div class="room-dist-card">
            <div style="display:flex; justify-content:space-between; margin-bottom: 0.35rem;">
              <strong style="font-size: 0.9rem; color: var(--text-main);">${escapeHtml(rt.room_type)}</strong>
              <span style="font-size: 0.8rem; color: var(--cyan); font-weight:700;">${rt.occupied}/${rt.capacity} Beds</span>
            </div>
            <div class="occupancy-meter" style="height: 6px;">
              <div class="occupancy-fill" style="width: ${rate}%;"></div>
            </div>
            <span style="font-size: 0.75rem; color: var(--text-muted);">${rt.count} Rooms Total</span>
          </div>
        `;
      }).join('');
    }

    // Recent Bookings Mini-Table
    const recentBContainer = document.getElementById('recent-bookings-body');
    if (recentBContainer && data.recent_bookings) {
      if (data.recent_bookings.length === 0) {
        recentBContainer.innerHTML = `<tr><td colspan="4" class="empty-state">No recent bookings recorded.</td></tr>`;
      } else {
        recentBContainer.innerHTML = data.recent_bookings.map(b => `
          <tr>
            <td><strong>${escapeHtml(b.student_name)}</strong><br><small style="color:var(--text-muted);">${escapeHtml(b.roll_number)}</small></td>
            <td><span class="badge badge-active">${escapeHtml(b.room_number)}</span></td>
            <td>${formatDate(b.allocation_date)}</td>
            <td><span class="badge badge-${b.status.toLowerCase()}">${escapeHtml(b.status)}</span></td>
          </tr>
        `).join('');
      }
    }

    // Recent Complaints Mini-Table
    const recentCContainer = document.getElementById('recent-complaints-body');
    if (recentCContainer && data.recent_complaints) {
      if (data.recent_complaints.length === 0) {
        recentCContainer.innerHTML = `<tr><td colspan="4" class="empty-state">No complaints logged.</td></tr>`;
      } else {
        recentCContainer.innerHTML = data.recent_complaints.map(c => `
          <tr>
            <td><strong>${escapeHtml(c.title)}</strong><br><small style="color:var(--text-muted);">${escapeHtml(c.category)} • Room ${escapeHtml(c.room_number)}</small></td>
            <td><span class="priority-pill priority-${c.priority.toLowerCase()}">${escapeHtml(c.priority)}</span></td>
            <td><span class="badge badge-${c.status.toLowerCase().replace(' ', '-')}">${escapeHtml(c.status)}</span></td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="openResolveModal(${c.complaint_id}, '${escapeHtml(c.title)}', '${c.status}', '${escapeHtml(c.admin_remarks || '')}')">
                Manage
              </button>
            </td>
          </tr>
        `).join('');
      }
    }
  } catch (err) {
    showToast('Error loading dashboard statistics.', 'error');
  }
}

/**
 * Rooms Management
 */
async function loadRoomsTable() {
  try {
    const res = await API.get('/api/rooms');
    allRoomsList = res.data || [];
    renderRoomsTable(allRoomsList);
  } catch (err) {
    showToast('Failed to load rooms list.', 'error');
  }
}

function renderRoomsTable(rooms) {
  const tbody = document.getElementById('rooms-table-body');
  if (!tbody) return;

  if (rooms.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No rooms found.</td></tr>`;
    return;
  }

  tbody.innerHTML = rooms.map(r => {
    const occupancyPercent = Math.round((r.current_occupancy / r.capacity) * 100);
    const isFull = r.current_occupancy >= r.capacity;

    let statusBadge = `<span class="badge badge-available">${r.status}</span>`;
    if (r.status === 'Maintenance') statusBadge = `<span class="badge badge-pending">Maintenance</span>`;
    else if (isFull) statusBadge = `<span class="badge badge-full">Full</span>`;

    return `
      <tr>
        <td><strong style="font-size: 1rem; color: var(--text-main);">${escapeHtml(r.room_number)}</strong></td>
        <td>${escapeHtml(r.block_name)}</td>
        <td><span class="badge badge-active">${escapeHtml(r.room_type)}</span></td>
        <td>${r.capacity} Beds</td>
        <td>
          <div style="display:flex; align-items:center; gap:0.5rem;">
            <span><strong>${r.current_occupancy}</strong> / ${r.capacity}</span>
            <div class="occupancy-meter" style="width: 70px; margin: 0;">
              <div class="occupancy-fill ${isFull ? 'high' : ''}" style="width: ${occupancyPercent}%;"></div>
            </div>
          </div>
        </td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="viewRoomOccupants(${r.room_id})">
            View Occupants (${r.current_occupancy})
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

window.viewRoomOccupants = async (roomId) => {
  try {
    const res = await API.get(`/api/rooms/${roomId}`);
    const room = res.data;
    const modal = document.getElementById('room-occupants-modal');
    if (!modal) return;

    document.getElementById('occupants-modal-title').innerText = `Room ${room.room_number} Occupants (${room.current_occupancy}/${room.capacity})`;
    
    const listContainer = document.getElementById('occupants-list-container');
    if (!room.occupants || room.occupants.length === 0) {
      listContainer.innerHTML = `<p class="empty-state">No students currently allocated to this room.</p>`;
    } else {
      listContainer.innerHTML = room.occupants.map(stu => `
        <div style="display:flex; justify-content:space-between; align-items:center; background: var(--bg-surface); padding: 0.85rem; border-radius: var(--radius-md); margin-bottom: 0.5rem; border: 1px solid var(--border-subtle);">
          <div>
            <strong style="display:block; color:var(--text-main);">${escapeHtml(stu.full_name)}</strong>
            <span style="font-size: 0.8rem; color: var(--text-muted);">${escapeHtml(stu.roll_number)} • ${escapeHtml(stu.department)}</span>
            <span style="font-size: 0.75rem; color: var(--cyan); display:block;">Allocated on: ${formatDate(stu.allocation_date)}</span>
          </div>
          <button class="btn btn-danger btn-sm" onclick="adminVacateStudent(${stu.booking_id}, '${escapeHtml(stu.full_name)}', '${room.room_number}')">
            Vacate
          </button>
        </div>
      `).join('');
    }

    openModal('room-occupants-modal');
  } catch (err) {
    showToast('Failed to load room occupants.', 'error');
  }
};

/**
 * Students Directory & Allocation
 */
async function loadStudentsTable() {
  try {
    const searchInput = document.getElementById('student-search-input');
    const search = searchInput ? searchInput.value.trim() : '';
    const res = await API.get('/api/students', { search });
    allStudentsList = res.data || [];
    renderStudentsTable(allStudentsList);
  } catch (err) {
    showToast('Failed to load students roster.', 'error');
  }
}

function renderStudentsTable(students) {
  const tbody = document.getElementById('students-table-body');
  if (!tbody) return;

  if (students.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No students matching query.</td></tr>`;
    return;
  }

  tbody.innerHTML = students.map(s => {
    const isAllocated = s.booking_status === 'Active';
    const roomInfo = isAllocated 
      ? `<span class="badge badge-active">${escapeHtml(s.room_number)} (${escapeHtml(s.block_name)})</span>` 
      : `<span class="badge badge-vacated">Unallocated</span>`;

    return `
      <tr>
        <td><strong>${escapeHtml(s.roll_number)}</strong></td>
        <td>
          <strong style="color:var(--text-main);">${escapeHtml(s.full_name)}</strong><br>
          <small style="color:var(--text-muted);">${escapeHtml(s.email)}</small>
        </td>
        <td>${escapeHtml(s.department)}</td>
        <td>${escapeHtml(s.gender)}</td>
        <td>${escapeHtml(s.phone)}</td>
        <td>${roomInfo}</td>
        <td>
          ${isAllocated ? `
            <button class="btn btn-danger btn-sm" onclick="adminVacateStudent(${s.booking_id}, '${escapeHtml(s.full_name)}', '${s.room_number}')">
              Vacate Room
            </button>
          ` : `
            <button class="btn btn-primary btn-sm" onclick="openAdminAllocateModal(${s.student_id}, '${escapeHtml(s.full_name)}', '${escapeHtml(s.roll_number)}')">
              Allocate Room
            </button>
          `}
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Bookings / Allocation Log Table
 */
async function loadBookingsTable() {
  try {
    const statusSelect = document.getElementById('booking-status-filter');
    const status = statusSelect ? statusSelect.value : '';
    const res = await API.get('/api/bookings', { status });
    allBookingsList = res.data || [];
    renderBookingsTable(allBookingsList);
  } catch (err) {
    showToast('Failed to load bookings history.', 'error');
  }
}

function renderBookingsTable(bookings) {
  const tbody = document.getElementById('bookings-table-body');
  if (!tbody) return;

  if (bookings.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No booking records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = bookings.map(b => {
    const badgeClass = b.status === 'Active' ? 'badge-active' : 'badge-vacated';
    return `
      <tr>
        <td>#BKG-${b.booking_id}</td>
        <td>
          <strong>${escapeHtml(b.student_name)}</strong><br>
          <small style="color:var(--text-muted);">${escapeHtml(b.roll_number)} • ${escapeHtml(b.department)}</small>
        </td>
        <td>
          <span class="badge badge-active">${escapeHtml(b.room_number)}</span><br>
          <small style="color:var(--text-muted);">${escapeHtml(b.block_name)}</small>
        </td>
        <td>${formatDate(b.allocation_date)}</td>
        <td>${b.vacate_date ? formatDate(b.vacate_date) : '<span style="color:var(--text-muted);">—</span>'}</td>
        <td><span class="badge ${badgeClass}">${escapeHtml(b.status)}</span></td>
        <td>
          ${b.status === 'Active' ? `
            <button class="btn btn-danger btn-sm" onclick="adminVacateStudent(${b.booking_id}, '${escapeHtml(b.student_name)}', '${b.room_number}')">
              Vacate
            </button>
          ` : `
            <span style="font-size:0.8rem; color:var(--text-muted);">Closed</span>
          `}
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Complaints Resolution Management
 */
async function loadComplaintsTable() {
  try {
    const params = {};
    if (activeComplaintFilter) params.status = activeComplaintFilter;
    if (activePriorityFilter) params.priority = activePriorityFilter;

    const res = await API.get('/api/complaints', params);
    allComplaintsList = res.data || [];
    renderComplaintsTable(allComplaintsList);
  } catch (err) {
    showToast('Failed to load complaints table.', 'error');
  }
}

function renderComplaintsTable(complaints) {
  const tbody = document.getElementById('complaints-table-body');
  if (!tbody) return;

  if (complaints.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No complaints matching filter criteria.</td></tr>`;
    return;
  }

  tbody.innerHTML = complaints.map(c => {
    let statusBadge = `<span class="badge badge-pending">Pending</span>`;
    if (c.status === 'In Progress') statusBadge = `<span class="badge badge-in-progress">In Progress</span>`;
    else if (c.status === 'Resolved') statusBadge = `<span class="badge badge-resolved">Resolved</span>`;

    return `
      <tr>
        <td>#CMP-${c.complaint_id}</td>
        <td>
          <strong style="color:var(--text-main);">${escapeHtml(c.title)}</strong><br>
          <span style="font-size:0.8rem; color:var(--text-muted);">${escapeHtml(c.description.substring(0, 70))}${c.description.length > 70 ? '...' : ''}</span>
        </td>
        <td>
          <strong>${escapeHtml(c.student_name)}</strong><br>
          <small style="color:var(--text-muted);">Room: ${escapeHtml(c.room_number)} (${escapeHtml(c.roll_number)})</small>
        </td>
        <td><span class="complaint-category-pill">${escapeHtml(c.category)}</span></td>
        <td><span class="priority-pill priority-${c.priority.toLowerCase()}">${escapeHtml(c.priority)}</span></td>
        <td>${statusBadge}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="openResolveModal(${c.complaint_id}, '${escapeHtml(c.title)}', '${c.status}', '${escapeHtml(c.admin_remarks || '')}')">
            Update Status
          </button>
        </td>
      </tr>
    `;
  }).join('');
}

/**
 * Modals Initializer
 */
function initAdminModals() {
  // Add Room Form
  const addRoomForm = document.getElementById('add-room-form');
  if (addRoomForm) {
    addRoomForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const room_number = document.getElementById('new-room-number').value.trim();
      const block_name = document.getElementById('new-room-block').value.trim();
      const room_type = document.getElementById('new-room-type').value;
      const capacity = parseInt(document.getElementById('new-room-capacity').value, 10);
      const price_per_term = parseFloat(document.getElementById('new-room-price').value) || 0;
      const amenities = document.getElementById('new-room-amenities').value.trim();

      try {
        const res = await API.post('/api/rooms', {
          room_number, block_name, room_type, capacity, price_per_term, amenities
        });

        closeModal('add-room-modal');
        showToast(res.message || 'Room added successfully!', 'success');
        addRoomForm.reset();
        await loadRoomsTable();
        await loadDashboardStats();
      } catch (err) {
        showToast(err.message || 'Failed to add room.', 'error');
      }
    });
  }

  // Admin Allocate Form
  const adminAllocateForm = document.getElementById('admin-allocate-form');
  if (adminAllocateForm) {
    adminAllocateForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const student_id = document.getElementById('allocate-student-id').value;
      const room_id = document.getElementById('allocate-room-select').value;
      const alloc_date = document.getElementById('allocate-date-input').value;
      const remarks = document.getElementById('allocate-remarks-input').value.trim();

      if (!room_id) {
        showToast('Please select an available room.', 'warning');
        return;
      }

      try {
        const res = await API.post('/api/bookings/allocate', {
          student_id: parseInt(student_id, 10),
          room_id: parseInt(room_id, 10),
          allocation_date: alloc_date,
          remarks: remarks || 'Allocated by Warden'
        });

        closeModal('admin-allocate-modal');
        showToast(res.message || 'Student room allocated successfully!', 'success');
        await loadStudentsTable();
        await loadRoomsTable();
        await loadBookingsTable();
        await loadDashboardStats();
      } catch (err) {
        showToast(err.message || 'Allocation failed.', 'error');
      }
    });
  }

  // Resolve Complaint Form
  const resolveForm = document.getElementById('resolve-complaint-form');
  if (resolveForm) {
    resolveForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const complaintId = document.getElementById('resolve-complaint-id').value;
      const status = document.getElementById('resolve-status-select').value;
      const admin_remarks = document.getElementById('resolve-remarks-input').value.trim();

      try {
        const res = await API.patch(`/api/complaints/${complaintId}`, {
          status,
          admin_remarks
        });

        closeModal('resolve-complaint-modal');
        showToast(res.message || 'Complaint updated successfully.', 'success');
        await loadComplaintsTable();
        await loadDashboardStats();
      } catch (err) {
        showToast(err.message || 'Failed to update complaint.', 'error');
      }
    });
  }

  // Search & Filter event listeners
  const studentSearch = document.getElementById('student-search-input');
  if (studentSearch) {
    studentSearch.addEventListener('input', () => {
      loadStudentsTable();
    });
  }

  const bookingStatusFilter = document.getElementById('booking-status-filter');
  if (bookingStatusFilter) {
    bookingStatusFilter.addEventListener('change', () => {
      loadBookingsTable();
    });
  }

  // Complaint Status Filter Pills
  const cFilterPills = document.querySelectorAll('.complaint-status-pill');
  cFilterPills.forEach(pill => {
    pill.addEventListener('click', () => {
      cFilterPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      activeComplaintFilter = pill.dataset.status || '';
      loadComplaintsTable();
    });
  });
}

/**
 * Open Admin Allocation Modal
 */
window.openAdminAllocateModal = async (studentId, studentName, rollNumber) => {
  try {
    const res = await API.get('/api/rooms', { available_only: 'true' });
    const availableRooms = res.data || [];

    const modal = document.getElementById('admin-allocate-modal');
    if (!modal) return;

    document.getElementById('allocate-student-id').value = studentId;
    document.getElementById('allocate-student-display').innerText = `${studentName} (${rollNumber})`;

    const select = document.getElementById('allocate-room-select');
    if (availableRooms.length === 0) {
      select.innerHTML = `<option value="">No available rooms with vacant beds</option>`;
    } else {
      select.innerHTML = `
        <option value="">-- Choose an Available Room --</option>
        ${availableRooms.map(r => `
          <option value="${r.room_id}">Room ${r.room_number} (${r.block_name}) - ${r.room_type} (${r.available_beds} beds free, ${formatCurrency(r.price_per_term)})</option>
        `).join('')}
      `;
    }

    const today = new Date().toISOString().split('T')[0];
    document.getElementById('allocate-date-input').value = today;

    openModal('admin-allocate-modal');
  } catch (err) {
    showToast('Failed to fetch available rooms for allocation.', 'error');
  }
};

/**
 * Open Resolve Complaint Modal
 */
window.openResolveModal = (complaintId, title, currentStatus, currentRemarks) => {
  const modal = document.getElementById('resolve-complaint-modal');
  if (!modal) return;

  document.getElementById('resolve-complaint-id').value = complaintId;
  document.getElementById('resolve-complaint-title').innerText = `#CMP-${complaintId}: ${title}`;
  document.getElementById('resolve-status-select').value = currentStatus;
  document.getElementById('resolve-remarks-input').value = currentRemarks || '';

  openModal('resolve-complaint-modal');
};

/**
 * Admin Vacate Student Action
 */
window.adminVacateStudent = async (bookingId, studentName, roomNumber) => {
  if (!confirm(`Are you sure you want to vacate ${studentName} from Room ${roomNumber}? This will free up the bed.`)) {
    return;
  }

  try {
    const res = await API.post('/api/bookings/vacate', {
      booking_id: bookingId,
      remarks: 'Vacated by Warden administration'
    });

    showToast(res.message || 'Room vacated successfully.', 'success');
    closeModal('room-occupants-modal');
    await loadStudentsTable();
    await loadRoomsTable();
    await loadBookingsTable();
    await loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to vacate student.', 'error');
  }
};
