/**
 * api.js — Centralized API Communication Service
 * Handles base URL, JWT token injection, response parsing, and error toasts.
 */

const API_BASE = window.location.origin.includes(':8000') 
  ? window.location.origin 
  : 'http://127.0.0.1:8000';

const Api = {
  getToken() {
    return localStorage.getItem('slpa_token') || '';
  },

  setSession(token, user) {
    localStorage.setItem('slpa_token', token);
    localStorage.setItem('slpa_user', JSON.stringify(user));
  },

  getUser() {
    try {
      return JSON.parse(localStorage.getItem('slpa_user') || 'null');
    } catch {
      return null;
    }
  },

  clearSession() {
    localStorage.removeItem('slpa_token');
    localStorage.removeItem('slpa_user');
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = options.headers || {};

    const token = this.getToken();
    if (token && !headers['Authorization']) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    if (!(options.body instanceof FormData) && !headers['Content-Type']) {
      headers['Content-Type'] = 'application/json';
    }

    options.headers = headers;

    try {
      const response = await fetch(url, options);

      if (response.status === 401) {
        this.clearSession();
        if (!window.location.pathname.includes('login.html')) {
          window.location.href = '/static/login.html';
        }
        throw new Error('Session expired. Please log in again.');
      }

      if (response.headers.get('content-type')?.includes('text/csv')) {
        return await response.text();
      }

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.detail || 'An unexpected error occurred.';
        this.showToast(errorMsg, 'error');
        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(`API Error [${options.method || 'GET'} ${endpoint}]:`, err);
      throw err;
    }
  },

  get(endpoint, params = null) {
    let url = endpoint;
    if (params) {
      const query = new URLSearchParams(params).toString();
      url = `${endpoint}?${query}`;
    }
    return this.request(url, { method: 'GET' });
  },

  post(endpoint, body) {
    const isForm = body instanceof FormData;
    return this.request(endpoint, {
      method: 'POST',
      body: isForm ? body : JSON.stringify(body),
    });
  },

  put(endpoint, body) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  },

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  },

  showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    const icon = type === 'error' ? '' : (type === 'success' ? '' : 'ℹ');
    toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

    container.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.3s ease';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }
};
