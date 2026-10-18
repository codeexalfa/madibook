// MediBook Admin Dashboard Logic
// Renders Chart.js visualization, KPI metrics, and department table

let chartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
    // Role protection: Admin only
    requireAuth("admin");
    setupUserNav();
    loadAdminStats();
});

function setupUserNav() {
    const user = getCurrentUser();
    const container = document.getElementById("nav-user-container");
    if (container && user) {
        container.innerHTML = `
            <span class="user-badge" style="background:#fee2e2; color:#991b1b;">ADMIN</span>
            <span style="font-size: 0.9rem; color: #475569; margin: 0 0.5rem;">${user.email || user.name || "Administrator"}</span>
            <button onclick="authSignOut()" class="btn btn-secondary btn-sm">Log Out</button>
        `;
    }
}

async function loadAdminStats() {
    try {
        let stats = null;

        if (!CONFIG.API_URL || CONFIG.API_URL.includes("YOUR_")) {
            // Local preview sample metrics
            stats = {
                totalAppointments: 24,
                confirmedCount: 19,
                noShowCount: 3,
                cancelledCount: 2,
                noShowRate: "12.5%",
                busiestDay: "Monday",
                busiestDayCount: 8,
                bookingsPerDepartment: {
                    "Cardiology": 6,
                    "Neurology": 5,
                    "Pediatrics": 5,
                    "Orthopedics": 5,
                    "Dermatology": 3
                },
                departmentTable: [
                    { department: "Cardiology", bookings: 6, percentage: "25.0%" },
                    { department: "Neurology", bookings: 5, percentage: "20.8%" },
                    { department: "Pediatrics", bookings: 5, percentage: "20.8%" },
                    { department: "Orthopedics", bookings: 5, percentage: "20.8%" },
                    { department: "Dermatology", bookings: 3, percentage: "12.5%" }
                ]
            };
        } else {
            stats = await apiGetAdminStats();
        }

        renderMetrics(stats);
        renderChart(stats.bookingsPerDepartment || {});
        renderTable(stats.departmentTable || []);

    } catch (err) {
        console.error("Failed to load admin stats:", err);
        alert(`Failed to load admin metrics: ${err.message}`);
    }
}

// 1. Render KPI Summary Cards
function renderMetrics(stats) {
    document.getElementById("stat-total").textContent = stats.totalAppointments || "0";
    document.getElementById("stat-noshow").textContent = stats.noShowRate || "0%";
    document.getElementById("stat-noshow-sub").textContent = `${stats.noShowCount || 0} missed visits`;
    document.getElementById("stat-busiest").textContent = stats.busiestDay || "N/A";
    document.getElementById("stat-busiest-sub").textContent = stats.busiestDayCount ? `${stats.busiestDayCount} appointments` : "Peak day";
    document.getElementById("stat-confirmed").textContent = stats.confirmedCount || "0";
    document.getElementById("stat-confirmed-sub").textContent = `${stats.cancelledCount || 0} cancelled`;
}

// 2. Render Chart.js Bar Chart
function renderChart(deptMap) {
    const canvas = document.getElementById("departmentChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    const labels = Object.keys(deptMap);
    const dataValues = Object.values(deptMap);

    // Color palette for departments
    const backgroundColors = [
        "rgba(2, 132, 199, 0.8)",   // Medical Sky Blue
        "rgba(16, 185, 129, 0.8)",  // Health Emerald
        "rgba(139, 92, 246, 0.8)",  // Violet
        "rgba(245, 158, 11, 0.8)",  // Amber
        "rgba(6, 182, 212, 0.8)"    // Cyan
    ];

    const borderColors = [
        "#0284c7",
        "#10b981",
        "#8b5cf6",
        "#f59e0b",
        "#06b6d4"
    ];

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: "bar",
        data: {
            labels: labels,
            datasets: [{
                label: "Number of Bookings",
                data: dataValues,
                backgroundColor: backgroundColors.slice(0, labels.length),
                borderColor: borderColors.slice(0, labels.length),
                borderWidth: 1.5,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` ${context.raw} patient appointments`;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        stepSize: 1,
                        precision: 0
                    },
                    grid: {
                        color: "#f1f5f9"
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

// 3. Render Department Table
function renderTable(tableRows) {
    const tbody = document.getElementById("department-table-tbody");
    if (!tbody) return;

    if (!tableRows || tableRows.length === 0) {
        tbody.innerHTML = `<tr><td colspan="4" style="text-align: center; color: #64748b; padding: 2rem;">No department data available.</td></tr>`;
        return;
    }

    let rowsHtml = "";
    tableRows.forEach(row => {
        rowsHtml += `
            <tr>
                <td><strong>🏥 ${row.department}</strong></td>
                <td>${row.bookings}</td>
                <td>${row.percentage}</td>
                <td>
                    <span class="badge" style="background:#e0f2fe; color:#0369a1;">ACTIVE</span>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = rowsHtml;
}
