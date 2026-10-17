/**
 * Baalaji Pharmacy Management System - Main Application Controller
 */

const App = {
  currentView: "dashboard",
  excelPreviewData: null,

  init() {
    // 1. Initialize API and Auth
    Auth.init();
    POS.init();
    Medicines.init();
    Purchases.init();
    Suppliers.init();
    Customers.init();
    Alerts.init();
    Reports.init();
    Invoices.init();
    Returns.init();
    Settings.init();

    // 2. Setup Navigation
    this.setupNavigation();

    // 3. Setup Modal Close Listeners
    this.setupModals();

    // 4. Setup Excel Import Listeners
    this.setupExcelImport();

    // 5. Check Auth State
    if (Auth.checkAuth()) {
      this.showApp();
      this.navigateTo("dashboard");
    } else {
      this.showLogin();
    }
  },

  showLogin() {
    document.getElementById("login-screen").style.display = "flex";
    document.getElementById("app-container").style.display = "none";
  },

  showApp() {
    document.getElementById("login-screen").style.display = "none";
    document.getElementById("app-container").style.display = "flex";
  },

  setupNavigation() {
    const navItems = document.querySelectorAll(".sidebar-nav .nav-item");
    navItems.forEach(item => {
      item.addEventListener("click", () => {
        const view = item.dataset.view;
        if (view) {
          this.navigateTo(view);
        }
      });
    });
  },

  navigateTo(viewName) {
    this.currentView = viewName;

    // Update nav item active state
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
      if (item.dataset.view === viewName) {
        item.classList.add("active");
      } else {
        item.classList.remove("active");
      }
    });

    // Update view panels
    document.querySelectorAll(".view-section").forEach(sec => {
      sec.classList.remove("active");
    });

    const targetSec = document.getElementById(`view-${viewName}`);
    if (targetSec) {
      targetSec.classList.add("active");
    }

    // Update Header Title
    const titles = {
      dashboard: { title: "Dashboard Overview", subtitle: "Real-time pharmacy analytics, sales, stock & alerts" },
      pos: { title: "Point of Sale (POS) Billing", subtitle: "Fast GST Billing, barcode search, batch selection & instant receipt printing" },
      medicines: { title: "Medicine Catalog & Batches", subtitle: "Medicine registration, batch tracking, rack locations & stock monitoring" },
      purchases: { title: "Purchase Entry & Stock-In", subtitle: "Supplier invoice entry, multi-item batch registration & GST credit" },
      suppliers: { title: "Supplier Directory & Ledger", subtitle: "Manage distributors, track payments, and audit outstanding balances" },
      customers: { title: "Customer Records & History", subtitle: "Customer directory, prescription details, and purchase history" },
      alerts: { title: "Expiry & Low-Stock Alerts", subtitle: "Automated 6-month expiry radar, expired stock quarantine & reorder alarms" },
      reports: { title: "Financial & GST Reports", subtitle: "Profit & loss, revenue, COGS, GSTR-1 summaries, and tax breakdown" },
      returns: { title: "Sales & Purchase Returns", subtitle: "Customer bill returns, credit notes, and supplier batch returns" },
      settings: { title: "Pharmacy Settings & System", subtitle: "Clinic profile, drug licenses, GSTIN, SMTP email configuration & users" }
    };

    const headerTitle = document.getElementById("header-title");
    const headerSubtitle = document.getElementById("header-subtitle");
    if (headerTitle && titles[viewName]) {
      headerTitle.textContent = titles[viewName].title;
      headerSubtitle.textContent = titles[viewName].subtitle;
    }

    // Trigger module loaders
    switch (viewName) {
      case "dashboard":
        Dashboard.load();
        break;
      case "pos":
        document.getElementById("pos-barcode-input")?.focus();
        break;
      case "medicines":
        Medicines.load();
        break;
      case "purchases":
        Purchases.load();
        break;
      case "suppliers":
        Suppliers.load();
        break;
      case "customers":
        Customers.load();
        break;
      case "alerts":
        Alerts.load();
        break;
      case "reports":
        Reports.load();
        break;
      case "settings":
        Settings.load();
        break;
    }
  },

  setupModals() {
    // Close modal on click of close button or outside backdrop
    document.querySelectorAll(".modal-overlay").forEach(overlay => {
      overlay.addEventListener("click", (e) => {
        if (e.target === overlay) {
          overlay.classList.remove("active");
        }
      });
    });

    document.querySelectorAll(".modal-close, .btn-modal-cancel").forEach(btn => {
      btn.addEventListener("click", () => {
        const modal = btn.closest(".modal-overlay");
        if (modal) modal.classList.remove("active");
      });
    });
  },

  setupExcelImport() {
    const dropZone = document.getElementById("excel-drop-zone");
    const fileInput = document.getElementById("excel-file-input");

    if (dropZone && fileInput) {
      dropZone.addEventListener("click", () => fileInput.click());

      fileInput.addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (file) {
          await this.processExcelUpload(file);
        }
      });

      // Drag and drop
      dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#0f766e";
        dropZone.style.background = "#f0fdfa";
      });

      dropZone.addEventListener("dragleave", () => {
        dropZone.style.borderColor = "#cbd5e1";
        dropZone.style.background = "#f8fafc";
      });

      dropZone.addEventListener("drop", async (e) => {
        e.preventDefault();
        dropZone.style.borderColor = "#cbd5e1";
        dropZone.style.background = "#f8fafc";
        if (e.dataTransfer.files.length > 0) {
          await this.processExcelUpload(e.dataTransfer.files[0]);
        }
      });
    }

    const btnConfirmImport = document.getElementById("btn-confirm-excel-import");
    if (btnConfirmImport) {
      btnConfirmImport.addEventListener("click", () => this.confirmExcelImport());
    }
  },

  openExcelImportModal() {
    this.excelPreviewData = null;
    document.getElementById("excel-preview-container").style.display = "none";
    document.getElementById("btn-confirm-excel-import").style.display = "none";
    document.getElementById("excel-file-input").value = "";
    document.getElementById("modal-excel-import").classList.add("active");
  },

  async processExcelUpload(file) {
    if (!file.name.endsWith(".xlsx") && !file.name.endsWith(".xls")) {
      this.showToast("Please select a valid Excel (.xlsx) file.", "error");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    try {
      this.showToast("Parsing and validating Excel file...", "info");
      const preview = await API.post("/api/excel/upload/medicines/preview", formData);

      this.excelPreviewData = preview.all_data;
      const previewContainer = document.getElementById("excel-preview-container");
      const summaryText = document.getElementById("excel-preview-summary");
      const tbody = document.getElementById("excel-preview-tbody");
      const confirmBtn = document.getElementById("btn-confirm-excel-import");

      summaryText.textContent = `Detected ${preview.total_rows} valid records in file. Please verify preview before saving.`;

      tbody.innerHTML = preview.preview.map(row => `
        <tr>
          <td>${row.item_code || 'Auto'}</td>
          <td><b>${row.name}</b></td>
          <td>${row.generic_name || '-'}</td>
          <td>${row.category}</td>
          <td>${row.hsn_code} (${row.gst_rate}%)</td>
          <td>${row.min_stock_level}</td>
          <td>₹ ${row.default_purchase_price.toFixed(2)}</td>
          <td>₹ ${row.default_selling_price.toFixed(2)}</td>
        </tr>
      `).join("");

      previewContainer.style.display = "block";
      confirmBtn.style.display = "inline-flex";
      this.showToast(`Preview loaded! ${preview.total_rows} rows found.`, "success");
    } catch (err) {
      this.showToast("Excel Parsing Error: " + err.message, "error");
    }
  },

  async confirmExcelImport() {
    if (!this.excelPreviewData || this.excelPreviewData.length === 0) {
      this.showToast("No data to import.", "warning");
      return;
    }

    try {
      const btn = document.getElementById("btn-confirm-excel-import");
      btn.disabled = true;
      btn.textContent = "Saving to Database...";

      const res = await API.post("/api/excel/upload/medicines/confirm", this.excelPreviewData);
      this.showToast(res.message, "success");

      document.getElementById("modal-excel-import").classList.remove("active");
      Medicines.load();
      Dashboard.load();
    } catch (err) {
      this.showToast("Import failed: " + err.message, "error");
    } finally {
      const btn = document.getElementById("btn-confirm-excel-import");
      btn.disabled = false;
      btn.textContent = "Confirm & Save into Database";
    }
  },

  showToast(message, type = "info") {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerHTML = `
      <span>${message}</span>
      <span style="cursor:pointer; margin-left:8px;" onclick="this.parentElement.remove()">&times;</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateX(100%)";
      toast.style.transition = "all 0.3s ease";
      setTimeout(() => toast.remove(), 300);
    }, 4500);
  }
};

// Initialize when DOM is ready
window.addEventListener("DOMContentLoaded", () => {
  App.init();
});
