/**
 * Medicines & Inventory Management Controller
 */

const Medicines = {
  currentMedicines: [],

  init() {
    const searchInput = document.getElementById("med-search-filter");
    if (searchInput) {
      let debounce = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(debounce);
        debounce = setTimeout(() => this.load(e.target.value.trim()), 250);
      });
    }

    const categoryFilter = document.getElementById("med-category-filter");
    if (categoryFilter) {
      categoryFilter.addEventListener("change", (e) => {
        this.load(document.getElementById("med-search-filter").value.trim(), e.target.value);
      });
    }

    const addForm = document.getElementById("form-add-medicine");
    if (addForm) {
      addForm.addEventListener("submit", (e) => this.handleAddMedicine(e));
    }

    const addBatchForm = document.getElementById("form-add-batch");
    if (addBatchForm) {
      addBatchForm.addEventListener("submit", (e) => this.handleAddBatch(e));
    }
  },

  async load(search = "", category = "") {
    try {
      let endpoint = `/api/medicines?`;
      if (search) endpoint += `search=${encodeURIComponent(search)}&`;
      if (category) endpoint += `category=${encodeURIComponent(category)}&`;

      const list = await API.get(endpoint);
      this.currentMedicines = list;
      this.renderTable(list);
    } catch (err) {
      App.showToast("Failed to load medicines: " + err.message, "error");
    }
  },

  renderTable(list) {
    const tbody = document.getElementById("medicines-table-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="9" style="text-align:center; padding:30px; color:#94a3b8;">No medicines registered yet. Click "Register New Medicine" to add.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(m => {
      const isLow = m.total_stock <= m.min_stock_level;
      const statusBadge = isLow 
        ? `<span class="badge badge-orange">Low Stock (${m.total_stock})</span>`
        : `<span class="badge badge-green">In Stock (${m.total_stock})</span>`;

      return `
        <tr>
          <td><b>${m.item_code || ''}</b></td>
          <td>
            <div style="font-weight:600; color:#0f172a;">${m.name}</div>
            <div style="font-size:11.5px; color:#64748b;">${m.generic_name || ''}</div>
          </td>
          <td>${m.category || 'Allopathy'}</td>
          <td>${m.rack_location || '-'}</td>
          <td><b>${m.hsn_code || '3004'}</b> (${m.gst_rate}%)</td>
          <td>${statusBadge}</td>
          <td>₹ ${Number(m.default_selling_price || 0).toFixed(2)}</td>
          <td>
            <span style="font-size:11.5px; color:#64748b;">${m.batches ? m.batches.length : 0} batch(es)</span>
          </td>
          <td>
            <div style="display:flex; gap:6px;">
              <button class="btn btn-secondary btn-sm" onclick="Medicines.openAddBatchModal(${m.id})">+ Batch</button>
              <button class="btn btn-secondary btn-sm" onclick="Medicines.viewBatchesDetail(${m.id})">Batches</button>
            </div>
          </td>
        </tr>
      `;
    }).join("");
  },

  openAddMedicineModal() {
    const form = document.getElementById("form-add-medicine");
    if (form) form.reset();
    document.getElementById("modal-add-medicine").classList.add("active");
  },

  async handleAddMedicine(e) {
    e.preventDefault();
    const name = document.getElementById("new-med-name").value.trim();
    const generic = document.getElementById("new-med-generic").value.trim();
    const manufacturer = document.getElementById("new-med-mfg").value.trim();
    const category = document.getElementById("new-med-category").value;
    const hsn = document.getElementById("new-med-hsn").value.trim() || "3004";
    const gst = parseFloat(document.getElementById("new-med-gst").value) || 12.0;
    const rack = document.getElementById("new-med-rack").value.trim();
    const unit = document.getElementById("new-med-unit").value.trim() || "Strip";
    const minStock = parseInt(document.getElementById("new-med-min-stock").value, 10) || 10;
    const pPrice = parseFloat(document.getElementById("new-med-purchase-price").value) || 0.0;
    const sPrice = parseFloat(document.getElementById("new-med-selling-price").value) || 0.0;
    const barcode = document.getElementById("new-med-barcode").value.trim() || null;

    // Optional batch info
    const initialBatch = document.getElementById("new-med-batch").value.trim();
    const expiryDate = document.getElementById("new-med-expiry").value || null;
    const initQty = parseInt(document.getElementById("new-med-qty").value, 10) || null;

    const payload = {
      name,
      generic_name: generic,
      manufacturer,
      category,
      hsn_code: hsn,
      gst_rate: gst,
      rack_location: rack,
      unit,
      min_stock_level: minStock,
      default_purchase_price: pPrice,
      default_selling_price: sPrice,
      barcode,
      initial_batch_number: initialBatch || null,
      expiry_date: expiryDate,
      quantity: initQty
    };

    try {
      await API.post("/api/medicines", payload);
      App.showToast(`Medicine "${name}" registered successfully!`, "success");
      document.getElementById("modal-add-medicine").classList.remove("active");
      this.load();
      Dashboard.load();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  openAddBatchModal(medicineId) {
    const med = this.currentMedicines.find(m => m.id === medicineId);
    if (!med) return;

    document.getElementById("batch-modal-med-id").value = medicineId;
    document.getElementById("batch-modal-med-title").textContent = `Add Batch for: ${med.name}`;
    document.getElementById("batch-purchase-price").value = med.default_purchase_price || "";
    document.getElementById("batch-selling-price").value = med.default_selling_price || "";
    document.getElementById("batch-mrp").value = med.default_selling_price || "";

    document.getElementById("modal-add-batch").classList.add("active");
  },

  async handleAddBatch(e) {
    e.preventDefault();
    const medId = document.getElementById("batch-modal-med-id").value;
    const batchNum = document.getElementById("batch-number-input").value.trim();
    const expiry = document.getElementById("batch-expiry-input").value;
    const qty = parseInt(document.getElementById("batch-qty-input").value, 10);
    const pPrice = parseFloat(document.getElementById("batch-purchase-price").value) || 0;
    const mrp = parseFloat(document.getElementById("batch-mrp").value) || 0;
    const sPrice = parseFloat(document.getElementById("batch-selling-price").value) || 0;

    const payload = {
      batch_number: batchNum,
      expiry_date: expiry,
      quantity: qty,
      purchase_price: pPrice,
      mrp: mrp,
      selling_price: sPrice
    };

    try {
      await API.post(`/api/medicines/${medId}/batches`, payload);
      App.showToast(`Batch ${batchNum} added successfully!`, "success");
      document.getElementById("modal-add-batch").classList.remove("active");
      this.load();
      Dashboard.load();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  viewBatchesDetail(medicineId) {
    const med = this.currentMedicines.find(m => m.id === medicineId);
    if (!med) return;

    const modal = document.getElementById("modal-view-batches");
    document.getElementById("view-batches-title").textContent = `Batches for: ${med.name}`;
    const tbody = document.getElementById("view-batches-tbody");

    if (!med.batches || med.batches.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; padding:20px; color:#94a3b8;">No batches tracked for this medicine.</td></tr>`;
    } else {
      tbody.innerHTML = med.batches.map(b => `
        <tr style="background:${b.is_expired ? '#fef2f2' : 'white'};">
          <td><b>${b.batch_number}</b></td>
          <td>${b.expiry_date}</td>
          <td>${b.days_to_expiry} days</td>
          <td><b>${b.quantity} units</b></td>
          <td>₹ ${b.purchase_price.toFixed(2)}</td>
          <td>₹ ${b.mrp.toFixed(2)}</td>
          <td>
            ${b.is_expired 
              ? `<span class="badge badge-red">EXPIRED</span>` 
              : (b.quantity <= 5 ? `<span class="badge badge-orange">LOW STOCK</span>` : `<span class="badge badge-green">ACTIVE</span>`)}
          </td>
        </tr>
      `).join("");
    }

    modal.classList.add("active");
  }
};
