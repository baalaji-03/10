/**
 * Customer Management & Purchase History Controller
 */

const Customers = {
  currentCustomers: [],

  init() {
    const searchInput = document.getElementById("customer-search-filter");
    if (searchInput) {
      let debounce = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(debounce);
        debounce = setTimeout(() => this.load(e.target.value.trim()), 200);
      });
    }

    const addForm = document.getElementById("form-add-customer");
    if (addForm) {
      addForm.addEventListener("submit", (e) => this.handleAddCustomer(e));
    }
  },

  async load(search = "") {
    try {
      let endpoint = `/api/customers`;
      if (search) endpoint += `?search=${encodeURIComponent(search)}`;
      const list = await API.get(endpoint);
      this.currentCustomers = list;
      this.renderTable(list);
    } catch (err) {
      App.showToast("Failed to load customers: " + err.message, "error");
    }
  },

  renderTable(list) {
    const tbody = document.getElementById("customers-table-tbody");
    if (!tbody) return;

    if (!list || list.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:30px; color:#94a3b8;">No registered customers found.</td></tr>`;
      return;
    }

    tbody.innerHTML = list.map(c => `
      <tr>
        <td><b>${c.customer_code || ''}</b></td>
        <td><b>${c.name}</b></td>
        <td><b>${c.mobile}</b></td>
        <td>${c.email || '-'}</td>
        <td>${c.address || '-'}</td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="Customers.viewPurchaseHistory(${c.id})">
            Purchase History
          </button>
        </td>
      </tr>
    `).join("");
  },

  openAddCustomerModal() {
    const form = document.getElementById("form-add-customer");
    if (form) form.reset();
    document.getElementById("modal-add-customer").classList.add("active");
  },

  async handleAddCustomer(e) {
    e.preventDefault();
    const name = document.getElementById("cust-name").value.trim();
    const mobile = document.getElementById("cust-mobile").value.trim();
    const email = document.getElementById("cust-email").value.trim();
    const address = document.getElementById("cust-address").value.trim();
    const dob = document.getElementById("cust-dob").value || null;
    const gender = document.getElementById("cust-gender").value;

    if (!name || !mobile) {
      App.showToast("Name and Mobile are required.", "warning");
      return;
    }

    const payload = {
      name,
      mobile,
      email,
      address,
      date_of_birth: dob,
      gender
    };

    try {
      const created = await API.post("/api/customers", payload);
      App.showToast(`Customer "${created.name}" registered successfully!`, "success");
      document.getElementById("modal-add-customer").classList.remove("active");
      this.load();
      Dashboard.load();
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async viewPurchaseHistory(customerId) {
    try {
      const data = await API.get(`/api/customers/${customerId}/history`);
      const modal = document.getElementById("modal-customer-history");
      const c = data.customer;

      document.getElementById("cust-history-title").textContent = `Purchase History: ${c.name} (${c.mobile})`;
      document.getElementById("cust-history-summary").textContent = `Total Visits: ${c.total_purchases_count} | Total Lifetime Spend: ₹ ${c.total_spend.toFixed(2)}`;

      const tbody = document.getElementById("cust-history-tbody");
      if (!data.invoices || data.invoices.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; padding:20px; color:#94a3b8;">No past bills found for this customer.</td></tr>`;
      } else {
        tbody.innerHTML = data.invoices.map(inv => `
          <tr>
            <td><b>${inv.invoice_number}</b></td>
            <td>${inv.invoice_date} ${inv.invoice_time}</td>
            <td>
              <div style="font-size:12px;">${inv.items_summary.slice(0, 3).join(", ")}${inv.items_summary.length > 3 ? "..." : ""}</div>
            </td>
            <td><b>₹ ${inv.net_amount.toFixed(2)}</b></td>
            <td><span class="badge badge-green">${inv.payment_method}</span></td>
            <td>
              <button class="btn btn-secondary btn-sm" onclick="Invoices.viewInvoice(${inv.sale_id})">Reprint</button>
            </td>
          </tr>
        `).join("");
      }

      modal.classList.add("active");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  }
};
