/**
 * auth.js — Authentication State & Navigation Guard
 */

const Auth = {
  checkAuth(allowedRoles = []) {
    const token = Api.getToken();
    const user = Api.getUser();

    if (!token || !user) {
      Api.clearSession();
      if (!window.location.pathname.endsWith('login.html')) {
        window.location.href = '/static/login.html';
      }
      return null;
    }

    if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
      alert(`Access Restricted. This view requires one of the following roles: ${allowedRoles.join(', ')}.`);
      this.redirectToDashboard(user.role);
      return null;
    }

    this.renderUserBadge(user);
    return user;
  },

  redirectToDashboard(role) {
    if (role === 'administrator') {
      window.location.href = '/static/dashboards/admin.html';
    } else if (role === 'teacher') {
      window.location.href = '/static/dashboards/teacher.html';
    } else if (role === 'student') {
      window.location.href = '/static/dashboards/student.html';
    } else {
      window.location.href = '/static/login.html';
    }
  },

  renderUserBadge(user) {
    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-role-label');
    const avatarEl = document.getElementById('user-avatar');

    if (nameEl) nameEl.textContent = user.display_name || user.username;
    if (roleEl) roleEl.textContent = user.role.toUpperCase();
    if (avatarEl) {
      avatarEl.textContent = (user.display_name || user.username).charAt(0).toUpperCase();
    }
  },

  logout() {
    Api.clearSession();
    window.location.href = '/static/login.html';
  }
};
