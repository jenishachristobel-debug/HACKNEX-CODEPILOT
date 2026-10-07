/**
 * Student Portal Controller
 * Manages Student Profile, Room Browsing, Instant Room Booking, Complaints, and Vacating.
 */

let currentStudent = null;
let allocatedRoomData = null;
let allRooms = [];
let activeTypeFilter = '';
let activeBlockFilter = '';
let activeAvailableOnly = false;

document.addEventListener('DOMContentLoaded', async () => {
  currentStudent = await API.checkAuthGuard('student');
  if (!currentStudent) return;

  renderStudentNavProfile();
  await loadStudentRoomDetails();
  await loadAvailableRooms();
  await loadStudentComplaints();
  initStudentEventListeners();
});

function renderStudentNavProfile() {
  const nameEl = document.getElementById('student-nav-name');
  if (nameEl) nameEl.innerText = currentStudent.full_name;

  const heroName = document.getElementById('hero-student-name');
  if (heroName) heroName.innerText = currentStudent.full_name;

  const heroRoll = document.getElementById('hero-student-roll');
  if (heroRoll) heroRoll.innerText = currentStudent.roll_number;

  const heroDept = document.getElementById('hero-student-dept');
  if (heroDept) heroDept.innerText = currentStudent.department;

  const heroEmail = document.getElementById('hero-student-email');
  if (heroEmail) heroEmail.innerText = currentStudent.email;

  const heroPhone = document.getElementById('hero-student-phone');
  if (heroPhone) heroPhone.innerText = currentStudent.phone;

  const avatar = document.getElementById('student-avatar-initial');
  if (avatar) avatar.innerText = currentStudent.full_name.charAt(0).toUpperCase();
}

/**
 * Loads current room allocation & roommates
 */
async function loadStudentRoomDetails() {
  try {
    const res = await API.get(`/api/students/${currentStudent.student_id}/room`);
    const myRoomBox = document.getElementById('my-room-container');
    const complaintRoomSelect = document.getElementById('complaint-room-id');
    const complaintNotice = document.getElementById('complaint-unallocated-notice');
    const complaintForm = document.getElementById('complaint-form-box');

    if (res.allocated && res.data) {
      allocatedRoomData = res.data;
      
      // Update room in complaint form
      if (complaintRoomSelect) {
        complaintRoomSelect.innerHTML = `<option value="${res.data.room_id}">Allocated Room: ${res.data.room_number} (${res.data.block_name})</option>`;
      }
      if (complaintNotice) complaintNotice.style.display = 'none';
      if (complaintForm) complaintForm.style.display = 'block';

      // Render My Room Card
      myRoomBox.innerHTML = `
        <div class="card" style="border: 1px solid var(--border-subtle); background: var(--surface-container-lowest); box-shadow: var(--shadow-md);">
          <div class="card-header" style="border-bottom: 1px solid var(--border-subtle); padding-bottom: 1.25rem; margin-bottom: 1.25rem;">
            <div>
              <span class="badge badge-active" style="background: var(--primary-fixed); color: var(--primary);">Allocated Room</span>
              <h2 style="margin-top: 0.4rem; font-size: 1.8rem; color: var(--text-main); font-weight: 800;">${escapeHtml(res.data.room_number)}</h2>
              <p style="color: var(--text-muted); font-size: 0.9rem;">${escapeHtml(res.data.block_name)} • ${escapeHtml(res.data.room_type)}</p>
            </div>
            <button class="btn btn-danger btn-sm" onclick="promptVacateRoom(${res.data.booking_id}, '${res.data.room_number}')">
              Vacate Room
            </button>
          </div>

          <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0;">
            <div style="background: var(--surface-container-low); border: 1px solid var(--border-subtle); padding: 0.85rem; border-radius: var(--radius-md);">
              <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Allocation Date</span>
              <h4 style="color: var(--text-main); margin-top: 0.2rem; font-weight: 700;">${formatDate(res.data.allocation_date)}</h4>
            </div>
            <div style="background: var(--surface-container-low); border: 1px solid var(--border-subtle); padding: 0.85rem; border-radius: var(--radius-md);">
              <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Capacity / Occupancy</span>
              <h4 style="color: var(--emerald); margin-top: 0.2rem; font-weight: 700;">${res.data.current_occupancy} of ${res.data.capacity} Beds Occupied</h4>
            </div>
            <div style="background: var(--surface-container-low); border: 1px solid var(--border-subtle); padding: 0.85rem; border-radius: var(--radius-md);">
              <span style="font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase;">Term Fee</span>
              <h4 style="color: var(--primary); margin-top: 0.2rem; font-weight: 700;">${formatCurrency(res.data.price_per_term)} / term</h4>
            </div>
          </div>

          ${res.data.amenities ? `
            <div style="margin: 1.5rem 0;">
              <span style="font-size: 0.8rem; color: var(--text-muted); font-weight:600; text-transform: uppercase;">Amenities:</span>
              <div class="amenities-list" style="margin-top: 0.35rem;">
                ${res.data.amenities.split(',').map(a => `<span class="amenity-tag">${escapeHtml(a.trim())}</span>`).join('')}
              </div>
            </div>
          ` : ''}

          <div style="margin-top: 2rem; border-top: 1px solid var(--border-subtle); padding-top: 1.5rem;">
            <h4 style="font-size: 0.95rem; margin-bottom: 1rem; color: var(--text-main); text-transform: uppercase; letter-spacing: 0.05em;">
              Roommates (${res.data.roommates.length})
            </h4>
            ${res.data.roommates.length === 0 ? `
              <p style="font-size: 0.85rem; color: var(--text-muted);">No other roommates currently sharing this room.</p>
            ` : `
              <div class="roommates-grid">
                ${res.data.roommates.map(rm => `
                  <div class="roommate-card">
                    <div class="roommate-icon">${escapeHtml(rm.full_name.charAt(0))}</div>
                    <div>
                      <strong style="display:block; font-size: 0.9rem; color: var(--text-main);">${escapeHtml(rm.full_name)}</strong>
                      <span style="font-size: 0.775rem; color: var(--text-muted);">${escapeHtml(rm.roll_number)} • ${escapeHtml(rm.department)}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            `}
          </div>
        </div>
      `;

      // Update hero badge
      const heroRoomBadge = document.getElementById('hero-student-room-badge');
      if (heroRoomBadge) {
        heroRoomBadge.innerHTML = `<span class="badge badge-active">Allocated: Room ${escapeHtml(res.data.room_number)}</span>`;
      }
    } else {
      allocatedRoomData = null;
      myRoomBox.innerHTML = `
        <div class="card" style="text-align: center; padding: 2.5rem 1.5rem;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">🛏️</div>
          <h3>No Room Allocated Yet</h3>
          <p style="max-width: 440px; margin: 0.5rem auto 1.25rem;">
            You do not have an active hostel room allocation. Browse the rooms below and book an available bed.
          </p>
          <a href="#rooms-section" class="btn btn-primary btn-sm">Browse Available Rooms ↓</a>
        </div>
      `;
      if (complaintNotice) complaintNotice.style.display = 'block';
      if (complaintForm) complaintForm.style.display = 'none';

      const heroRoomBadge = document.getElementById('hero-student-room-badge');
      if (heroRoomBadge) {
        heroRoomBadge.innerHTML = `<span class="badge badge-pending">Unallocated</span>`;
      }
    }
  } catch (err) {
    console.error('Error loading student room info:', err);
  }
}

/**
 * Loads room inventory & real-time availability
 */
async function loadAvailableRooms() {
  try {
    const params = {};
    if (activeTypeFilter) params.room_type = activeTypeFilter;
    if (activeBlockFilter) params.block = activeBlockFilter;
    if (activeAvailableOnly) params.available_only = 'true';

    const res = await API.get('/api/rooms', params);
    allRooms = res.data || [];
    renderRoomsGrid(allRooms);
  } catch (err) {
    showToast('Failed to load room listings.', 'error');
  }
}

function renderRoomsGrid(rooms) {
  const container = document.getElementById('rooms-grid-container');
  if (!container) return;

  if (rooms.length === 0) {
    container.innerHTML = `
      <div class="empty-state" style="grid-column: 1 / -1;">
        <div class="empty-state-icon">🔍</div>
        <h3>No rooms match your filter criteria</h3>
        <p>Try selecting a different room type or clearing your filters.</p>
      </div>
    `;
    return;
  }

  container.innerHTML = rooms.map(room => {
    const isFull = room.current_occupancy >= room.capacity;
    const isMaintenance = room.status === 'Maintenance';
    const isAllocatedToMe = allocatedRoomData && allocatedRoomData.room_id === room.room_id;
    const occupancyPercent = Math.min(100, Math.round((room.current_occupancy / room.capacity) * 100));

    let statusBadge = '';
    if (isMaintenance) {
      statusBadge = '<span class="badge badge-full">Maintenance</span>';
    } else if (isFull) {
      statusBadge = '<span class="badge badge-full">Full</span>';
    } else {
      statusBadge = `<span class="badge badge-available">${room.available_beds} Bed${room.available_beds > 1 ? 's' : ''} Available</span>`;
    }

    const amenitiesList = room.amenities 
      ? room.amenities.split(',').map(a => `<span class="amenity-tag">${escapeHtml(a.trim())}</span>`).join('') 
      : '';

    return `
      <div class="room-card">
        <div>
          <div class="room-card-header">
            <div>
              <span class="room-block">${escapeHtml(room.block_name)}</span>
              <div class="room-number">${escapeHtml(room.room_number)}</div>
            </div>
            ${statusBadge}
          </div>

          <div style="display: flex; justify-content: space-between; align-items: baseline; margin: 0.5rem 0;">
            <span style="font-weight: 600; font-size: 0.9rem; color: var(--text-main);">${escapeHtml(room.room_type)}</span>
            <span style="color: var(--cyan); font-weight: 700; font-size: 0.95rem;">${formatCurrency(room.price_per_term)}<span style="font-size:0.75rem; color:var(--text-muted);">/term</span></span>
          </div>

          <div style="margin: 0.75rem 0;">
            <div style="display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-muted); margin-bottom: 0.25rem;">
              <span>Occupancy</span>
              <span><strong>${room.current_occupancy}</strong> / ${room.capacity} Beds</span>
            </div>
            <div class="occupancy-meter">
              <div class="occupancy-fill ${occupancyPercent >= 100 ? 'high' : ''}" style="width: ${occupancyPercent}%;"></div>
            </div>
          </div>

          <div class="amenities-list">
            ${amenitiesList}
          </div>
        </div>

        <div style="margin-top: 1rem; padding-top: 0.75rem; border-top: 1px solid var(--border-subtle);">
          ${isAllocatedToMe ? `
            <button class="btn btn-secondary btn-sm" style="width: 100%; border-color: var(--primary);" disabled>
              ✓ Currently Your Room
            </button>
          ` : isFull || isMaintenance ? `
            <button class="btn btn-secondary btn-sm" style="width: 100%; opacity: 0.5;" disabled>
              ${isMaintenance ? 'Under Maintenance' : 'Room Full'}
            </button>
          ` : `
            <button class="btn btn-primary btn-sm" style="width: 100%;" onclick="openBookingModal(${room.room_id}, '${room.room_number}', '${room.room_type}', '${room.block_name}', ${room.price_per_term})">
              Book Bed in Room ${escapeHtml(room.room_number)} →
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');
}

/**
 * Booking Modal & Allocation Logic
 */
window.openBookingModal = (roomId, roomNumber, roomType, blockName, price) => {
  if (allocatedRoomData) {
    showToast(`You already have an active room (${allocatedRoomData.room_number}). Please vacate your current room first.`, 'warning', 5000);
    return;
  }

  const modal = document.getElementById('booking-modal');
  if (!modal) return;

  document.getElementById('booking-room-id').value = roomId;
  document.getElementById('booking-modal-room-num').innerText = roomNumber;
  document.getElementById('booking-modal-room-type').innerText = `${roomType} (${blockName})`;
  document.getElementById('booking-modal-student').innerText = `${currentStudent.full_name} (${currentStudent.roll_number})`;
  document.getElementById('booking-modal-price').innerText = formatCurrency(price);
  
  // Set default allocation date to today
  const today = new Date().toISOString().split('T')[0];
  document.getElementById('booking-alloc-date').value = today;

  openModal('booking-modal');
};

/**
 * Student Complaints List
 */
async function loadStudentComplaints() {
  try {
    const res = await API.get('/api/complaints', { student_id: currentStudent.student_id });
    const container = document.getElementById('my-complaints-list');
    if (!container) return;

    const complaints = res.data || [];
    if (complaints.length === 0) {
      container.innerHTML = `
        <div class="empty-state" style="padding: 2rem 1rem;">
          <div class="empty-state-icon">📋</div>
          <h4>No complaints raised</h4>
          <p style="font-size: 0.85rem;">If you experience any issues in your room, submit a maintenance ticket above.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = complaints.map(c => {
      let statusBadge = '';
      if (c.status === 'Resolved') statusBadge = '<span class="badge badge-resolved">Resolved</span>';
      else if (c.status === 'In Progress') statusBadge = '<span class="badge badge-in-progress">In Progress</span>';
      else statusBadge = '<span class="badge badge-pending">Pending Review</span>';

      return `
        <div class="complaint-item">
          <div class="complaint-item-header">
            <div style="display:flex; align-items:center; gap:0.5rem;">
              <span class="complaint-category-pill">${escapeHtml(c.category)}</span>
              <strong style="font-size: 0.95rem; color: var(--text-main);">${escapeHtml(c.title)}</strong>
            </div>
            ${statusBadge}
          </div>
          
          <p style="font-size: 0.875rem; color: var(--text-muted); margin: 0.35rem 0;">
            ${escapeHtml(c.description)}
          </p>

          <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.775rem; color: var(--text-subtle); margin-top: 0.5rem;">
            <span>Room: <strong>${escapeHtml(c.room_number)}</strong> • Priority: <strong>${escapeHtml(c.priority)}</strong></span>
            <span>Raised: ${formatDate(c.date_raised)}</span>
          </div>

          ${c.admin_remarks ? `
            <div class="complaint-remark-box">
              <strong style="color: var(--primary); display:block; font-size: 0.775rem; margin-bottom: 0.15rem;">
                Hostel Warden Response (${c.resolved_date ? formatDate(c.resolved_date) : 'Update'}):
              </strong>
              ${escapeHtml(c.admin_remarks)}
            </div>
          ` : ''}
        </div>
      `;
    }).join('');
  } catch (err) {
    console.error('Error loading complaints:', err);
  }
}

/**
 * Prompt Vacate Room
 */
window.promptVacateRoom = async (bookingId, roomNumber) => {
  if (!confirm(`Are you sure you want to vacate Room ${roomNumber}? This will release your bed allocation.`)) {
    return;
  }

  try {
    const res = await API.post('/api/bookings/vacate', {
      booking_id: bookingId,
      remarks: 'Vacated by student through student portal'
    });

    showToast(res.message || 'Room vacated successfully.', 'success');
    await loadStudentRoomDetails();
    await loadAvailableRooms();
  } catch (err) {
    showToast(err.message || 'Failed to vacate room.', 'error');
  }
};

/**
 * Event Listeners Initializer
 */
function initStudentEventListeners() {
  // Booking Form Submit
  const bookingForm = document.getElementById('booking-form');
  if (bookingForm) {
    bookingForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roomId = document.getElementById('booking-room-id').value;
      const allocDate = document.getElementById('booking-alloc-date').value;
      const remarks = document.getElementById('booking-remarks').value.trim() || 'Self-service room booking';

      const submitBtn = bookingForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Allocating Bed...';

      try {
        const res = await API.post('/api/bookings/allocate', {
          student_id: currentStudent.student_id,
          room_id: parseInt(roomId, 10),
          allocation_date: allocDate,
          remarks: remarks
        });

        closeModal('booking-modal');
        showToast(res.message || 'Room booked successfully!', 'success');
        
        await loadStudentRoomDetails();
        await loadAvailableRooms();

        // Scroll to my room
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (err) {
        showToast(err.message || 'Booking allocation failed.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Confirm Room Allocation';
      }
    });
  }

  // Complaint Form Submit
  const complaintForm = document.getElementById('complaint-form');
  if (complaintForm) {
    complaintForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!allocatedRoomData) {
        showToast('You must have an allocated room to raise a room complaint.', 'warning');
        return;
      }

      const title = document.getElementById('complaint-title').value.trim();
      const category = document.getElementById('complaint-category').value;
      const priority = document.getElementById('complaint-priority').value;
      const description = document.getElementById('complaint-description').value.trim();

      const submitBtn = complaintForm.querySelector('button[type="submit"]');
      submitBtn.disabled = true;
      submitBtn.innerText = 'Submitting Ticket...';

      try {
        const res = await API.post('/api/complaints', {
          student_id: currentStudent.student_id,
          room_id: allocatedRoomData.room_id,
          title,
          category,
          priority,
          description
        });

        showToast(res.message || 'Complaint submitted successfully!', 'success');
        complaintForm.reset();
        await loadStudentComplaints();
      } catch (err) {
        showToast(err.message || 'Failed to submit complaint.', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerText = 'Submit Complaint Ticket';
      }
    });
  }

  // Filter Buttons
  const typeFilters = document.querySelectorAll('.type-filter-btn');
  typeFilters.forEach(btn => {
    btn.addEventListener('click', () => {
      typeFilters.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeTypeFilter = btn.dataset.type || '';
      loadAvailableRooms();
    });
  });

  const blockSelect = document.getElementById('filter-block-select');
  if (blockSelect) {
    blockSelect.addEventListener('change', (e) => {
      activeBlockFilter = e.target.value;
      loadAvailableRooms();
    });
  }

  const availOnlyCheckbox = document.getElementById('filter-available-only');
  if (availOnlyCheckbox) {
    availOnlyCheckbox.addEventListener('change', (e) => {
      activeAvailableOnly = e.target.checked;
      loadAvailableRooms();
    });
  }
}
