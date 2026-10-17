/**
 * Financial, GST and Profitability Reports Controller
 */

const Reports = {
  init() {
    const filterBtn = document.getElementById("btn-apply-report-filter");
    if (filterBtn) {
      filterBtn.addEventListener("click", () => this.load());
    }

    const rangeSelect = document.getElementById("report-date-preset");
    if (rangeSelect) {
      rangeSelect.addEventListener("change", (e) => this.handlePresetChange(e.target.value));
    }

    const expSales = document.getElementById("btn-rep-export-sales");
    if (expSales) {
      expSales.addEventListener("click", () => API.download("/api/excel/export/sales", "Sales_Report.xlsx"));
    }

    const expGst = document.getElementById("btn-rep-export-gst");
    if (expGst) {
      expGst.addEventListener("click", () => API.download("/api/excel/export/gst-summary", "GSTR1_Report.xlsx"));
    }
  },

  handlePresetChange(preset) {
    const startInput = document.getElementById("report-start-date");
    const endInput = document.getElementById("report-end-date");
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];

    if (preset === "today") {
      startInput.value = todayStr;
      endInput.value = todayStr;
    } else if (preset === "week") {
      const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);
      startInput.value = weekAgo.toISOString().split("T")[0];
      endInput.value = todayStr;
    } else if (preset === "month") {
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1);
      startInput.value = monthStart.toISOString().split("T")[0];
      endInput.value = todayStr;
    } else if (preset === "all") {
      startInput.value = "";
      endInput.value = "";
    }
    this.load();
  },

  async load() {
    const start = document.getElementById("report-start-date")?.value || "";
    const end = document.getElementById("report-end-date")?.value || "";

    try {
      let endpoint = `/api/reports/financial?`;
      if (start) endpoint += `start_date=${start}&`;
      if (end) endpoint += `end_date=${end}&`;

      const data = await API.get(endpoint);
      const s = data.summary;

      // Update Metric Tiles
      document.getElementById("rep-gross-sales").textContent = `₹ ${s.gross_sales.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-sales-returns").textContent = `- ₹ ${s.sales_refunds.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-net-revenue").textContent = `₹ ${s.net_sales_revenue.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-purchases").textContent = `₹ ${s.net_purchases.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-cogs").textContent = `₹ ${s.cogs.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-gross-profit").textContent = `₹ ${s.gross_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-gross-margin").textContent = `${s.gross_margin_percent}% Margin`;
      document.getElementById("rep-expenses").textContent = `- ₹ ${s.total_expenses.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("rep-net-profit").textContent = `₹ ${s.net_profit.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;

      // Update GST Breakdown
      const gst = data.gst_summary;
      document.getElementById("rep-gst-output").textContent = `₹ ${gst.output_tax.total.toFixed(2)}`;
      document.getElementById("rep-gst-cgst").textContent = `₹ ${gst.output_tax.cgst.toFixed(2)}`;
      document.getElementById("rep-gst-sgst").textContent = `₹ ${gst.output_tax.sgst.toFixed(2)}`;
      document.getElementById("rep-gst-itc").textContent = `₹ ${gst.input_tax_credit.total.toFixed(2)}`;
      document.getElementById("rep-gst-payable").textContent = `₹ ${gst.net_payable_gst.toFixed(2)}`;

      // Update Top Selling Medicines
      const topTbody = document.getElementById("rep-top-sellers-tbody");
      if (topTbody) {
        if (!data.best_sellers || data.best_sellers.length === 0) {
          topTbody.innerHTML = `<tr><td colspan="3" style="text-align:center; padding:15px; color:#94a3b8;">No sales recorded in selected period.</td></tr>`;
        } else {
          topTbody.innerHTML = data.best_sellers.map(b => `
            <tr>
              <td><b>${b.medicine_name}</b></td>
              <td><b>${b.units_sold} units</b></td>
              <td><b>₹ ${b.revenue.toFixed(2)}</b></td>
            </tr>
          `).join("");
        }
      }

      // Update Payment Methods breakdown
      const payList = document.getElementById("rep-payment-methods-list");
      if (payList) {
        const pm = data.payment_methods;
        payList.innerHTML = Object.keys(pm).map(method => `
          <div style="display:flex; justify-content:space-between; padding:8px 0; border-bottom:1px solid #f1f5f9;">
            <span style="font-weight:600; font-size:13px;">${method}</span>
            <span style="font-weight:700; color:#0f766e;">₹ ${pm[method].toFixed(2)}</span>
          </div>
        `).join("");
      }
    } catch (err) {
      App.showToast("Failed to load reports: " + err.message, "error");
    }
  }
};
