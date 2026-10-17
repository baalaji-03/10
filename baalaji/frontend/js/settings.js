/**
 * Settings, SMTP Configuration and User Management Controller
 */

const Settings = {
  init() {
    const profileForm = document.getElementById("form-pharmacy-settings");
    if (profileForm) {
      profileForm.addEventListener("submit", (e) => this.handleSaveSettings(e));
    }

    const testEmailBtn = document.getElementById("btn-test-smtp");
    if (testEmailBtn) {
      testEmailBtn.addEventListener("click", () => this.handleTestEmail());
    }

    const addUserForm = document.getElementById("form-add-user");
    if (addUserForm) {
      addUserForm.addEventListener("submit", (e) => this.handleAddUser(e));
    }
  },

  async load() {
    await this.loadPharmacySettings();
    if (API.getUser()?.role === "Admin") {
      this.loadUsers();
      this.loadAuditLogs();
    }
  },

  async loadPharmacySettings() {
    try {
      const s = await API.get("/api/settings");
      document.getElementById("set-pharmacy-name").value = s.pharmacy_name || "";
      document.getElementById("set-tagline").value = s.tagline || "";
      document.getElementById("set-addr1").value = s.address_line1 || "";
      document.getElementById("set-addr2").value = s.address_line2 || "";
      document.getElementById("set-city").value = s.city || "";
      document.getElementById("set-state").value = s.state || "";
      document.getElementById("set-pincode").value = s.postal_code || "";
      document.getElementById("set-phone").value = s.phone || "";
      document.getElementById("set-email").value = s.email || "";
      document.getElementById("set-gstin").value = s.gstin || "";
      document.getElementById("set-dl").value = s.dl_number || "";
      document.getElementById("set-pan").value = s.pan_number || "";
      document.getElementById("set-prefix").value = s.invoice_prefix || "INV";
      document.getElementById("set-declaration").value = s.invoice_declaration || "";
      document.getElementById("set-expiry-months").value = s.expiry_warning_months || 6;
      document.getElementById("set-reorder-mult").value = s.default_reorder_multiplier || 2.0;

      // SMTP Settings
      document.getElementById("set-smtp-host").value = s.smtp_host || "";
      document.getElementById("set-smtp-port").value = s.smtp_port || 587;
      document.getElementById("set-smtp-user").value = s.smtp_user || "";
      document.getElementById("set-smtp-from").value = s.smtp_from_email || "";
      document.getElementById("set-alert-recipient").value = s.alert_email_recipient || "";
      document.getElementById("set-smtp-tls").checked = s.smtp_use_tls !== false;
    } catch (err) {
      console.error("Failed to load settings:", err);
    }
  },

  async handleSaveSettings(e) {
    e.preventDefault();
    const payload = {
      pharmacy_name: document.getElementById("set-pharmacy-name").value.trim(),
      tagline: document.getElementById("set-tagline").value.trim(),
      address_line1: document.getElementById("set-addr1").value.trim(),
      address_line2: document.getElementById("set-addr2").value.trim(),
      city: document.getElementById("set-city").value.trim(),
      state: document.getElementById("set-state").value.trim(),
      postal_code: document.getElementById("set-pincode").value.trim(),
      phone: document.getElementById("set-phone").value.trim(),
      email: document.getElementById("set-email").value.trim(),
      gstin: document.getElementById("set-gstin").value.trim(),
      dl_number: document.getElementById("set-dl").value.trim(),
      pan_number: document.getElementById("set-pan").value.trim(),
      invoice_prefix: document.getElementById("set-prefix").value.trim(),
      invoice_declaration: document.getElementById("set-declaration").value.trim(),
      expiry_warning_months: parseInt(document.getElementById("set-expiry-months").value, 10) || 6,
      default_reorder_multiplier: parseFloat(document.getElementById("set-reorder-mult").value) || 2.0,
      smtp_host: document.getElementById("set-smtp-host").value.trim(),
      smtp_port: parseInt(document.getElementById("set-smtp-port").value, 10) || 587,
      smtp_user: document.getElementById("set-smtp-user").value.trim(),
      smtp_password: document.getElementById("set-smtp-pass").value,
      smtp_use_tls: document.getElementById("set-smtp-tls").checked,
      smtp_from_email: document.getElementById("set-smtp-from").value.trim(),
      alert_email_recipient: document.getElementById("set-alert-recipient").value.trim()
    };

    try {
      await API.put("/api/settings", payload);
      App.showToast("Pharmacy profile and SMTP configuration saved!", "success");
      Dashboard.load();
    } catch (err) {
      App.showToast("Failed to save settings: " + err.message, "error");
    }
  },

  async handleTestEmail() {
    const recipient = document.getElementById("set-alert-recipient")?.value.trim() || document.getElementById("set-smtp-user")?.value.trim();
    if (!recipient) {
      App.showToast("Please enter an Alert Email Recipient first.", "warning");
      return;
    }

    try {
      App.showToast(`Sending test message to ${recipient}...`, "info");
      const res = await API.post("/api/settings/test-email", { test_recipient: recipient });
      App.showToast(res.message || "Test email dispatched successfully!", "success");
    } catch (err) {
      App.showToast("SMTP Test Failed: " + err.message, "error");
    }
  },

  async loadUsers() {
    try {
      const users = await API.get("/api/auth/users");
      const tbody = document.getElementById("users-table-tbody");
      if (!tbody) return;

      tbody.innerHTML = users.map(u => `
        <tr>
          <td><b>${u.username}</b></td>
          <td>${u.full_name}</td>
          <td>${u.email}</td>
          <td><span class="badge badge-blue">${u.role}</span></td>
          <td>
            <span class="badge ${u.is_active ? 'badge-green' : 'badge-red'}">
              ${u.is_active ? 'Active' : 'Inactive'}
            </span>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
    }
  },

  openAddUserModal() {
    const form = document.getElementById("form-add-user");
    if (form) form.reset();
    document.getElementById("modal-add-user").classList.add("active");
  },

  async handleAddUser(e) {
    e.preventDefault();
    const username = document.getElementById("new-user-username").value.trim();
    const fullName = document.getElementById("new-user-fullname").value.trim();
    const email = document.getElementById("new-user-email").value.trim();
    const password = document.getElementById("new-user-password").value;
    const role = document.getElementById("new-user-role").value;

    const payload = {
      username,
      full_name: fullName,
      email,
      password,
      role,
      is_active: true
    };

    try {
      await API.post("/api/auth/users", payload);
      App.showToast(`User account "${username}" created!`, "success");
      document.getElementById("modal-add-user").classList.remove("active");
      this.loadUsers();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async loadAuditLogs() {
    try {
      const logs = await API.get("/api/settings/logs/audit");
      const tbody = document.getElementById("audit-logs-tbody");
      if (!tbody) return;

      tbody.innerHTML = logs.map(l => `
        <tr>
          <td>${l.created_at ? l.created_at.replace("T", " ").slice(0, 19) : ""}</td>
          <td><b>${l.username || 'System'}</b></td>
          <td><span class="badge badge-blue">${l.module}</span></td>
          <td><b>${l.action}</b></td>
          <td>${l.details || ''}</td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
    }
  }
};
