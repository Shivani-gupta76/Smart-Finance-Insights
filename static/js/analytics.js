/* =========================================================
   Analytics Dashboard — Chart.js Visualizations (Rebuilt)
========================================================= */

document.addEventListener("DOMContentLoaded", function () {
    if (!window.analyticsData) return;

    const data = window.analyticsData;

    // FinSight Color Palette
    const palette = [
        "#2563EB", "#16A34A", "#D97706", "#9333EA", "#06B6D4",
        "#EC4899", "#8B5CF6", "#F59E0B", "#10B981", "#6366F1"
    ];

    // 1. Spending Pattern Analysis (Doughnut Chart)
    const categoryCtx = document.getElementById("categoryChart");
    if (categoryCtx && data.categories && data.categories.length > 0) {
        new Chart(categoryCtx, {
            type: "doughnut",
            data: {
                labels: data.categories,
                datasets: [{
                    data: data.categoryAmounts,
                    backgroundColor: palette.slice(0, data.categories.length),
                    borderWidth: 2,
                    borderColor: "#ffffff"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { font: { family: "Poppins", size: 12 } }
                    },
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

    // 2. Cash Flow Trend — Last 6 Months (Line Chart)
    const cashFlowCtx = document.getElementById("cashFlowChart");
    if (cashFlowCtx && data.trendLabels && data.trendLabels.length > 0) {
        new Chart(cashFlowCtx, {
            type: "line",
            data: {
                labels: data.trendLabels,
                datasets: [
                    {
                        label: "Income (₹)",
                        data: data.trendIncome,
                        borderColor: "#16A34A",
                        backgroundColor: "rgba(22, 163, 74, 0.08)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: "Expenses (₹)",
                        data: data.trendExpenses,
                        borderColor: "#DC2626",
                        backgroundColor: "rgba(220, 38, 38, 0.08)",
                        borderWidth: 2.5,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: "Savings (₹)",
                        data: data.trendSavings,
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
                    legend: {
                        position: "top",
                        labels: { font: { family: "Poppins", size: 12 } }
                    },
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
                        ticks: {
                            font: { family: "Poppins" },
                            callback: function (val) {
                                return "₹" + val.toLocaleString();
                            }
                        }
                    },
                    x: {
                        ticks: { font: { family: "Poppins" } }
                    }
                }
            }
        });
    }
});
