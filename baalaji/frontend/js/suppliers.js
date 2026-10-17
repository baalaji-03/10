/**
 * Suppliers Management Controller
 */

const Suppliers = {
  currentSuppliers: [],

  init() {
    const addForm = document.getElementById("form-add-supplier");
    if (addForm) {
      addForm.addEventListener("submit", (e) => this.handleAddSupplier(e));
    }

    const payForm = document.getElementById("form-supplier-payment");
    if (payForm) {
      payForm.addEventListener("submit", (e) => this.handleRecordPayment(e));
    }
  },

  async load() {
    try {
      const list = await API.get("/api/suppliers");
      this.currentSuppliers = list;
      this.renderTable(list);
    } catch (err) {
      App.showToast("Failed to load suppliers: " + err.message, "error");
    }
  },

  renderTable(list) {
    const tbody = document.getElementById("suppliers-table-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:30px; color:#94a3b8;">No suppliers added yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(s => `
      <tr>
        <td><b>${s.supplier_code || ''}</b></td>
        <td>
          <div style="font-weight:600; color:#0f172a;">${s.name}</div>
          <div style="font-size:11.5px; color:#64748b;">Contact: ${s.contact_person || 'N/A'}</div>
        </td>
        <td>${s.phone}</td>
        <td><b>${s.gstin || 'URP'}</b></td>
        <td>${s.city || ''}, ${s.state || ''}</td>
        <td>
          <b style="color:${s.outstanding_balance > 0 ? '#ef4444' : '#10b981'}; font-size:14px;">
            ₹ ${Number(s.outstanding_balance || 0).toFixed(2)}
          </b>
        </td>
        <td>
          <div style="display:flex; gap:6px;">
            <button class="btn btn-primary btn-sm" onclick="Suppliers.openPaymentModal(${s.id})">Pay</button>
            <button class="btn btn-secondary btn-sm" onclick="Suppliers.viewLedger(${s.id})">Ledger</button>
          </div>
        </td>
      </tr>
    `).join("");
  },

  openAddSupplierModal() {
    const form = document.getElementById("form-add-supplier");
    if (form) form.reset();
    document.getElementById("modal-add-supplier").classList.add("active");
  },

  async handleAddSupplier(e) {
    e.preventDefault();
    const name = document.getElementById("sup-name").value.trim();
    const contact = document.getElementById("sup-contact").value.trim();
    const phone = document.getElementById("sup-phone").value.trim();
    const email = document.getElementById("sup-email").value.trim();
    const gstin = document.getElementById("sup-gstin").value.trim();
    const dl = document.getElementById("sup-dl").value.trim();
    const address = document.getElementById("sup-address").value.trim();
    const city = document.getElementById("sup-city").value.trim();
    const state = document.getElementById("sup-state").value.trim();
    const balance = parseFloat(document.getElementById("sup-opening-bal").value) || 0;

    const payload = {
      name,
      contact_person: contact,
      phone,
      email,
      gstin,
      dl_number: dl,
      address,
      city,
      state,
      opening_balance: balance
    };

    try {
      await API.post("/api/suppliers", payload);
      App.showToast(`Supplier "${name}" registered!`, "success");
      document.getElementById("modal-add-supplier").classList.remove("active");
      this.load();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  openPaymentModal(supplierId) {
    const sup = this.currentSuppliers.find(s => s.id === supplierId);
    if (!sup) return;

    document.getElementById("pay-supplier-id").value = supplierId;
    document.getElementById("pay-supplier-name").textContent = sup.name;
    document.getElementById("pay-supplier-balance").textContent = `₹ ${Number(sup.outstanding_balance).toFixed(2)}`;
    document.getElementById("pay-amount-input").value = sup.outstanding_balance > 0 ? sup.outstanding_balance : "";

    document.getElementById("modal-supplier-payment").classList.add("active");
  },

  async handleRecordPayment(e) {
    e.preventDefault();
    const supplierId = parseInt(document.getElementById("pay-supplier-id").value, 10);
    const amount = parseFloat(document.getElementById("pay-amount-input").value);
    const method = document.getElementById("pay-method-select").value;
    const ref = document.getElementById("pay-reference-input").value.trim();
    const notes = document.getElementById("pay-notes-input").value.trim();

    if (!amount || amount <= 0) {
      App.showToast("Please enter a valid payment amount.", "warning");
      return;
    }

    const payload = {
      supplier_id: supplierId,
      amount,
      payment_method: method,
      reference_number: ref,
      notes
    };

    try {
      const res = await API.post("/api/suppliers/payments", payload);
      App.showToast(`Payment of ₹${amount.toFixed(2)} recorded! Remaining balance: ₹${res.remaining_supplier_balance.toFixed(2)}`, "success");
      document.getElementById("modal-supplier-payment").classList.remove("active");
      this.load();
      Dashboard.load();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async viewLedger(supplierId) {
    try {
      const data = await API.get(`/api/suppliers/${supplierId}/ledger`);
      const modal = document.getElementById("modal-supplier-ledger");
      document.getElementById("ledger-supplier-title").textContent = `Ledger: ${data.supplier.name}`;
      document.getElementById("ledger-outstanding").textContent = `₹ ${Number(data.supplier.outstanding_balance).toFixed(2)}`;

      const pTbody = document.getElementById("ledger-purchases-tbody");
      pTbody.innerHTML = data.purchases.length === 0 
        ? `<tr><td colspan="5" style="text-align:center; color:#94a3b8;">No purchases recorded</td></tr>`
        : data.purchases.map(p => `
          <tr>
            <td><b>${p.purchase_number}</b></td>
            <td>${p.supplier_invoice_number}</td>
            <td>${p.invoice_date}</td>
            <td><b>₹ ${p.total_amount.toFixed(2)}</b></td>
            <td><span class="badge ${p.payment_status === 'PAID' ? 'badge-green' : 'badge-orange'}">${p.payment_status}</span></td>
          </tr>
        `).join("");

      const payTbody = document.getElementById("ledger-payments-tbody");
      payTbody.innerHTML = data.payments.length === 0
        ? `<tr><td colspan="4" style="text-align:center; color:#94a3b8;">No payments recorded</td></tr>`
        : data.payments.map(py => `
          <tr>
            <td><b>${py.payment_number}</b></td>
            <td>${py.payment_date}</td>
            <td>${py.payment_method} (${py.reference_number || 'Direct'})</td>
            <td><b style="color:#10b981;">₹ ${py.amount.toFixed(2)}</b></td>
          </tr>
        `).join("");

      modal.classList.add("active");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  }
};
