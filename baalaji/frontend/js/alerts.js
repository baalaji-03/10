/**
 * Expiry & Low-Stock Alerts Controller
 */

const Alerts = {
  currentExpiryAlerts: [],
  currentLowStockAlerts: [],

  init() {
    const btnExpExcel = document.getElementById("btn-export-expiry-excel");
    if (btnExpExcel) {
      btnExpExcel.addEventListener("click", () => API.download("/api/excel/export/batches", "Expiry_Alerts.xlsx"));
    }

    const btnLowStockExcel = document.getElementById("btn-export-lowstock-excel");
    if (btnLowStockExcel) {
      btnLowStockExcel.addEventListener("click", () => API.download("/api/excel/export/inventory", "Low_Stock_Report.xlsx"));
    }

    const btnSendExpiryEmail = document.getElementById("btn-email-expiry-alert");
    if (btnSendExpiryEmail) {
      btnSendExpiryEmail.addEventListener("click", () => this.sendEmailAlert("expiry"));
    }

    const btnSendLowStockEmail = document.getElementById("btn-email-lowstock-alert");
    if (btnSendLowStockEmail) {
      btnSendLowStockEmail.addEventListener("click", () => this.sendEmailAlert("low-stock"));
    }
  },

  async load() {
    await Promise.all([this.loadExpiryAlerts(), this.loadLowStockAlerts()]);
  },

  async loadExpiryAlerts() {
    try {
      const list = await API.get("/api/alerts/expiry");
      this.currentExpiryAlerts = list;
      const tbody = document.getElementById("expiry-alerts-tbody");
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:30px; color:#10b981; font-weight:600;">All medicines are well within their validity period. No near-expiry or expired stock.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map(a => {
        const isExpired = a.status_level === "RED";
        const badge = isExpired
          ? `<span class="badge badge-red">EXPIRED (${Math.abs(a.days_remaining)} days ago)</span>`
          : `<span class="badge badge-orange">NEAR EXPIRY (${a.days_remaining} days left)</span>`;

        return `
          <tr style="background:${isExpired ? '#fef2f2' : '#fffbeb'};">
            <td>
              <div style="font-weight:700; color:${isExpired ? '#991b1b' : '#92400e'};">${a.medicine_name}</div>
              <div style="font-size:11.5px; color:#64748b;">${a.generic_name || ''}</div>
            </td>
            <td><b>${a.batch_number}</b></td>
            <td><b>${a.expiry_date}</b></td>
            <td>${a.days_remaining > 0 ? a.days_remaining + ' days' : 'Expired'}</td>
            <td><b>${a.quantity} units</b></td>
            <td>₹ ${a.purchase_price.toFixed(2)}</td>
            <td><b>₹ ${a.stock_value.toFixed(2)}</b></td>
            <td>${badge}</td>
          </tr>
        `;
      }).join("");
    } catch (err) {
      App.showToast("Failed to load expiry alerts: " + err.message, "error");
    }
  },

  async loadLowStockAlerts() {
    try {
      const list = await API.get("/api/alerts/low-stock");
      this.currentLowStockAlerts = list;
      const tbody = document.getElementById("lowstock-alerts-tbody");
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#10b981; font-weight:600;">Inventory is healthy. No medicines currently below minimum threshold.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map(l => `
        <tr>
          <td>
            <div style="font-weight:700; color:#0f172a;">${l.medicine_name}</div>
            <div style="font-size:11.5px; color:#64748b;">${l.generic_name || ''} | Rack: ${l.rack_location || '-'}</div>
          </td>
          <td><b style="color:#ef4444; font-size:14px;">${l.current_stock}</b> ${l.unit}</td>
          <td>${l.min_stock_level} ${l.unit}</td>
          <td><b style="color:#0f766e; font-size:14px;">${l.suggested_reorder_qty} ${l.unit}</b></td>
          <td>₹ ${l.estimated_reorder_cost.toFixed(2)}</td>
          <td>
            <span class="badge badge-orange">Reorder Advised</span>
          </td>
          <td>
            <button class="btn btn-primary btn-sm" onclick="App.navigateTo('purchases');">Create PO</button>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      App.showToast("Failed to load low-stock alerts: " + err.message, "error");
    }
  },

  async sendEmailAlert(type) {
    try {
      App.showToast(`Dispatching ${type} email report with Excel attachment...`, "info");
      const res = await API.post(`/api/settings/send-alert-email/${type}`);
      App.showToast(res.message || "Email notification dispatched successfully!", "success");
    } catch (err) {
      App.showToast("Failed to send email alert: " + err.message, "error");
    }
  }
};
