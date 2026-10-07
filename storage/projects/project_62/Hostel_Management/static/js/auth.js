/**
 * Authentication Module: Login & Registration Controller
 */

document.addEventListener('DOMContentLoaded', () => {
  initAuthTabs();

  initFormSubmissions();
});

function initAuthTabs() {
  const tabs = document.querySelectorAll('.auth-tab-btn');
  const forms = {
    'student-login': document.getElementById('student-login-form-box'),
    'admin-login': document.getElementById('admin-login-form-box'),
    'student-register': document.getElementById('student-register-form-box')
  };

  const authCard = document.querySelector('.auth-card');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');

      const target = tab.dataset.tab;
      Object.keys(forms).forEach(key => {
        if (forms[key]) {
          forms[key].style.display = (key === target) ? 'block' : 'none';
        }
      });

      if (authCard) {
        if (target === 'student-register') {
          authCard.classList.add('wide');
        } else {
          authCard.classList.remove('wide');
        }
      }
    });
  });
}



function switchAuthTab(tabName) {
  const tabBtn = document.querySelector(`.auth-tab-btn[data-tab="${tabName}"]`);
  if (tabBtn) tabBtn.click();
}

function initFormSubmissions() {
  // 1. Student Login
  const studentLoginForm = document.getElementById('student-login-form');
  if (studentLoginForm) {
    studentLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const identifier = document.getElementById('student-identifier').value.trim();
      const password = document.getElementById('student-password').value;
      const submitBtn = studentLoginForm.querySelector('button[type="submit"]');

      if (!identifier || !password) {
        showToast('Please enter your Roll Number / Email and password.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerText = 'Logging in...';

      try {
        const res = await API.post('/api/auth/student/login', { identifier, password });
        showToast(res.message || 'Login successful!', 'success');
        setTimeout(() => {
          window.location.href = '/student';
        }, 600);
      } catch (err) {
        showToast(err.message || 'Student login failed.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerText = 'Student Login →';
      }
    });
  }

  // 2. Admin Login
  const adminLoginForm = document.getElementById('admin-login-form');
  if (adminLoginForm) {
    adminLoginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('admin-username').value.trim();
      const password = document.getElementById('admin-password').value;
      const submitBtn = adminLoginForm.querySelector('button[type="submit"]');

      if (!username || !password) {
        showToast('Please enter admin username and password.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerText = 'Verifying...';

      try {
        const res = await API.post('/api/auth/admin/login', { username, password });
        showToast(res.message || 'Admin authentication verified!', 'success');
        setTimeout(() => {
          window.location.href = '/admin';
        }, 600);
      } catch (err) {
        showToast(err.message || 'Admin login failed.', 'error');
        submitBtn.disabled = false;
        submitBtn.innerText = 'Warden / Admin Login →';
      }
    });
  }

  // 3. Student Registration Form
  const registerForm = document.getElementById('student-register-form');
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const roll_number = document.getElementById('reg-roll').value.trim();
      const full_name = document.getElementById('reg-name').value.trim();
      const email = document.getElementById('reg-email').value.trim();
      const password = document.getElementById('reg-password').value;
      const phone = document.getElementById('reg-phone').value.trim();
      const department = document.getElementById('reg-dept').value.trim();
      const gender = document.getElementById('reg-gender').value;
      const emergency_contact = document.getElementById('reg-emergency').value.trim();

      const submitBtn = registerForm.querySelector('button[type="submit"]');

      if (!roll_number || !full_name || !email || !password || !phone || !department || !gender) {
        showToast('Please fill in all required fields.', 'warning');
        return;
      }

      submitBtn.disabled = true;
      submitBtn.innerText = 'Registering Student...';

      try {
        const res = await API.post('/api/students', {
          roll_number, full_name, email, password, phone, department, gender, emergency_contact
        });

        showToast('Registration successful! Logging you in...', 'success');
        
        // Auto-login after registration
        const loginRes = await API.post('/api/auth/student/login', { identifier: roll_number, password });
        setTimeout(() => {
          window.location.href = '/student';
        }, 800);
      } catch (err) {
        const errorMsg = (err.data && err.data.errors) ? err.data.errors.join(' ') : (err.message || 'Registration failed.');
        showToast(errorMsg, 'error');
        submitBtn.disabled = false;
        submitBtn.innerText = 'Complete Registration';
      }
    });
  }
}
