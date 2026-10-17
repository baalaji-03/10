/**
 * Dashboard & Analytics Controller
 */

let salesChartInstance = null;

const Dashboard = {
  async load() {
    try {
      const stats = await API.get("/api/dashboard/stats");

      // Update KPIs
      document.getElementById("kpi-today-sales").textContent = `₹ ${stats.today_sales.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("kpi-today-bills").textContent = `${stats.today_bills_count} Bills Today`;
      document.getElementById("kpi-gross-profit").textContent = `₹ ${stats.estimated_gross_profit_today.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("kpi-total-meds").textContent = stats.total_medicines;
      document.getElementById("kpi-available-stock").textContent = `${stats.total_available_stock} Units in Stock`;
      document.getElementById("kpi-customers").textContent = stats.registered_customers;
      document.getElementById("kpi-today-purchases").textContent = `₹ ${stats.today_purchases.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
      document.getElementById("kpi-low-stock").textContent = stats.low_stock_count;
      document.getElementById("kpi-near-expiry").textContent = stats.near_expiry_count;
      document.getElementById("kpi-expired").textContent = stats.expired_count;

      // Update Sidebar Badges
      const nearExpBadge = document.getElementById("badge-near-expiry");
      const lowStockBadge = document.getElementById("badge-low-stock");
      if (nearExpBadge) nearExpBadge.textContent = stats.near_expiry_count + stats.expired_count;
      if (lowStockBadge) lowStockBadge.textContent = stats.low_stock_count;

      // Render Chart.js Chart
      this.renderChart(stats.monthly_chart);

      // Render Recent Transactions
      this.renderRecentTransactions(stats.recent_transactions);

      // Render Recent Notifications
      this.renderRecentNotifications(stats.recent_notifications);
    } catch (err) {
      console.error("Failed to load dashboard stats:", err);
      App.showToast("Failed to load dashboard data: " + err.message, "error");
    }
  },

  renderChart(chartData) {
    const ctx = document.getElementById("monthlySalesChart");
    if (!ctx) return;

    if (salesChartInstance) {
      salesChartInstance.destroy();
    }

    salesChartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            label: "Sales Revenue (₹)",
            data: chartData.sales,
            backgroundColor: "rgba(15, 118, 110, 0.85)",
            borderColor: "#0f766e",
            borderRadius: 6,
            borderWidth: 1
          },
          {
            label: "Purchases (₹)",
            data: chartData.purchases,
            backgroundColor: "rgba(99, 102, 241, 0.75)",
            borderColor: "#6366f1",
            borderRadius: 6,
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              boxWidth: 14,
              font: { family: "'Inter', sans-serif", size: 12, weight: 600 }
            }
          },
          tooltip: {
            callbacks: {
              label: (context) => ` ${context.dataset.label}: ₹${Number(context.raw).toLocaleString('en-IN')}`
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            ticks: {
              callback: (val) => "₹" + Number(val).toLocaleString('en-IN')
            },
            grid: { color: "#f1f5f9" }
          },
          x: {
            grid: { display: false }
          }
        }
      }
    });
  },

  renderRecentTransactions(txs) {
    const tbody = document.getElementById("recent-transactions-tbody");
    if (!tbody) return;

    if (!txs || txs.length === 0) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-center" style="padding:20px; color:#94a3b8;">No recent sales transactions recorded today.</td></tr>`;
      return;
    }

    tbody.innerHTML = txs.map(t => `
      <tr>
        <td><b>${t.invoice_number}</b></td>
        <td>${t.customer_name}</td>
        <td>${t.date}</td>
        <td><span class="badge badge-blue">${t.payment_method}</span></td>
        <td><b>₹ ${t.amount.toFixed(2)}</b></td>
        <td>
          <button class="btn btn-secondary btn-sm" onclick="Invoices.viewInvoice(${t.id})">
            Reprint / View
          </button>
        </td>
      </tr>
    `).join("");
  },

  renderRecentNotifications(notifs) {
    const container = document.getElementById("recent-notifications-list");
    if (!container) return;

    if (!notifs || notifs.length === 0) {
      container.innerHTML = `<div style="padding:15px; text-align:center; color:#94a3b8;">No recent alerts or logs.</div>`;
      return;
    }

    container.innerHTML = notifs.map(n => `
      <div style="padding:10px 12px; border-bottom:1px solid #e2e8f0; display:flex; justify-content:space-between; align-items:center;">
        <div>
          <div style="font-weight:600; font-size:12.5px;">${n.subject || n.type}</div>
          <div style="font-size:11px; color:#64748b;">${n.sent_at}</div>
        </div>
        <span class="badge ${n.status === 'SENT' ? 'badge-green' : 'badge-red'}">${n.status}</span>
      </div>
    `).join("");
  }
};
