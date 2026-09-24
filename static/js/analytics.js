/* =========================================================
   Analytics Dashboard — Chart.js Visualizations (Multi-Tab & Goal-Expense)
========================================================= */

window.chartInstances = {};

function initOrUpdateAnalyticsCharts() {
    if (!window.analyticsData || !window.Chart) return;

    const data = window.analyticsData;

    function getChartThemeColors() {
        const isDark = document.documentElement.getAttribute('data-rendered-theme') === 'dark';
        return {
            textColor: isDark ? '#f9fafb' : '#334155',
            gridColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)',
            borderColor: isDark ? '#1f2937' : '#ffffff'
        };
    }

    const tc = getChartThemeColors();
    Chart.defaults.color = tc.textColor;
    Chart.defaults.borderColor = tc.gridColor;

    const palette = [
        "#2563EB", "#16A34A", "#D97706", "#9333EA", "#06B6D4",
        "#EC4899", "#8B5CF6", "#F59E0B", "#10B981", "#6366F1"
    ];

    function getLineChartConfig(labels, income, expenses, savings) {
        return {
            type: "line",
            data: {
                labels: labels,
                datasets: [
                    {
                        label: "Income (₹)",
                        data: income,
                        borderColor: "#16A34A",
                        backgroundColor: "rgba(22, 163, 74, 0.08)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: "Expenses (₹)",
                        data: expenses,
                        borderColor: "#DC2626",
                        backgroundColor: "rgba(220, 38, 38, 0.08)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: "Savings (₹)",
                        data: savings,
                        borderColor: "#2563EB",
                        backgroundColor: "rgba(37, 99, 235, 0.08)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top", labels: { font: { size: 12 } } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` ${ctx.dataset.label}: ₹${ctx.raw.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: function (val) { return "₹" + val.toLocaleString(); } }
                    }
                }
            }
        };
    }

    // 1. Overview Tab Cash Flow Line Chart
    const overviewCashCtx = document.getElementById("overviewCashFlowChart");
    if (overviewCashCtx && data.trendLabels && !window.chartInstances.overviewCash) {
        window.chartInstances.overviewCash = new Chart(overviewCashCtx, getLineChartConfig(data.trendLabels, data.trendIncome, data.trendExpenses, data.trendSavings));
    }

    // 2. Spending Analysis Tab Doughnut Chart
    const doughnutCtx = document.getElementById("categoryDoughnutChart");
    if (doughnutCtx && !window.chartInstances.categoryDoughnut) {
        const initCategories = (data.spendingPeriods && data.spendingPeriods.this_month && data.spendingPeriods.this_month.categories) ? data.spendingPeriods.this_month.categories : (data.categories || []);
        const initAmounts = (data.spendingPeriods && data.spendingPeriods.this_month && data.spendingPeriods.this_month.amounts) ? data.spendingPeriods.this_month.amounts : (data.categoryAmounts || []);

        window.chartInstances.categoryDoughnut = new Chart(doughnutCtx, {
            type: "doughnut",
            data: {
                labels: initCategories,
                datasets: [{
                    data: initAmounts,
                    backgroundColor: palette.slice(0, initCategories.length),
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { font: { size: 12 } } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` ${ctx.label}: ₹${ctx.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // 3. Goal-Related Expenses by Goal (Bar Chart)
    const goalExpCtx = document.getElementById("goalExpensesChart");
    if (goalExpCtx && data.goalNames && data.goalNames.length > 0 && !window.chartInstances.goalExpenses) {
        window.chartInstances.goalExpenses = new Chart(goalExpCtx, {
            type: "bar",
            data: {
                labels: data.goalNames,
                datasets: [{
                    label: "Total Goal Expenses (₹)",
                    data: data.goalLinkedTotals,
                    backgroundColor: palette.slice(0, data.goalNames.length),
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` Linked Expenses: ₹${ctx.raw.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: function (val) { return "₹" + val.toLocaleString(); } }
                    }
                }
            }
        });
    }

    // 4. Expense Distribution (Goal-Linked vs Regular Doughnut Chart)
    const goalVsRegCtx = document.getElementById("goalVsRegularChart");
    if (goalVsRegCtx && !window.chartInstances.goalVsRegular) {
        window.chartInstances.goalVsRegular = new Chart(goalVsRegCtx, {
            type: "doughnut",
            data: {
                labels: ["Goal-Linked Expenses", "Regular Expenses"],
                datasets: [{
                    data: [data.totalGoalLinked || 0, data.totalRegularExpenses || 0],
                    backgroundColor: ["#2563EB", "#94A3B8"],
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "bottom", labels: { font: { size: 12 } } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` ${ctx.label}: ₹${ctx.raw.toLocaleString()}`;
                            }
                        }
                    }
                }
            }
        });
    }

    // 5. Monthly Goal-Linked Expense Trend Line Chart
    const monthlyGoalTrendCtx = document.getElementById("monthlyGoalExpenseTrendChart");
    if (monthlyGoalTrendCtx && data.monthlyGoalTrendLabels && !window.chartInstances.monthlyGoalTrend) {
        window.chartInstances.monthlyGoalTrend = new Chart(monthlyGoalTrendCtx, {
            type: "line",
            data: {
                labels: data.monthlyGoalTrendLabels,
                datasets: [{
                    label: "Monthly Goal-Linked Expenses (₹)",
                    data: data.monthlyGoalTrendAmounts,
                    borderColor: "#2563EB",
                    backgroundColor: "rgba(37, 99, 235, 0.1)",
                    borderWidth: 2.5,
                    tension: 0.3,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: "top", labels: { font: { size: 12 } } },
                    tooltip: {
                        callbacks: {
                            label: function (ctx) {
                                return ` Goal Expenses: ₹${ctx.raw.toLocaleString()}`;
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { callback: function (val) { return "₹" + val.toLocaleString(); } }
                    }
                }
            }
        });
    }
}

window.selectSpendingPeriod = function(periodKey) {
    if (!window.analyticsData) return;
    const data = window.analyticsData;
    if (!data.spendingPeriods || !data.spendingPeriods[periodKey]) return;

    document.querySelectorAll("#tab-spending .filter-btn").forEach(btn => {
        btn.classList.remove("active");
        if (btn.getAttribute("onclick") && btn.getAttribute("onclick").includes(periodKey)) {
            btn.classList.add("active");
        }
    });

    const periodData = data.spendingPeriods[periodKey];
    const categories = periodData.categories || [];
    const amounts = periodData.amounts || [];
    const totalExp = periodData.total_expenses || 0;
    const palette = [
        "#2563EB", "#16A34A", "#D97706", "#9333EA", "#06B6D4",
        "#EC4899", "#8B5CF6", "#F59E0B", "#10B981", "#6366F1"
    ];

    if (window.chartInstances && window.chartInstances.categoryDoughnut) {
        window.chartInstances.categoryDoughnut.data.labels = categories;
        window.chartInstances.categoryDoughnut.data.datasets[0].data = amounts;
        window.chartInstances.categoryDoughnut.data.datasets[0].backgroundColor = palette.slice(0, categories.length);
        window.chartInstances.categoryDoughnut.update();
    }

    const tbody = document.getElementById("spendingCategoryTableBody");
    if (tbody) {
        if (categories.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" style="text-align:center; color:#94A3B8; padding:20px;">No expense records found for this period.</td></tr>';
        } else {
            let html = '';
            categories.forEach((cat, idx) => {
                const amt = amounts[idx] || 0;
                const pct = totalExp > 0 ? ((amt / totalExp) * 100).toFixed(1) : 0;
                html += `<tr>
                    <td><strong>${cat}</strong></td>
                    <td>₹${amt.toLocaleString()}</td>
                    <td>${pct}%</td>
                </tr>`;
            });
            tbody.innerHTML = html;
        }
    }
};

window.renderOrResizeCharts = function(tabName) {
    initOrUpdateAnalyticsCharts();
    setTimeout(function() {
        Object.values(window.chartInstances || {}).forEach(chart => {
            if (chart && typeof chart.resize === 'function') {
                chart.resize();
            }
        });
    }, 50);
};

document.addEventListener("DOMContentLoaded", function () {
    initOrUpdateAnalyticsCharts();
});
