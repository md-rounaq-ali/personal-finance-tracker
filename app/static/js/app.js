/* ============================================================
   FinTrack — App JavaScript
   Chart.js rendering, animations, interactions
   ============================================================ */

// --- Sidebar Toggle (Mobile & Tablet) ---
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebarOverlay');
    if (!sidebar || !overlay) return;
    sidebar.classList.toggle('open');
    overlay.classList.toggle('show');
}

// Close sidebar on ESC key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebarOverlay');
        if (sidebar && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            if (overlay) overlay.classList.remove('show');
        }
    }
});

// Auto-close sidebar on mobile/tablet when a nav link is tapped
document.addEventListener('DOMContentLoaded', () => {
    const navLinks = document.querySelectorAll('.sidebar-nav .nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 1024) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebarOverlay');
                if (sidebar) sidebar.classList.remove('open');
                if (overlay) overlay.classList.remove('show');
            }
        });
    });
});

// --- Flash Messages Auto-dismiss ---
document.addEventListener('DOMContentLoaded', () => {
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach((msg, i) => {
        setTimeout(() => {
            msg.style.opacity = '0';
            msg.style.transform = 'translateX(20px)';
            setTimeout(() => msg.remove(), 300);
        }, 4000 + i * 500);
    });
});

// --- Chart.js Defaults ---
if (typeof Chart !== 'undefined') {
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
}

// --- Create Doughnut Chart ---
function createDoughnutChart(canvasId, labels, data, colors) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors,
                borderColor: 'rgba(15, 23, 42, 0.8)',
                borderWidth: 2,
                hoverBorderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { padding: 14, font: { size: 11.5 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    borderWidth: 1,
                    titleFont: { weight: '600' },
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((context.parsed / total) * 100).toFixed(1);
                            return ` ₹${context.parsed.toLocaleString('en-IN')} (${pct}%)`;
                        }
                    }
                }
            },
            animation: { animateRotate: true, duration: 1000 }
        }
    });
}

// --- Create Bar Chart ---
function createBarChart(canvasId, labels, incomeData, expenseData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Income',
                    data: incomeData,
                    backgroundColor: 'rgba(16, 185, 129, 0.7)',
                    borderColor: '#10b981',
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false
                },
                {
                    label: 'Expenses',
                    data: expenseData,
                    backgroundColor: 'rgba(244, 63, 94, 0.7)',
                    borderColor: '#f43f5e',
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            plugins: {
                legend: { position: 'top' },
                tooltip: {
                    backgroundColor: 'rgba(30, 41, 59, 0.95)',
                    borderColor: 'rgba(148, 163, 184, 0.2)',
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                    callbacks: {
                        label: function(context) {
                            return ` ${context.dataset.label}: ₹${context.parsed.y.toLocaleString('en-IN')}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: { font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(148, 163, 184, 0.06)' },
                    ticks: {
                        font: { size: 11 },
                        callback: function(value) {
                            if (value >= 100000) return '₹' + (value / 100000).toFixed(1) + 'L';
                            if (value >= 1000) return '₹' + (value / 1000).toFixed(0) + 'K';
                            return '₹' + value;
                        }
                    }
                }
            },
            animation: { duration: 800, easing: 'easeOutQuart' }
        }
    });
}

// --- Confirm Delete ---
document.addEventListener('DOMContentLoaded', () => {
    // Add staggered animation to table rows
    document.querySelectorAll('.fade-in').forEach((el, i) => {
        el.style.animationDelay = `${i * 0.04}s`;
    });
});
