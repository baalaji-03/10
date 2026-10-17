/**
 * Authentication & Role-Based Access Control Module
 */

const Auth = {
  init() {
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => this.handleLogin(e));
    }

    const logoutBtn = document.getElementById("btn-logout");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => this.handleLogout());
    }
  },

  checkAuth() {
    const token = API.getToken();
    const user = API.getUser();
    if (!token || !user) {
      App.showLogin();
      return false;
    }
    this.updateUserUI(user);
    this.applyRolePermissions(user.role);
    return true;
  },

  async handleLogin(e) {
    e.preventDefault();
    const usernameInput = document.getElementById("login-username");
    const passwordInput = document.getElementById("login-password");
    const loginBtn = document.getElementById("btn-login-submit");

    const username = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!username || !password) {
      App.showToast("Please enter both username and password", "error");
      return;
    }

    try {
      loginBtn.disabled = true;
      loginBtn.textContent = "Logging in...";

      const formData = new URLSearchParams();
      formData.append("username", username);
      formData.append("password", password);

      const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: formData
      });

      const responseText = await res.text();
      let data = null;
      try {
        data = responseText ? JSON.parse(responseText) : null;
      } catch {
        // Vercel and other proxies may return plain-text errors instead of JSON.
      }

      if (!res.ok) {
        const detail = data?.detail || responseText.trim();
        throw new Error(detail || `Login request failed (HTTP ${res.status})`);
      }

      if (!data || typeof data.access_token !== "string" || !data.access_token) {
        throw new Error(`The login service returned an invalid response (HTTP ${res.status}).`);
      }

      API.setToken(data.access_token);
      API.setUser({
        id: data.user_id,
        username: data.username,
        full_name: data.full_name,
        role: data.role
      });

      App.showToast(`Welcome back, ${data.full_name}!`, "success");
      loginInputReset();
      App.showApp();
      this.updateUserUI(data);
      this.applyRolePermissions(data.role);
      Dashboard.load();
    } catch (err) {
      const msg = (err.name === "TypeError" && err.message === "Failed to fetch")
        ? "Unable to connect to backend server. Check your network or verify the backend service status."
        : (err.message || "Login failed");
      App.showToast(msg, "error");
    } finally {
      loginBtn.disabled = false;
      loginBtn.textContent = "Sign In to Dashboard";
    }

    function loginInputReset() {
      usernameInput.value = "";
      passwordInput.value = "";
    }
  },

  handleLogout() {
    API.clearToken();
    App.showToast("Logged out successfully", "info");
    App.showLogin();
  },

  updateUserUI(user) {
    const nameEl = document.getElementById("current-user-name");
    const roleEl = document.getElementById("current-user-role");
    const avatarEl = document.getElementById("current-user-avatar");

    if (nameEl) nameEl.textContent = user.full_name || user.username;
    if (roleEl) roleEl.textContent = user.role;
    if (avatarEl) {
      const initial = (user.full_name || user.username || "U")[0].toUpperCase();
      avatarEl.textContent = initial;
    }
  },

  applyRolePermissions(role) {
    // Role-based visibility
    const adminElements = document.querySelectorAll("[data-role-required='Admin']");
    const pharmaElements = document.querySelectorAll("[data-role-required='Pharmacist']");

    if (role === "Admin") {
      adminElements.forEach(el => el.style.display = "");
      pharmaElements.forEach(el => el.style.display = "");
    } else if (role === "Pharmacist") {
      adminElements.forEach(el => el.style.display = "none");
      pharmaElements.forEach(el => el.style.display = "");
    } else if (role === "Cashier") {
      // Cashier only sees POS Billing & Customers
      adminElements.forEach(el => el.style.display = "none");
      pharmaElements.forEach(el => el.style.display = "none");
    } else if (role === "Inventory Staff") {
      adminElements.forEach(el => el.style.display = "none");
    }
  }
};
