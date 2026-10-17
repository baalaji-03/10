/**
 * Purchase Entry & Stock In Controller
 */

const Purchases = {
  purchaseItems: [],
  suppliersList: [],
  currentPurchaseId: null,

  init() {
    const btnAddRow = document.getElementById("btn-add-purchase-row");
    if (btnAddRow) {
      btnAddRow.addEventListener("click", () => this.addItemRow());
    }

    const form = document.getElementById("form-purchase-entry");
    if (form) {
      form.addEventListener("submit", (e) => this.handleSavePurchase(e));
    }

    const uploadBillButton = document.getElementById("btn-upload-purchase-bill");
    if (uploadBillButton) {
      uploadBillButton.addEventListener("click", () => this.uploadBillFromDetails());
    }

    const downloadBillButton = document.getElementById("btn-download-purchase-bill");
    if (downloadBillButton) {
      downloadBillButton.addEventListener("click", () => this.downloadBill());
    }
  },

  async load() {
    await this.loadSuppliers();
    this.resetForm();
    this.loadHistory();
  },

  async loadSuppliers() {
    try {
      const list = await API.get("/api/suppliers");
      this.suppliersList = list;
      const select = document.getElementById("purchase-supplier-select");
      if (select) {
        select.innerHTML = `<option value="">-- Choose Supplier --</option>` + 
          list.map(s => `<option value="${s.id}">${s.name} (GSTIN: ${s.gstin || 'URP'})</option>`).join("");
      }
    } catch (err) {
      console.error(err);
    }
  },

  resetForm() {
    const form = document.getElementById("form-purchase-entry");
    if (form) form.reset();
    
    // Set default today dates
    const todayStr = new Date().toISOString().split("T")[0];
    const invDateInput = document.getElementById("purchase-invoice-date");
    const recDateInput = document.getElementById("purchase-received-date");
    if (invDateInput) invDateInput.value = todayStr;
    if (recDateInput) recDateInput.value = todayStr;

    // Reset items
    this.purchaseItems = [];
    const tbody = document.getElementById("purchase-items-tbody");
    if (tbody) tbody.innerHTML = "";
    this.addItemRow(); // Start with 1 blank row
    this.recalculateTotals();
  },

  addItemRow() {
    const tbody = document.getElementById("purchase-items-tbody");
    if (!tbody) return;

    const rowId = Date.now() + Math.random().toString(36).substr(2, 5);
    const row = document.createElement("tr");
    row.id = `pur-row-${rowId}`;

    row.innerHTML = `
      <td>
        <input type="text" placeholder="Medicine Name" class="pur-med-name" required 
          style="width:100%; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="text" placeholder="Batch No" class="pur-batch" required 
          style="width:90px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="date" class="pur-expiry" required 
          style="width:130px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="number" min="1" value="10" class="pur-qty" required 
          oninput="Purchases.recalculateTotals()" 
          style="width:65px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="number" min="0" value="0" class="pur-free" 
          style="width:55px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="number" step="0.01" min="0" placeholder="0.00" class="pur-rate" required 
          oninput="Purchases.recalculateTotals()" 
          style="width:75px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="number" step="0.01" min="0" placeholder="0.00" class="pur-mrp" required 
          style="width:75px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <input type="number" step="0.1" min="0" max="100" value="0" class="pur-disc" 
          oninput="Purchases.recalculateTotals()" 
          style="width:55px; padding:6px; border:1px solid #cbd5e1; border-radius:4px;" />
      </td>
      <td>
        <select class="pur-gst" onchange="Purchases.recalculateTotals()" style="padding:6px; border:1px solid #cbd5e1; border-radius:4px;">
          <option value="12">12%</option>
          <option value="5">5%</option>
          <option value="18">18%</option>
          <option value="0">0%</option>
        </select>
      </td>
      <td class="pur-row-total" style="font-weight:700; color:#0f766e; text-align:right;">
        ₹ 0.00
      </td>
      <td>
        <button type="button" onclick="Purchases.removeRow('${rowId}')" 
          style="background:none; border:none; color:#ef4444; font-size:16px; cursor:pointer;">&times;</button>
      </td>
    `;

    tbody.appendChild(row);
  },

  removeRow(rowId) {
    const row = document.getElementById(`pur-row-${rowId}`);
    if (row) {
      row.remove();
      this.recalculateTotals();
    }
  },

  recalculateTotals() {
    const tbody = document.getElementById("purchase-items-tbody");
    if (!tbody) return;

    const rows = tbody.querySelectorAll("tr");
    let subtotal = 0;
    let totalTax = 0;
    let totalDiscount = 0;

    rows.forEach(r => {
      const qty = parseFloat(r.querySelector(".pur-qty")?.value) || 0;
      const rate = parseFloat(r.querySelector(".pur-rate")?.value) || 0;
      const discPercent = parseFloat(r.querySelector(".pur-disc")?.value) || 0;
      const gstPercent = parseFloat(r.querySelector(".pur-gst")?.value) || 12;

      const gross = qty * rate;
      const disc = gross * (discPercent / 100);
      const taxable = gross - disc;
      const tax = taxable * (gstPercent / 100);
      const rowTotal = taxable + tax;

      subtotal += gross;
      totalDiscount += disc;
      totalTax += tax;

      const totalCell = r.querySelector(".pur-row-total");
      if (totalCell) totalCell.textContent = `₹ ${rowTotal.toFixed(2)}`;
    });

    const addCharges = parseFloat(document.getElementById("purchase-additional-charges")?.value) || 0;
    const net = Math.round(subtotal - totalDiscount + totalTax + addCharges);

    document.getElementById("pur-calc-subtotal").textContent = `₹ ${subtotal.toFixed(2)}`;
    document.getElementById("pur-calc-discount").textContent = `- ₹ ${totalDiscount.toFixed(2)}`;
    document.getElementById("pur-calc-tax").textContent = `₹ ${totalTax.toFixed(2)}`;
    document.getElementById("pur-calc-total").textContent = `₹ ${net.toFixed(2)}`;
  },

  async handleSavePurchase(e) {
    e.preventDefault();
    const supplierId = parseInt(document.getElementById("purchase-supplier-select").value, 10);
    const invoiceNum = document.getElementById("purchase-invoice-number").value.trim();
    const invoiceDate = document.getElementById("purchase-invoice-date").value;
    const receivedDate = document.getElementById("purchase-received-date").value;
    const addCharges = parseFloat(document.getElementById("purchase-additional-charges").value) || 0;
    const paidAmount = parseFloat(document.getElementById("purchase-paid-amount").value) || 0;
    const notes = document.getElementById("purchase-notes").value.trim();
    const billFile = document.getElementById("purchase-bill-file").files[0];

    if (!supplierId) {
      App.showToast("Please choose a supplier.", "warning");
      return;
    }
    if (!invoiceNum) {
      App.showToast("Please enter supplier invoice number.", "warning");
      return;
    }

    const tbody = document.getElementById("purchase-items-tbody");
    const rows = tbody.querySelectorAll("tr");
    if (rows.length === 0) {
      App.showToast("Please add at least one medicine item.", "warning");
      return;
    }

    const items = [];
    for (const r of rows) {
      const name = r.querySelector(".pur-med-name").value.trim();
      const batch = r.querySelector(".pur-batch").value.trim();
      const expiry = r.querySelector(".pur-expiry").value;
      const qty = parseInt(r.querySelector(".pur-qty").value, 10);
      const free = parseInt(r.querySelector(".pur-free").value, 10) || 0;
      const rate = parseFloat(r.querySelector(".pur-rate").value) || 0;
      const mrp = parseFloat(r.querySelector(".pur-mrp").value) || 0;
      const disc = parseFloat(r.querySelector(".pur-disc").value) || 0;
      const gst = parseFloat(r.querySelector(".pur-gst").value) || 12;

      if (!name || !batch || !expiry || qty <= 0 || rate <= 0) {
        App.showToast("Please complete all required fields for each medicine row.", "error");
        return;
      }

      items.push({
        medicine_name: name,
        batch_number: batch,
        expiry_date: expiry,
        quantity: qty,
        free_quantity: free,
        purchase_price: rate,
        mrp: mrp || rate * 1.3,
        selling_price: mrp || rate * 1.3,
        discount_percent: disc,
        gst_rate: gst
      });
    }

    const payload = {
      supplier_id: supplierId,
      supplier_invoice_number: invoiceNum,
      invoice_date: invoiceDate,
      received_date: receivedDate,
      additional_charges: addCharges,
      paid_amount: paidAmount,
      notes: notes,
      items: items
    };

    try {
      const res = await API.post("/api/purchases", payload);
      if (billFile) {
        try {
          await this.uploadBill(res.id, billFile);
          App.showToast(`Purchase ${res.purchase_number} saved and supplier bill attached.`, "success");
        } catch (err) {
          App.showToast(
            `Purchase ${res.purchase_number} was saved, but the supplier bill upload failed: ${err.message}. Open its Details to upload the bill.`,
            "error"
          );
        }
      } else {
        App.showToast(`Purchase ${res.purchase_number} saved and stock updated!`, "success");
      }
      this.resetForm();
      this.loadHistory();
      Dashboard.load();
    } catch (err) {
      App.showToast("Error saving purchase: " + err.message, "error");
    }
  },

  async loadHistory() {
    try {
      const list = await API.get("/api/purchases");
      const tbody = document.getElementById("purchase-history-tbody");
      if (!tbody) return;

      if (list.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94a3b8;">No purchase invoices recorded yet.</td></tr>`;
        return;
      }

      tbody.innerHTML = list.map(p => `
        <tr>
          <td><b>${p.purchase_number}</b></td>
          <td>${p.supplier_name}</td>
          <td><b>${p.supplier_invoice_number}</b></td>
          <td>${p.invoice_date}</td>
          <td><b>₹ ${p.total_amount.toFixed(2)}</b></td>
          <td>
            <span class="badge ${p.payment_status === 'PAID' ? 'badge-green' : (p.payment_status === 'PARTIAL' ? 'badge-orange' : 'badge-red')}">
              ${p.payment_status}
            </span>
          </td>
          <td>
            <button class="btn btn-secondary btn-sm" onclick="Purchases.viewDetail(${p.id})">Details</button>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      console.error(err);
    }
  },

  async viewDetail(id) {
    try {
      const p = await API.get(`/api/purchases/${id}`);
      this.currentPurchaseId = id;
      const modal = document.getElementById("modal-purchase-detail");
      document.getElementById("pur-detail-title").textContent = `Purchase Invoice: ${p.purchase_number}`;
      document.getElementById("pur-detail-supplier").textContent = `${p.supplier_name} (GSTIN: ${p.supplier_gstin || 'URP'})`;
      document.getElementById("pur-detail-inv-no").textContent = p.supplier_invoice_number;
      document.getElementById("pur-detail-date").textContent = p.invoice_date;
      document.getElementById("pur-detail-total").textContent = `₹ ${p.total_amount.toFixed(2)}`;

      const billStatus = document.getElementById("pur-detail-bill-status");
      const downloadBillButton = document.getElementById("btn-download-purchase-bill");
      billStatus.textContent = p.bill_filename || "No bill attached";
      downloadBillButton.style.display = p.bill_filename ? "" : "none";
      document.getElementById("pur-detail-bill-file").value = "";

      const tbody = document.getElementById("pur-detail-items-tbody");
      tbody.innerHTML = p.items.map(i => `
        <tr>
          <td><b>${i.medicine_name}</b></td>
          <td>${i.batch_number}</td>
          <td>${i.expiry_date}</td>
          <td>${i.quantity} (+${i.free_quantity} free)</td>
          <td>₹ ${i.purchase_price.toFixed(2)}</td>
          <td>₹ ${i.mrp.toFixed(2)}</td>
          <td>${i.gst_rate}%</td>
          <td><b>₹ ${i.total_amount.toFixed(2)}</b></td>
        </tr>
      `).join("");

      modal.classList.add("active");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async uploadBill(purchaseId, file) {
    const formData = new FormData();
    formData.append("file", file);
    return API.post(`/api/purchases/${purchaseId}/bill`, formData);
  },

  async uploadBillFromDetails() {
    const fileInput = document.getElementById("pur-detail-bill-file");
    const uploadButton = document.getElementById("btn-upload-purchase-bill");
    const file = fileInput.files[0];
    if (!this.currentPurchaseId || !file) {
      App.showToast("Choose a supplier bill file to upload.", "warning");
      return;
    }

    uploadButton.disabled = true;
    try {
      await this.uploadBill(this.currentPurchaseId, file);
      App.showToast("Supplier bill uploaded successfully.", "success");
      await this.viewDetail(this.currentPurchaseId);
      this.loadHistory();
    } catch (err) {
      App.showToast(`Supplier bill upload failed: ${err.message}`, "error");
    } finally {
      uploadButton.disabled = false;
    }
  },

  async downloadBill() {
    if (!this.currentPurchaseId) return;
    try {
      const purchase = await API.get(`/api/purchases/${this.currentPurchaseId}`);
      await API.download(
        `/api/purchases/${this.currentPurchaseId}/bill`,
        purchase.bill_filename || "supplier-bill"
      );
    } catch (err) {
      App.showToast(`Could not download supplier bill: ${err.message}`, "error");
    }
  }
};
