/**
 * data-management.js — CSV Import and Export Operations
 */

const DataManagement = {
  async init() {
    const user = Auth.checkAuth(['administrator', 'teacher']);
    if (!user) return;

    this.setupListeners();
  },

  setupListeners() {
    const uploadForm = document.getElementById('csv-upload-form');
    if (uploadForm) {
      uploadForm.addEventListener('submit', (e) => {
        e.preventDefault();
        this.submitCsvUpload();
      });
    }

    const exportBtn = document.getElementById('btn-export-csv');
    if (exportBtn) {
      exportBtn.addEventListener('click', () => this.downloadCsvExport());
    }
  },

  async submitCsvUpload() {
    const fileInput = document.getElementById('csv-file-input');
    const overwrite = document.getElementById('csv-overwrite-checkbox')?.checked || false;
    const reportBox = document.getElementById('import-report-container');

    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      Api.showToast('Please select a CSV file to upload.', 'error');
      return;
    }

    const file = fileInput.files[0];
    if (!file.name.toLowerCase().endsWith('.csv')) {
      Api.showToast('Please select a valid .csv file.', 'error');
      return;
    }

    const formData = new FormData();
    formData.append('file', file);

    const submitBtn = document.getElementById('btn-submit-import');
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Validating and Importing...';
    }

    try {
      // Use raw fetch so we control Content-Type (do NOT set it — browser sets multipart boundary)
      const token = Api.getToken();
      const response = await fetch(`${window.location.origin}/api/data/import/csv?overwrite=${overwrite}`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` },
        body: formData,
      });

      const res = await response.json();

      if (!response.ok) {
        const msg = res.detail || 'Import failed. Check the server logs.';
        Api.showToast(msg, 'error');
        return;
      }

      Api.showToast(res.message || 'Import complete.', 'success');

      if (reportBox) {
        reportBox.style.display = 'block';
        document.getElementById('report-total-rows').textContent = res.total_rows ?? 0;
        document.getElementById('report-imported-count').textContent = res.imported_count ?? 0;
        document.getElementById('report-skipped-count').textContent = res.skipped_count ?? 0;

        const errorSection = document.getElementById('report-errors-section');
        const errorList = document.getElementById('report-error-list');
        if (errorList && errorSection) {
          if (res.errors && res.errors.length > 0) {
            errorList.innerHTML = res.errors.map(e => `<li>${e}</li>`).join('');
            errorSection.style.display = 'block';
          } else {
            errorList.innerHTML = '';
            errorSection.style.display = 'none';
          }
        }
      }

      fileInput.value = '';
    } catch (err) {
      Api.showToast('Network error during import. Is the server running?', 'error');
      console.error('Import failure:', err);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Upload and Import CSV';
      }
    }
  },

  async downloadCsvExport() {
    try {
      // Use raw fetch so we can get the raw CSV text with proper auth header
      const token = Api.getToken();
      const response = await fetch(`${window.location.origin}/api/data/export/csv`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        Api.showToast(data.detail || 'Export failed.', 'error');
        return;
      }

      const csvText = await response.text();
      const blob = new Blob([csvText], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.setAttribute('href', url);
      link.setAttribute('download', `student_learning_assessments_${new Date().toISOString().slice(0, 10)}.csv`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      Api.showToast('CSV export downloaded successfully.', 'success');
    } catch (err) {
      Api.showToast('Network error during export. Is the server running?', 'error');
      console.error('Export failure:', err);
    }
  }
};
