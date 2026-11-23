/**
 * students.js — Student Record Management
 */

const Students = {
  currentStudents: [],

  async init() {
    const user = Auth.checkAuth(['administrator', 'teacher']);
    if (!user) return;

    if (user.role === 'administrator') {
      const addBtn = document.getElementById('btn-add-student-modal');
      if (addBtn) addBtn.style.display = 'inline-flex';
    }

    await this.loadClassFilter();
    await this.fetchStudents();
    this.setupListeners();
  },

  async loadClassFilter() {
    try {
      const classes = await Api.get('/api/classes');
      const select = document.getElementById('filter-class');
      const modalSelect = document.getElementById('modal-student-class');

      if (select) {
        select.innerHTML = '<option value="">All Permitted Classes</option>';
        classes.forEach(c => {
          select.innerHTML += `<option value="${c.id}">${c.class_name} - ${c.section}</option>`;
        });
      }

      if (modalSelect) {
        modalSelect.innerHTML = '';
        classes.forEach(c => {
          modalSelect.innerHTML += `<option value="${c.id}">${c.class_name} - ${c.section}</option>`;
        });
      }
    } catch (err) {
      console.error('Failed to load classes:', err);
    }
  },

  async fetchStudents() {
    const classId = document.getElementById('filter-class')?.value || null;
    const search = document.getElementById('search-input')?.value || null;

    const params = {};
    if (classId) params.class_id = classId;
    if (search) params.search = search;

    try {
      const students = await Api.get('/api/students', params);
      this.currentStudents = students;
      this.renderStudentTable(students);
    } catch (err) {
      console.error('Failed to fetch students:', err);
    }
  },

  renderStudentTable(students) {
    const tbody = document.getElementById('students-table-body');
    const countEl = document.getElementById('student-count-badge');
    if (countEl) countEl.textContent = `${students.length} Student(s)`;

    if (!tbody) return;

    if (students.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No students found matching current filters.</td></tr>';
      return;
    }

    const user = Api.getUser();
    const isAdmin = user && user.role === 'administrator';

    tbody.innerHTML = students.map(s => `
      <tr>
        <td><strong>${s.student_id}</strong></td>
        <td>${s.student_name}</td>
        <td>${s.class_name} - ${s.section}</td>
        <td>${s.academic_session}</td>
        <td>
          <a href="/static/pages/student-details.html?id=${s.student_id}" class="btn btn-outline btn-sm">
            View Details
          </a>
        </td>
        ${isAdmin ? `
          <td>
            <button class="btn btn-danger btn-sm" onclick="Students.deleteStudent('${s.student_id}')">
              Delete
            </button>
          </td>
        ` : ''}
      </tr>
    `).join('');
  },

  setupListeners() {
    const filterClass = document.getElementById('filter-class');
    const searchInput = document.getElementById('search-input');

    if (filterClass) {
      filterClass.addEventListener('change', () => this.fetchStudents());
    }

    if (searchInput) {
      let debounceTimeout;
      searchInput.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(() => this.fetchStudents(), 300);
      });
    }

    // Modal submit
    const form = document.getElementById('add-student-form');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.submitAddStudent();
      });
    }
  },

  async submitAddStudent() {
    const studentId = document.getElementById('modal-student-id').value.trim();
    const studentName = document.getElementById('modal-student-name').value.trim();
    const classId = parseInt(document.getElementById('modal-student-class').value, 10);

    if (!studentId || !studentName || isNaN(classId)) {
      Api.showToast('Please fill all required fields.', 'error');
      return;
    }

    try {
      await Api.post('/api/students', {
        student_id: studentId,
        student_name: studentName,
        class_id: classId,
      });
      Api.showToast(`Student ${studentId} created successfully.`, 'success');
      this.closeModal();
      await this.fetchStudents();
    } catch (err) {
      // Error handled by Api.request
    }
  },

  async deleteStudent(studentId) {
    if (!confirm(`Are you sure you want to delete student '${studentId}'? All associated assessments will also be deleted.`)) {
      return;
    }

    try {
      await Api.delete(`/api/students/${studentId}`);
      Api.showToast(`Student ${studentId} deleted.`, 'success');
      await this.fetchStudents();
    } catch (err) {
      // Error handled by Api.request
    }
  },

  openModal() {
    const modal = document.getElementById('add-student-modal');
    if (modal) modal.style.display = 'flex';
  },

  closeModal() {
    const modal = document.getElementById('add-student-modal');
    if (modal) modal.style.display = 'none';
    const form = document.getElementById('add-student-form');
    if (form) form.reset();
  }
};
