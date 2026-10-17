/**
 * Sales and Purchase Returns Controller
 */

const Returns = {
  currentSaleToReturn: null,

  init() {
    const searchSaleBtn = document.getElementById("btn-lookup-return-sale");
    if (searchSaleBtn) {
      searchSaleBtn.addEventListener("click", () => this.lookupSaleForReturn());
    }

    const form = document.getElementById("form-process-sales-return");
    if (form) {
      form.addEventListener("submit", (e) => this.handleProcessSalesReturn(e));
    }
  },

  async lookupSaleForReturn() {
    const invNum = document.getElementById("return-invoice-lookup")?.value.trim();
    if (!invNum) {
      App.showToast("Please enter an invoice number to return.", "warning");
      return;
    }

    try {
      const list = await API.get(`/api/pos/invoices?search=${encodeURIComponent(invNum)}`);
      const matched = list.find(s => s.invoice_number.toUpperCase() === invNum.toUpperCase());
      if (!matched) {
        App.showToast(`Invoice "${invNum}" not found.`, "error");
        return;
      }

      const sale = await API.get(`/api/pos/invoices/${matched.id}`);
      this.currentSaleToReturn = sale;

      document.getElementById("return-sale-info").style.display = "block";
      document.getElementById("ret-cust-name").textContent = `${sale.customer_name} (${sale.customer_mobile || 'Walk-in'})`;
      document.getElementById("ret-bill-date").textContent = `${sale.invoice_date} ${sale.invoice_time}`;
      document.getElementById("ret-bill-total").textContent = `₹ ${sale.net_amount.toFixed(2)}`;

      const tbody = document.getElementById("return-items-select-tbody");
      tbody.innerHTML = sale.items.map(item => `
        <tr>
          <td><b>${item.medicine_name}</b></td>
          <td>${item.batch_number}</td>
          <td>${item.quantity}</td>
          <td>₹ ${item.unit_price.toFixed(2)}</td>
          <td>
            <input type="number" min="0" max="${item.quantity}" value="0" 
              class="ret-item-qty" data-item-id="${item.id}"
              style="width:65px; padding:4px; border:1px solid #cbd5e1; border-radius:4px;" />
          </td>
          <td>
            <select class="ret-item-status" data-item-id="${item.id}" style="padding:4px; font-size:12px; border:1px solid #cbd5e1; border-radius:4px;">
              <option value="RESTOCKED">Restock to Batch</option>
              <option value="DAMAGED_EXPIRED">Damaged / Expired (Quarantine)</option>
            </select>
          </td>
        </tr>
      `).join("");
    } catch (err) {
      App.showToast(err.message, "error");
    }
  },

  async handleProcessSalesReturn(e) {
    e.preventDefault();
    if (!this.currentSaleToReturn) {
      App.showToast("Please search for an invoice first.", "warning");
      return;
    }

    const reason = document.getElementById("return-reason-input").value.trim();
    const refundMethod = document.getElementById("return-refund-method").value;
    const qtyInputs = document.querySelectorAll(".ret-item-qty");

    const returnItems = [];
    qtyInputs.forEach(input => {
      const q = parseInt(input.value, 10);
      const itemId = parseInt(input.dataset.itemId, 10);
      const statusSelect = document.querySelector(`.ret-item-status[data-item-id="${itemId}"]`);
      if (q > 0) {
        returnItems.push({
          sale_item_id: itemId,
          quantity: q,
          restock_status: statusSelect ? statusSelect.value : "RESTOCKED"
        });
      }
    });

    if (returnItems.length === 0) {
      App.showToast("Please specify at least one return quantity greater than 0.", "warning");
      return;
    }

    const payload = {
      sale_id: this.currentSaleToReturn.id,
      reason: reason || "Customer Return",
      refund_method: refundMethod,
      items: returnItems
    };

    try {
      const res = await API.post("/api/returns/sales", payload);
      App.showToast(`Sales return ${res.return_number} processed! Refund amount: ₹${res.total_refund_amount.toFixed(2)}`, "success");
      
      // Reset
      document.getElementById("form-process-sales-return").reset();
      document.getElementById("return-sale-info").style.display = "none";
      this.currentSaleToReturn = null;
      Dashboard.load();
    } catch (err) {
      App.showToast("Error processing return: " + err.message, "error");
    }
  }
};
