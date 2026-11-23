/**
 * dashboard.js — Teacher & System Dashboard Analytics Visualisations
 */

let distChartInstance = null;
let compChartInstance = null;

const Dashboard = {
  async initTeacherDashboard() {
    const user = Auth.checkAuth(['teacher', 'administrator']);
    if (!user) return;

    await this.loadClassDropdown();
    this.setupEventListeners();
  },

  async loadClassDropdown() {
    try {
      const classes = await Api.get('/api/classes');
      const select = document.getElementById('class-selector');
      if (!select) return;

      select.innerHTML = '';
      if (classes.length === 0) {
        select.innerHTML = '<option value="">No classes assigned</option>';
        return;
      }

      classes.forEach((c, idx) => {
        const opt = document.createElement('option');
        opt.value = c.id;
        opt.textContent = `${c.class_name} - ${c.section} (${c.academic_session}) [${c.student_count} Students]`;
        if (idx === 0) opt.selected = true;
        select.appendChild(opt);
      });

      // Load analytics for the initially selected class
      const initialClassId = select.value;
      if (initialClassId) {
        await this.loadClassAnalytics(initialClassId);
      }
    } catch (err) {
      console.error('Failed to load classes:', err);
    }
  },

  setupEventListeners() {
    const select = document.getElementById('class-selector');
    if (select) {
      select.addEventListener('change', (e) => {
        if (e.target.value) {
          this.loadClassAnalytics(e.target.value);
        }
      });
    }
  },

  async loadClassAnalytics(classId) {
    try {
      const data = await Api.get(`/api/dashboard/class/${classId}`);
      this.renderStatCards(data);
      this.renderCharts(data);
      await this.loadInsightsPreview(classId);
      await this.loadStudentOverview(classId);
    } catch (err) {
      console.error('Failed to load class analytics:', err);
    }
  },

  renderStatCards(data) {
    document.getElementById('stat-total-enrolled').textContent = data.total_enrolled;
    
    document.getElementById('stat-avg-score').textContent = 
      data.average_total_marks !== null ? `${data.average_total_marks} / 40` : '—';
    
    const rangeEl = document.getElementById('stat-score-range');
    if (rangeEl) {
      if (data.highest_total_marks !== null && data.lowest_total_marks !== null) {
        rangeEl.textContent = `${data.lowest_total_marks} – ${data.highest_total_marks}`;
      } else {
        rangeEl.textContent = '—';
      }
    }

    document.getElementById('stat-incomplete-count').textContent = data.incomplete_records_count;
    document.getElementById('stat-support-count').textContent = data.support_needed_count;
  },

  renderCharts(data) {
    // 1. Score Distribution Chart
    const distCtx = document.getElementById('chart-distribution');
    if (distCtx) {
      if (distChartInstance) distChartInstance.destroy();

      const distData = data.score_distribution;
      distChartInstance = new Chart(distCtx, {
        type: 'bar',
        data: {
          labels: Object.keys(distData),
          datasets: [{
            label: 'Students in Score Range (out of 40)',
            data: Object.values(distData),
            backgroundColor: ['#dc2626', '#f59e0b', '#3b82f6', '#10b981'],
            borderRadius: 4,
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (ctx) => ` ${ctx.raw} student(s)`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              ticks: { stepSize: 1 },
              title: { display: true, text: 'Number of Students' }
            },
            x: {
              title: { display: true, text: 'Total Mid-Semester Score Range' }
            }
          }
        }
      });
    }

    // 2. Component-wise Average Comparison Chart
    const compCtx = document.getElementById('chart-components');
    if (compCtx) {
      if (compChartInstance) compChartInstance.destroy();

      const compData = data.component_averages;
      const labels = ['Midterm (Max 30)', 'Assignment (Max 3)', 'Presentation (Max 3)', 'Attendance (Max 4)', 'Sessional (Max 10)'];
      const averages = [
        compData.midterm.average || 0,
        compData.assignment.average || 0,
        compData.presentation.average || 0,
        compData.attendance.average || 0,
        compData.sessional.average || 0,
      ];
      const maxes = [30, 3, 3, 4, 10];
      const percentages = [
        compData.midterm.pct || 0,
        compData.assignment.pct || 0,
        compData.presentation.pct || 0,
        compData.attendance.pct || 0,
        compData.sessional.pct || 0,
      ];

      compChartInstance = new Chart(compCtx, {
        type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: 'Class Average % of Max',
              data: percentages,
              backgroundColor: '#1e3a8a',
              borderRadius: 4,
            }
          ]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            tooltip: {
              callbacks: {
                label: (ctx) => ` Average: ${averages[ctx.dataIndex]} / ${maxes[ctx.dataIndex]} (${ctx.raw}%)`
              }
            }
          },
          scales: {
            y: {
              beginAtZero: true,
              max: 100,
              ticks: { callback: (v) => `${v}%` },
              title: { display: true, text: 'Percentage of Component Maximum' }
            }
          }
        }
      });
    }
  },

  async loadInsightsPreview(classId) {
    const container = document.getElementById('insights-preview-container');
    if (!container) return;

    try {
      const res = await Api.get(`/api/dashboard/insights/class/${classId}`);
      const insights = res.insights || [];

      if (insights.length === 0) {
        container.innerHTML = `
          <div class="alert alert-info">
            All enrolled students currently have complete records and steady mid-semester progress.
          </div>
        `;
        return;
      }

      // Display top 3 insights with link to full view
      const preview = insights.slice(0, 3);
      container.innerHTML = preview.map(i => `
        <div class="insight-card severity-${i.severity.toLowerCase()}">
          <div class="insight-header">
            <span class="insight-title">${i.student_name} (${i.student_id})</span>
            <span class="badge ${i.severity === 'High' ? 'badge-danger' : 'badge-warning'}">${i.insight_type}</span>
          </div>
          <div class="insight-desc">${i.description}</div>
          <div class="insight-recommendation"><strong>Recommendation:</strong> ${i.recommendation}</div>
        </div>
      `).join('');

      if (insights.length > 3) {
        container.innerHTML += `
          <div style="text-align: right; margin-top: 8px;">
            <a href="/static/pages/insights.html?class_id=${classId}" class="btn btn-outline btn-sm">
              View All ${insights.length} Support Insights →
            </a>
          </div>
        `;
      }
    } catch (err) {
      console.error('Failed to load insights preview:', err);
    }
  },

  async loadStudentOverview(classId) {
    const tbody = document.getElementById('student-table-body');
    if (!tbody) return;

    try {
      const records = await Api.get(`/api/assessments/class/${classId}`);
      if (records.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;">No students enrolled in this class.</td></tr>';
        return;
      }

      tbody.innerHTML = records.map(r => `
        <tr>
          <td><strong>${r.student_id}</strong></td>
          <td>${r.student_name}</td>
          <td>${r.midterm_marks !== null ? `${r.midterm_marks} / 30` : '<span class="mark-missing">Missing</span>'}</td>
          <td>${r.assignment_marks !== null ? `${r.assignment_marks} / 3` : '<span class="mark-missing">Missing</span>'}</td>
          <td>${r.presentation_marks !== null ? `${r.presentation_marks} / 3` : '<span class="mark-missing">Missing</span>'}</td>
          <td>${r.attendance_marks !== null ? `${r.attendance_marks} / 4` : '<span class="mark-missing">Missing</span>'}</td>
          <td><strong>${r.total_marks !== null ? `${r.total_marks} / 40` : '<span class="mark-missing">Incomplete</span>'}</strong></td>
          <td>
            <a href="/static/pages/student-details.html?id=${r.student_id}" class="btn btn-outline btn-sm">
              View Profile
            </a>
          </td>
        </tr>
      `).join('');
    } catch (err) {
      console.error('Failed to load student table:', err);
    }
  }
};
