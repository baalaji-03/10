/**
 * Fast POS Billing & Point of Sale Controller
 */

const POS = {
  cart: [],
  selectedCustomer: null,
  searchResults: [],

  init() {
    const barcodeInput = document.getElementById("pos-barcode-input");
    if (barcodeInput) {
      barcodeInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
          e.preventDefault();
          this.handleBarcodeScan(barcodeInput.value.trim());
        }
      });
    }

    const searchInput = document.getElementById("pos-search-input");
    if (searchInput) {
      let debounceTimer = null;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.searchMedicines(e.target.value.trim());
        }, 200);
      });
    }

    const btnClearCart = document.getElementById("btn-clear-cart");
    if (btnClearCart) {
      btnClearCart.addEventListener("click", () => this.clearCart());
    }

    const btnCheckout = document.getElementById("btn-pos-checkout");
    if (btnCheckout) {
      btnCheckout.addEventListener("click", () => this.checkout());
    }

    // Keyboard shortcuts
    window.addEventListener("keydown", (e) => {
      if (App.currentView !== "pos") return;
      if (e.key === "F2") {
        e.preventDefault();
        searchInput?.focus();
      } else if (e.key === "F4") {
        e.preventDefault();
        document.getElementById("pos-customer-mobile")?.focus();
      } else if (e.key === "F9") {
        e.preventDefault();
        this.checkout();
      }
    });
  },

  async handleBarcodeScan(barcode) {
    if (!barcode) return;
    try {
      const med = await API.get(`/api/medicines/barcode/${encodeURIComponent(barcode)}`);
      document.getElementById("pos-barcode-input").value = "";
      this.promptBatchSelection(med);
    } catch (err) {
      App.showToast(`Barcode not recognized: ${barcode}`, "warning");
    }
  },

  async searchMedicines(query) {
    const resultsContainer = document.getElementById("pos-search-dropdown");
    if (!resultsContainer) return;

    if (!query || query.length < 2) {
      resultsContainer.style.display = "none";
      resultsContainer.innerHTML = "";
      return;
    }

    try {
      const list = await API.get(`/api/medicines?search=${encodeURIComponent(query)}`);
      this.searchResults = list;

      if (list.length === 0) {
        resultsContainer.innerHTML = `<div style="padding:12px; color:#64748b;">No medicines found matching "${query}"</div>`;
        resultsContainer.style.display = "block";
        return;
      }

      resultsContainer.innerHTML = list.map(m => `
        <div class="search-result-item" onclick="POS.selectMedicineFromSearch(${m.id})" style="padding:10px 14px; border-bottom:1px solid #e2e8f0; cursor:pointer; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <div style="font-weight:600; font-size:13.5px; color:#0f172a;">${m.name}</div>
            <div style="font-size:11.5px; color:#64748b;">${m.generic_name || ''} | Rack: ${m.rack_location || 'N/A'} | GST: ${m.gst_rate}%</div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700; color:#0f766e;">Stock: ${m.total_stock}</div>
            <div style="font-size:11px; color:#64748b;">MRP: ₹${Number(m.default_selling_price || 0).toFixed(2)}</div>
          </div>
        </div>
      `).join("");
      resultsContainer.style.display = "block";
    } catch (err) {
      console.error(err);
    }
  },

  selectMedicineFromSearch(medId) {
    const med = this.searchResults.find(m => m.id === medId);
    const resultsContainer = document.getElementById("pos-search-dropdown");
    if (resultsContainer) resultsContainer.style.display = "none";
    document.getElementById("pos-search-input").value = "";
    if (med) {
      this.promptBatchSelection(med);
    }
  },

  promptBatchSelection(med) {
    if (!med.batches || med.batches.length === 0) {
      App.showToast(`No stock batches available for ${med.name}. Please enter a purchase first.`, "error");
      return;
    }

    // Filter available batches
    const availableBatches = med.batches.filter(b => b.quantity > 0 && !b.is_expired);
    const expiredBatches = med.batches.filter(b => b.is_expired);

    if (availableBatches.length === 0 && expiredBatches.length > 0) {
      App.showToast(`CRITICAL: All stock batches for ${med.name} are EXPIRED and CANNOT be sold!`, "error");
      return;
    }

    if (availableBatches.length === 1) {
      // Auto-select single available batch
      this.addToCart(med, availableBatches[0], 1);
    } else {
      // Show batch selector modal
      this.openBatchSelectorModal(med, med.batches);
    }
  },

  openBatchSelectorModal(med, batches) {
    const modal = document.getElementById("modal-pos-batch-select");
    const container = document.getElementById("pos-batch-options-list");
    document.getElementById("batch-select-med-name").textContent = med.name;

    container.innerHTML = batches.map(b => {
      const isExp = b.is_expired;
      const isLow = b.quantity <= 5;
      return `
        <div style="padding:12px; border:1px solid ${isExp ? '#fca5a5' : '#cbd5e1'}; border-radius:8px; margin-bottom:10px; display:flex; justify-content:space-between; align-items:center; background:${isExp ? '#fef2f2' : '#ffffff'};">
          <div>
            <div style="font-weight:700; font-size:13.5px;">Batch: ${b.batch_number}</div>
            <div style="font-size:12px; color:#475569;">
              Exp: <b>${b.expiry_date}</b> (${b.days_to_expiry} days) | Available: <b>${b.quantity}</b> | MRP: <b>₹${b.mrp.toFixed(2)}</b>
            </div>
          </div>
          <div>
            ${isExp 
              ? `<span class="badge badge-red">EXPIRED (BLOCKED)</span>`
              : `<button class="btn btn-primary btn-sm" onclick="POS.confirmBatchSelection(${med.id}, ${b.id})">Select Batch</button>`
            }
          </div>
        </div>
      `;
    }).join("");

    modal.classList.add("active");
  },

  confirmBatchSelection(medId, batchId) {
    let med = this.searchResults.find(m => m.id === medId);
    if (!med) {
      // Fallback lookup
      API.get(`/api/medicines?search=`).then(list => {
        med = list.find(m => m.id === medId);
        if (med) {
          const batch = med.batches.find(b => b.id === batchId);
          this.addToCart(med, batch, 1);
          document.getElementById("modal-pos-batch-select").classList.remove("active");
        }
      });
      return;
    }

    const batch = med.batches.find(b => b.id === batchId);
    if (batch) {
      this.addToCart(med, batch, 1);
      document.getElementById("modal-pos-batch-select").classList.remove("active");
    }
  },

  addToCart(med, batch, qty = 1) {
    if (batch.is_expired) {
      App.showToast("Cannot sell an expired batch!", "error");
      return;
    }

    const existingIndex = this.cart.findIndex(i => i.batch_id === batch.id);
    if (existingIndex > -1) {
      const existing = this.cart[existingIndex];
      if (existing.quantity + qty > batch.quantity) {
        App.showToast(`Cannot add more. Only ${batch.quantity} units available in Batch ${batch.batch_number}.`, "warning");
        return;
      }
      existing.quantity += qty;
    } else {
      if (qty > batch.quantity) {
        App.showToast(`Requested quantity exceeds available stock (${batch.quantity}).`, "warning");
        return;
      }
      this.cart.push({
        medicine_id: med.id,
        batch_id: batch.id,
        name: med.name,
        generic: med.generic_name || "",
        batch_number: batch.batch_number,
        expiry_date: batch.expiry_date,
        max_quantity: batch.quantity,
        quantity: qty,
        unit_price: batch.selling_price || batch.mrp,
        mrp: batch.mrp,
        discount_percent: 0.0,
        gst_rate: Number(med.gst_rate || 12.0)
      });
    }

    App.showToast(`Added ${med.name} to bill`, "success");
    this.renderCart();
  },

  updateCartQty(index, newQty) {
    const item = this.cart[index];
    const qty = parseInt(newQty, 10);
    if (isNaN(qty) || qty <= 0) {
      this.removeCartItem(index);
      return;
    }
    if (qty > item.max_quantity) {
      App.showToast(`Stock limit reached! Only ${item.max_quantity} units available.`, "warning");
      item.quantity = item.max_quantity;
    } else {
      item.quantity = qty;
    }
    this.renderCart();
  },

  updateCartDiscount(index, newDisc) {
    const item = this.cart[index];
    const disc = parseFloat(newDisc) || 0;
    item.discount_percent = Math.min(100, Math.max(0, disc));
    this.renderCart();
  },

  removeCartItem(index) {
    this.cart.splice(index, 1);
    this.renderCart();
  },

  clearCart() {
    this.cart = [];
    this.renderCart();
  },

  calculateTotals() {
    let subtotal = 0;
    let totalDiscount = 0;
    let totalTaxable = 0;
    let totalTax = 0;

    for (const item of this.cart) {
      const gross = item.unit_price * item.quantity;
      const disc = gross * (item.discount_percent / 100);
      const taxable = gross - disc;
      const tax = taxable * (item.gst_rate / 100);

      subtotal += gross;
      totalDiscount += disc;
      totalTaxable += taxable;
      totalTax += tax;
    }

    const netAmount = Math.round(totalTaxable + totalTax);
    const roundOff = netAmount - (totalTaxable + totalTax);

    return {
      subtotal,
      discount: totalDiscount,
      taxable: totalTaxable,
      tax: totalTax,
      roundOff,
      netAmount
    };
  },

  renderCart() {
    const container = document.getElementById("pos-cart-items-list");
    const countBadge = document.getElementById("cart-items-count");
    if (!container) return;

    if (countBadge) countBadge.textContent = this.cart.length;

    if (this.cart.length === 0) {
      container.innerHTML = `
        <div style="text-align:center; padding: 40px 10px; color:#94a3b8;">
          <p style="font-size:14px; font-weight:500;">Bill is empty</p>
          <p style="font-size:12px; margin-top:4px;">Scan barcode or search medicine to add</p>
        </div>
      `;
      document.getElementById("pos-cart-subtotal").textContent = "₹ 0.00";
      document.getElementById("pos-cart-tax").textContent = "₹ 0.00";
      document.getElementById("pos-cart-discount").textContent = "₹ 0.00";
      document.getElementById("pos-cart-total").textContent = "₹ 0.00";
      return;
    }

    container.innerHTML = this.cart.map((item, idx) => {
      const gross = item.unit_price * item.quantity;
      const disc = gross * (item.discount_percent / 100);
      const tax = (gross - disc) * (item.gst_rate / 100);
      const itemTotal = (gross - disc) + tax;

      return `
        <div class="cart-item-row">
          <div style="flex:1;">
            <div class="cart-item-title">${item.name}</div>
            <div class="cart-item-meta">
              Batch: <b>${item.batch_number}</b> | Exp: ${item.expiry_date} | GST: ${item.gst_rate}%
            </div>
            <div style="display:flex; align-items:center; gap:8px; margin-top:6px;">
              <span style="font-size:11.5px; color:#64748b;">Qty:</span>
              <input type="number" min="1" max="${item.max_quantity}" value="${item.quantity}" 
                onchange="POS.updateCartQty(${idx}, this.value)" 
                style="width:55px; padding:3px 6px; font-size:12px; border:1px solid #cbd5e1; border-radius:4px;" />
              
              <span style="font-size:11.5px; color:#64748b; margin-left:6px;">Disc%:</span>
              <input type="number" min="0" max="100" value="${item.discount_percent}" 
                onchange="POS.updateCartDiscount(${idx}, this.value)" 
                style="width:50px; padding:3px 6px; font-size:12px; border:1px solid #cbd5e1; border-radius:4px;" />
            </div>
          </div>
          <div style="text-align:right;">
            <div style="font-weight:700; font-size:14px; color:#0f766e;">₹ ${itemTotal.toFixed(2)}</div>
            <div style="font-size:11px; color:#64748b;">₹ ${item.unit_price.toFixed(2)} / unit</div>
            <button onclick="POS.removeCartItem(${idx})" style="background:none; border:none; color:#ef4444; font-size:11px; cursor:pointer; margin-top:4px;">Remove</button>
          </div>
        </div>
      `;
    }).join("");

    const totals = this.calculateTotals();
    document.getElementById("pos-cart-subtotal").textContent = `₹ ${totals.subtotal.toFixed(2)}`;
    document.getElementById("pos-cart-discount").textContent = `- ₹ ${totals.discount.toFixed(2)}`;
    document.getElementById("pos-cart-tax").textContent = `₹ ${totals.tax.toFixed(2)}`;
    document.getElementById("pos-cart-total").textContent = `₹ ${totals.netAmount.toFixed(2)}`;
  },

  async checkout() {
    if (this.cart.length === 0) {
      App.showToast("Cannot checkout an empty bill!", "warning");
      return;
    }

    const totals = this.calculateTotals();
    const custName = document.getElementById("pos-customer-name")?.value.trim() || "Walk-in Customer";
    const custMobile = document.getElementById("pos-customer-mobile")?.value.trim() || "";
    const doctorName = document.getElementById("pos-doctor-name")?.value.trim() || "";
    const payMethod = document.getElementById("pos-payment-method")?.value || "CASH";

    const payload = {
      customer_id: this.selectedCustomer ? this.selectedCustomer.id : null,
      customer_name: custName,
      customer_mobile: custMobile,
      doctor_name: doctorName,
      payment_method: payMethod,
      paid_amount: totals.netAmount,
      items: this.cart.map(i => ({
        medicine_id: i.medicine_id,
        batch_id: i.batch_id,
        quantity: i.quantity,
        unit_price: i.unit_price,
        discount_percent: i.discount_percent
      }))
    };

    try {
      const btn = document.getElementById("btn-pos-checkout");
      btn.disabled = true;
      btn.textContent = "Processing Bill...";

      const sale = await API.post("/api/pos/sale", payload);
      App.showToast(`Bill ${sale.invoice_number} completed successfully!`, "success");

      // Reset POS
      this.clearCart();
      if (document.getElementById("pos-customer-name")) document.getElementById("pos-customer-name").value = "";
      if (document.getElementById("pos-customer-mobile")) document.getElementById("pos-customer-mobile").value = "";
      if (document.getElementById("pos-doctor-name")) document.getElementById("pos-doctor-name").value = "";
      this.selectedCustomer = null;

      // Open Print Modal Immediately
      Invoices.viewInvoice(sale.id);

      // Refresh Dashboard in background
      Dashboard.load();
    } catch (err) {
      App.showToast("Checkout Failed: " + err.message, "error");
    } finally {
      const btn = document.getElementById("btn-pos-checkout");
      btn.disabled = false;
      btn.textContent = "Complete & Print Bill (F9)";
    }
  }
};
