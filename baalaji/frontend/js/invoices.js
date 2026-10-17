/**
 * Invoice Printing, PDF Generation & Reprint Controller
 */

const Invoices = {
  currentSaleId: null,
  currentPrintFormat: "80mm", // Default thermal width

  init() {
    const btnPrintNow = document.getElementById("btn-trigger-print");
    if (btnPrintNow) {
      btnPrintNow.addEventListener("click", () => this.triggerPrint());
    }

    const btnDownloadPdf = document.getElementById("btn-download-invoice-pdf");
    if (btnDownloadPdf) {
      btnDownloadPdf.addEventListener("click", () => this.downloadPdf());
    }

    // Format selection buttons (58mm, 80mm, A4)
    const formatBtns = document.querySelectorAll(".btn-format-toggle");
    formatBtns.forEach(btn => {
      btn.addEventListener("click", (e) => {
        formatBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        this.setPrintFormat(btn.dataset.format);
      });
    });
  },

  async viewInvoice(saleId) {
    this.currentSaleId = saleId;
    try {
      const data = await API.get(`/api/invoices/${saleId}/print-data`);
      this.renderReceipt(data);
      document.getElementById("modal-invoice-print").classList.add("active");
    } catch (err) {
      App.showToast("Failed to load invoice details: " + err.message, "error");
    }
  },

  setPrintFormat(format) {
    this.currentPrintFormat = format;
    const paper = document.getElementById("printable-receipt-area");
    if (!paper) return;

    paper.className = `receipt-paper format-${format.toLowerCase()}`;
    // Re-render
    if (this.currentSaleId) {
      this.viewInvoice(this.currentSaleId);
    }
  },

  renderReceipt(data) {
    const paper = document.getElementById("printable-receipt-area");
    if (!paper) return;

    const p = data.pharmacy;
    const s = data.sale;
    const items = data.items;
    const format = this.currentPrintFormat;

    if (format === "A4") {
      paper.className = "receipt-paper format-a4";
      paper.innerHTML = `
        <div style="border: 2px solid #0f766e; border-radius: 8px; padding: 20px;">
          <!-- A4 Header -->
          <div style="display:flex; justify-content:space-between; align-items:center; border-bottom: 2px solid #0f766e; padding-bottom: 12px; margin-bottom: 14px;">
            <div>
              <h1 style="font-size:22px; font-weight:800; color:#0f766e; margin:0;">${p.name}</h1>
              <p style="font-size:12px; color:#64748b; font-style:italic; margin:2px 0;">${p.tagline}</p>
              <p style="font-size:12px; margin:2px 0;">${p.address}</p>
              <p style="font-size:12px; margin:2px 0;">Phone: <b>${p.phone}</b> | Email: ${p.email}</p>
              <p style="font-size:12px; margin:2px 0;"><b>GSTIN: ${p.gstin}</b> | <b>D.L. No: ${p.dl_number}</b></p>
            </div>
            <div style="text-align:right;">
              <span style="background:#0f766e; color:white; padding:4px 12px; font-weight:700; font-size:13px; border-radius:4px;">TAX INVOICE</span>
              <p style="font-size:13px; font-weight:700; margin-top:8px;">Bill No: ${s.invoice_number}</p>
              <p style="font-size:12px; color:#64748b;">Date: ${s.date} ${s.time}</p>
            </div>
          </div>

          <!-- Customer details -->
          <div style="display:flex; justify-content:space-between; background:#f8fafc; padding:10px 14px; border-radius:6px; margin-bottom:14px; font-size:12.5px;">
            <div>
              <div>Billed To: <b>${s.customer_name}</b></div>
              <div>Mobile: <b>${s.customer_mobile}</b></div>
            </div>
            <div style="text-align:right;">
              <div>Prescribing Doctor: <b>${s.doctor_name}</b></div>
              <div>Payment Method: <b>${s.payment_method}</b> (${s.payment_status})</div>
            </div>
          </div>

          <!-- Items Table -->
          <table style="width:100%; border-collapse:collapse; font-size:12px; margin-bottom:16px;">
            <thead>
              <tr style="background:#0f766e; color:white; text-align:left;">
                <th style="padding:8px;">#</th>
                <th style="padding:8px;">Medicine</th>
                <th style="padding:8px;">HSN</th>
                <th style="padding:8px;">Batch</th>
                <th style="padding:8px;">Exp</th>
                <th style="padding:8px; text-align:right;">Qty</th>
                <th style="padding:8px; text-align:right;">MRP</th>
                <th style="padding:8px; text-align:right;">Rate</th>
                <th style="padding:8px; text-align:right;">GST%</th>
                <th style="padding:8px; text-align:right;">Total (₹)</th>
              </tr>
            </thead>
            <tbody>
              ${items.map((item, idx) => `
                <tr style="border-bottom:1px solid #e2e8f0; ${idx % 2 === 1 ? 'background:#f8fafc;' : ''}">
                  <td style="padding:7px 8px;">${idx + 1}</td>
                  <td style="padding:7px 8px;"><b>${item.name}</b><br/><span style="font-size:10.5px; color:#64748b;">${item.generic || ''}</span></td>
                  <td style="padding:7px 8px;">${item.hsn}</td>
                  <td style="padding:7px 8px;">${item.batch}</td>
                  <td style="padding:7px 8px;">${item.expiry}</td>
                  <td style="padding:7px 8px; text-align:right;">${item.qty}</td>
                  <td style="padding:7px 8px; text-align:right;">₹${item.mrp.toFixed(2)}</td>
                  <td style="padding:7px 8px; text-align:right;">₹${item.rate.toFixed(2)}</td>
                  <td style="padding:7px 8px; text-align:right;">${item.gst_rate}%</td>
                  <td style="padding:7px 8px; text-align:right; font-weight:700;">₹${item.total.toFixed(2)}</td>
                </tr>
              `).join("")}
            </tbody>
          </table>

          <!-- Totals summary -->
          <div style="display:flex; justify-content:space-between; margin-top:14px; font-size:12.5px;">
            <div style="max-width:350px;">
              <p style="font-size:11px; color:#64748b;"><b>GST Breakdown:</b> Taxable: ₹${s.taxable.toFixed(2)} | CGST: ₹${s.cgst.toFixed(2)} | SGST: ₹${s.sgst.toFixed(2)}</p>
              <p style="font-size:10.5px; color:#64748b; margin-top:8px;">${p.declaration}</p>
            </div>
            <div style="min-width:220px; text-align:right;">
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Subtotal:</span> <span>₹${s.subtotal.toFixed(2)}</span></div>
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Discount:</span> <span>- ₹${s.discount.toFixed(2)}</span></div>
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Total GST:</span> <span>₹${s.tax.toFixed(2)}</span></div>
              <div style="display:flex; justify-content:space-between; margin-bottom:4px;"><span>Round Off:</span> <span>₹${s.round_off.toFixed(2)}</span></div>
              <div style="display:flex; justify-content:space-between; font-size:16px; font-weight:800; color:#0f766e; border-top:2px solid #0f766e; padding-top:6px; margin-top:6px;">
                <span>GRAND TOTAL:</span> <span>₹${s.net_amount.toFixed(2)}</span>
              </div>
              <div style="margin-top:25px; font-size:11px;">
                For <b>${p.name}</b><br/><br/>
                Authorized Signatory / Pharmacist
              </div>
            </div>
          </div>
        </div>
      `;
    } else {
      // 58mm or 80mm Thermal Receipt
      const is58 = format === "58mm";
      paper.className = `receipt-paper format-${format.toLowerCase()}`;
      paper.innerHTML = `
        <div style="text-align:center;">
          <div style="font-size:${is58 ? '12px' : '14px'}; font-weight:bold;">${p.name.toUpperCase()}</div>
          <div style="font-size:${is58 ? '9px' : '10px'};">${p.address}</div>
          <div style="font-size:${is58 ? '9px' : '10px'};">Ph: ${p.phone}</div>
          <div style="font-size:${is58 ? '9px' : '10px'};">GSTIN: ${p.gstin}</div>
          <div style="font-size:${is58 ? '9px' : '10px'};">DL: ${p.dl_number}</div>
        </div>
        <div style="border-top:1px dashed #000; margin:6px 0;"></div>
        <div style="font-size:${is58 ? '9px' : '10.5px'};">
          <div><b>Bill: ${s.invoice_number}</b></div>
          <div>Date: ${s.date} ${s.time}</div>
          <div>Cust: ${s.customer_name} (${s.customer_mobile || ''})</div>
          <div>Cashier: ${s.cashier}</div>
        </div>
        <div style="border-top:1px dashed #000; margin:6px 0;"></div>

        <table style="width:100%; border-collapse:collapse; font-size:${is58 ? '8.5px' : '10px'};">
          <thead>
            <tr style="border-bottom:1px solid #000; text-align:left;">
              <th>Item</th>
              <th>Batch</th>
              <th style="text-align:right;">Qty</th>
              <th style="text-align:right;">Amt</th>
            </tr>
          </thead>
          <tbody>
            ${items.map(i => `
              <tr>
                <td>${i.name.slice(0, is58 ? 12 : 16)}</td>
                <td>${i.batch.slice(0, 6)}</td>
                <td style="text-align:right;">${i.qty}</td>
                <td style="text-align:right;">${i.total.toFixed(1)}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>

        <div style="border-top:1px dashed #000; margin:6px 0;"></div>
        <div style="font-size:${is58 ? '9.5px' : '11px'};">
          <div style="display:flex; justify-content:space-between;"><span>Taxable:</span> <span>₹${s.taxable.toFixed(2)}</span></div>
          <div style="display:flex; justify-content:space-between;"><span>GST Total:</span> <span>₹${s.tax.toFixed(2)}</span></div>
          <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:${is58 ? '12px' : '14px'}; margin-top:4px;">
            <span>TOTAL:</span> <span>₹${s.net_amount.toFixed(2)}</span>
          </div>
          <div style="display:flex; justify-content:space-between; margin-top:2px;">
            <span>Paid (${s.payment_method}):</span> <span>₹${s.paid_amount.toFixed(2)}</span>
          </div>
        </div>
        <div style="border-top:1px dashed #000; margin:6px 0;"></div>
        <div style="text-align:center; font-size:${is58 ? '8px' : '9px'};">
          Thank you! Get well soon!<br/>
          Goods once sold cannot be returned without bill.
        </div>
      `;
    }
  },

  triggerPrint() {
    // Add print format class to body
    document.body.className = `print-${this.currentPrintFormat.toLowerCase()}`;
    window.print();
  },

  async downloadPdf() {
    if (!this.currentSaleId) return;
    try {
      const url = `/api/invoices/${this.currentSaleId}/pdf?format=${this.currentPrintFormat}`;
      await API.download(url, `Invoice_${this.currentSaleId}_${this.currentPrintFormat}.pdf`);
    } catch (err) {
      App.showToast("Failed to download PDF: " + err.message, "error");
    }
  }
};
