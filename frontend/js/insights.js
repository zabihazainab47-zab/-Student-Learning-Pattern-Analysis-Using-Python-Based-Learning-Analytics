/**
 * insights.js — Evidence-Based Academic Support Insights
 */

const Insights = {
  currentInsights: [],

  async init() {
    const user = Auth.checkAuth(['administrator', 'teacher']);
    if (!user) return;

    await this.loadClassDropdown();
    this.setupListeners();
  },

  async loadClassDropdown() {
    try {
      const classes = await Api.get('/api/classes');
      const select = document.getElementById('insights-class-select');
      if (!select) return;

      select.innerHTML = '';
      classes.forEach((c, idx) => {
        select.innerHTML += `<option value="${c.id}" ${idx === 0 ? 'selected' : ''}>${c.class_name} - ${c.section}</option>`;
      });

      if (classes.length > 0) {
        // Read URL query param if navigated from dashboard
        const urlParams = new URLSearchParams(window.location.search);
        const classParam = urlParams.get('class_id');
        const targetId = classParam ? parseInt(classParam, 10) : classes[0].id;
        select.value = targetId;

        await this.loadInsights(targetId);
      }
    } catch (err) {
      console.error('Failed to load class list for insights:', err);
    }
  },

  setupListeners() {
    const select = document.getElementById('insights-class-select');
    if (select) {
      select.addEventListener('change', (e) => {
        if (e.target.value) this.loadInsights(e.target.value);
      });
    }

    const filterType = document.getElementById('filter-insight-type');
    if (filterType) {
      filterType.addEventListener('change', () => this.filterInsights());
    }
  },

  async loadInsights(classId) {
    try {
      const res = await Api.get(`/api/dashboard/insights/class/${classId}`);
      this.currentInsights = res.insights || [];
      this.renderInsightsList(this.currentInsights);
    } catch (err) {
      console.error('Failed to fetch class insights:', err);
    }
  },

  filterInsights() {
    const type = document.getElementById('filter-insight-type')?.value || 'all';
    let filtered = this.currentInsights;

    if (type !== 'all') {
      filtered = this.currentInsights.filter(i => i.category.toLowerCase().includes(type.toLowerCase()) || i.insight_type.toLowerCase().includes(type.toLowerCase()));
    }

    this.renderInsightsList(filtered);
  },

  renderInsightsList(insights) {
    const container = document.getElementById('insights-cards-container');
    const countBadge = document.getElementById('insights-total-badge');
    if (countBadge) countBadge.textContent = `${insights.length} Identified Pattern(s)`;

    if (!container) return;

    if (insights.length === 0) {
      container.innerHTML = `
        <div class="card" style="text-align: center; padding: 40px;">
          <h3>No Support Alerts Identified</h3>
          <p style="margin-top: 8px;">All students in this class currently meet baseline progression criteria.</p>
        </div>
      `;
      return;
    }

    container.innerHTML = insights.map(i => {
      const sevClass = i.severity.toLowerCase();
      const badgeClass = i.severity === 'High' ? 'badge-danger' : (i.severity === 'Attention' ? 'badge-warning' : 'badge-info');

      return `
        <div class="insight-card severity-${sevClass}">
          <div class="insight-header">
            <div>
              <span class="insight-title">${i.student_name}</span>
              <span style="font-size: 12px; color: var(--text-muted); margin-left: 8px;">(${i.student_id})</span>
            </div>
            <div>
              <span class="badge ${badgeClass}">${i.insight_type}</span>
              <span class="badge badge-info" style="margin-left: 4px;">${i.category}</span>
            </div>
          </div>
          <div class="insight-desc">${i.description}</div>
          <div class="insight-recommendation">
            <strong>Evidence-Based Suggestion:</strong> ${i.recommendation}
          </div>
          <div style="margin-top: 10px; display: flex; justify-content: flex-end;">
            <a href="/static/pages/student-details.html?id=${i.student_id}" class="btn btn-outline btn-sm">
              Open Individual Student Profile →
            </a>
          </div>
        </div>
      `;
    }).join('');
  }
};
