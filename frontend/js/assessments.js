/**
 * assessments.js — Mid-Semester Marks Entry and Real-Time Validation
 */

const Assessments = {
  currentRecords: [],

  async init() {
    const user = Auth.checkAuth(['administrator', 'teacher']);
    if (!user) return;

    await this.loadClassDropdown();
    this.setupListeners();
  },

  async loadClassDropdown() {
    try {
      const classes = await Api.get('/api/classes');
      const select = document.getElementById('assessment-class-select');
      if (!select) return;

      select.innerHTML = '';
      if (classes.length === 0) {
        select.innerHTML = '<option value="">No classes available</option>';
        return;
      }

      classes.forEach((c, idx) => {
        select.innerHTML += `<option value="${c.id}" ${idx === 0 ? 'selected' : ''}>${c.class_name} - ${c.section}</option>`;
      });

      if (classes.length > 0) {
        await this.loadAssessmentTable(classes[0].id);
      }
    } catch (err) {
      console.error('Failed to load class options:', err);
    }
  },

  setupListeners() {
    const select = document.getElementById('assessment-class-select');
    if (select) {
      select.addEventListener('change', (e) => {
        if (e.target.value) this.loadAssessmentTable(e.target.value);
      });
    }

    const filterStatus = document.getElementById('filter-completeness');
    if (filterStatus) {
      filterStatus.addEventListener('change', () => this.filterTable());
    }
  },

  async loadAssessmentTable(classId) {
    try {
      const records = await Api.get(`/api/assessments/class/${classId}`);
      this.currentRecords = records;
      this.renderTable(records);
    } catch (err) {
      console.error('Failed to load assessment records:', err);
    }
  },

  filterTable() {
    const filter = document.getElementById('filter-completeness')?.value || 'all';
    let filtered = this.currentRecords;

    if (filter === 'complete') {
      filtered = this.currentRecords.filter(r => r.is_complete);
    } else if (filter === 'incomplete') {
      filtered = this.currentRecords.filter(r => !r.is_complete);
    }

    this.renderTable(filtered);
  },

  renderTable(records) {
    const tbody = document.getElementById('assessments-table-body');
    if (!tbody) return;

    if (records.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No assessment records found.</td></tr>';
      return;
    }

    tbody.innerHTML = records.map(r => `
      <tr id="row-${r.student_id}">
        <td><strong>${r.student_id}</strong></td>
        <td>${r.student_name}</td>
        <td>
          <input type="number" step="0.1" min="0" max="30" class="form-control form-control-sm mark-input"
                 data-student="${r.student_id}" data-component="midterm"
                 value="${r.midterm_marks !== null ? r.midterm_marks : ''}" placeholder="0–30">
        </td>
        <td>
          <input type="number" step="0.1" min="0" max="3" class="form-control form-control-sm mark-input"
                 data-student="${r.student_id}" data-component="assignment"
                 value="${r.assignment_marks !== null ? r.assignment_marks : ''}" placeholder="0–3">
        </td>
        <td>
          <input type="number" step="0.1" min="0" max="3" class="form-control form-control-sm mark-input"
                 data-student="${r.student_id}" data-component="presentation"
                 value="${r.presentation_marks !== null ? r.presentation_marks : ''}" placeholder="0–3">
        </td>
        <td>
          <input type="number" step="0.1" min="0" max="4" class="form-control form-control-sm mark-input"
                 data-student="${r.student_id}" data-component="attendance"
                 value="${r.attendance_marks !== null ? r.attendance_marks : ''}" placeholder="0–4">
        </td>
        <td class="total-cell" id="total-${r.student_id}">
          ${r.total_marks !== null 
            ? `<strong>${r.total_marks} / 40</strong>` 
            : `<span class="badge badge-warning">Incomplete</span>`}
        </td>
        <td>
          <button class="btn btn-primary btn-sm" onclick="Assessments.saveStudentMarks('${r.student_id}')">
            Save
          </button>
        </td>
      </tr>
    `).join('');
  },

  async saveStudentMarks(studentId) {
    const row = document.getElementById(`row-${studentId}`);
    if (!row) return;

    const midInput = row.querySelector('[data-component="midterm"]').value.trim();
    const assignInput = row.querySelector('[data-component="assignment"]').value.trim();
    const presInput = row.querySelector('[data-component="presentation"]').value.trim();
    const attInput = row.querySelector('[data-component="attendance"]').value.trim();

    // Parse marks (empty string becomes null)
    const parse = (v, max, name) => {
      if (v === '') return null;
      const num = parseFloat(v);
      if (isNaN(num)) throw new Error(`${name} must be numeric.`);
      if (num < 0 || num > max) throw new Error(`${name} must be between 0 and ${max}.`);
      return num;
    };

    try {
      const mid = parse(midInput, 30, 'Midterm');
      const assign = parse(assignInput, 3, 'Assignment');
      const pres = parse(presInput, 3, 'Presentation');
      const att = parse(attInput, 4, 'Attendance (marks out of 4, NOT percentage)');

      const updated = await Api.put(`/api/assessments/${studentId}`, {
        midterm_marks: mid,
        assignment_marks: assign,
        presentation_marks: pres,
        attendance_marks: att,
      });

      Api.showToast(`Marks for student ${studentId} saved successfully.`, 'success');

      // Update total cell in real time
      const totalCell = document.getElementById(`total-${studentId}`);
      if (totalCell) {
        totalCell.innerHTML = updated.total_marks !== null
          ? `<strong>${updated.total_marks} / 40</strong>`
          : `<span class="badge badge-warning">Incomplete</span>`;
      }
    } catch (err) {
      Api.showToast(err.message, 'error');
    }
  }
};
