// ===== SIDEBAR TOGGLE =====
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.querySelector('.sidebar');
if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', (e) => {
    if (window.innerWidth <= 992) {
        if (sidebar && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// ===== SEARCH FUNCTIONALITY =====
const userSearch = document.getElementById('userSearch');
const usersTable = document.getElementById('usersTable');
if (userSearch && usersTable) {
    userSearch.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const rows = usersTable.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

// Log search functionality
const logSearch = document.getElementById('logSearch');
const logsTable = document.getElementById('logsTable');
if (logSearch && logsTable) {
    logSearch.addEventListener('input', (e) => {
        const searchTerm = e.target.value.toLowerCase();
        const rows = logsTable.querySelectorAll('tbody tr');

        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(searchTerm) ? '' : 'none';
        });
    });
}

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        const href = this.getAttribute('href');
        if (href !== '#') {
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        }
    });
});

// ===== ANIMATION ON SCROLL =====
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate-fade-in');
        }
    });
}, observerOptions);

document.querySelectorAll('.animate-on-scroll').forEach(el => {
    observer.observe(el);
});

// ===== CONFIRMATION DIALOGS =====
document.querySelectorAll('[onclick*="confirm"]').forEach(btn => {
    btn.addEventListener('click', (e) => {
        const message = btn.getAttribute('onclick').match(/confirm\('(.+?)'\)/);
        if (message && message[1]) {
            if (!confirm(message[1])) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });
});

// ===== CHART INITIALIZATION (Analytics Page) =====
const activityChart = document.getElementById('activityChart');
if (activityChart) {
    const ctx = activityChart.getContext('2d');

    const chartData = {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'Users',
            data: [65, 59, 80, 81, 56, 55, 40, 70, 85, 90, 95, 100],
            borderColor: '#00c896',
            backgroundColor: 'rgba(0, 200, 150, 0.1)',
            tension: 0.4,
            fill: true
        }, {
            label: 'Workouts',
            data: [28, 48, 40, 19, 86, 27, 90, 100, 115, 120, 130, 140],
            borderColor: '#00b4d8',
            backgroundColor: 'rgba(0, 180, 216, 0.1)',
            tension: 0.4,
            fill: true
        }]
    };

    const chartConfig = {
        type: 'line',
        data: chartData,
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 12
                        }
                    }
                },
                tooltip: {
                    backgroundColor: '#1f2d2a',
                    titleFont: {
                        family: "'Poppins', sans-serif",
                        size: 13
                    },
                    bodyFont: {
                        family: "'Poppins', sans-serif",
                        size: 12
                    },
                    padding: 12,
                    cornerRadius: 8,
                    displayColors: true
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 200, 150, 0.1)'
                    },
                    ticks: {
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 11
                        },
                        color: '#666'
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        font: {
                            family: "'Poppins', sans-serif",
                            size: 11
                        },
                        color: '#666'
                    }
                }
            },
            interaction: {
                intersect: false,
                mode: 'index'
            }
        }
    };

    new Chart(ctx, chartConfig);
}

// ===== STATS COUNTER ANIMATION =====
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = target.toLocaleString();
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(start).toLocaleString();
        }
    }, 16);
}

// Animate stat numbers on page load
document.addEventListener('DOMContentLoaded', () => {
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        const target = parseInt(stat.textContent.replace(/,/g, ''));
        if (!isNaN(target)) {
            stat.textContent = '0';
            animateCounter(stat, target);
        }
    });
});

// ===== TOGGLE SWITCH ANIMATION =====
document.querySelectorAll('.toggle-switch input').forEach(toggle => {
    toggle.addEventListener('change', (e) => {
        const label = e.target.nextElementSibling;
        if (label) {
            label.style.transform = e.target.checked ? 'translateX(30px)' : 'translateX(0)';
        }
    });
});

// ===== ALERT AUTO-DISMISS =====
document.querySelectorAll('.alert').forEach(alert => {
    const dismissTimer = setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
    }, 5000); // Auto-dismiss after 5 seconds

    // Clear timer if manually closed
    alert.addEventListener('close.bs.alert', () => {
        clearTimeout(dismissTimer);
    });
});

// ===== NAVIGATION ACTIVE STATE =====
document.querySelectorAll('.nav-item').forEach(navItem => {
    navItem.addEventListener('click', function () {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
    });
});

// ===== TABLE ROW HIGHLIGHT =====
document.querySelectorAll('.data-table tbody tr').forEach(row => {
    row.addEventListener('mouseenter', function () {
        this.style.transform = 'scale(1.01)';
    });
    row.addEventListener('mouseleave', function () {
        this.style.transform = 'scale(1)';
    });
});

// ===== EXPORT FUNCTIONALITY =====
const exportBtn = document.querySelector('button[onclick*="export"], button:contains("Export")');
if (exportBtn) {
    exportBtn.addEventListener('click', () => {
        // Sample export functionality
        const table = document.querySelector('.data-table');
        if (table) {
            let csv = [];
            const rows = table.querySelectorAll('tr');
            rows.forEach(row => {
                const cols = row.querySelectorAll('th, td');
                const rowData = [];
                cols.forEach(col => {
                    rowData.push('"' + col.textContent.trim() + '"');
                });
                csv.push(rowData.join(','));
            });

            const csvFile = new Blob([csv.join('\n')], { type: 'text/csv' });
            const downloadLink = document.createElement('a');
            downloadLink.download = 'export_data.csv';
            downloadLink.href = window.URL.createObjectURL(csvFile);
            downloadLink.click();
        }
    });
}

// ✅ FIXED: LOADING STATE FOR BUTTONS (Exclude delete buttons)
document.querySelectorAll('form button[type="submit"]:not(.btn-danger):not([onclick*="delete"])').forEach(button => {
    button.addEventListener('click', function (e) {
        const form = this.closest('form');
        if (form && form.checkValidity()) {
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';

            // Re-enable after 3 seconds (prevent permanent disable if form fails)
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = originalText;
            }, 3000);
        }
    });
});

// ===== SESSION TIMEOUT WARNING =====
let sessionTimer;
const sessionTimeout = 30 * 60 * 1000; // 30 minutes

function resetSessionTimer() {
    clearTimeout(sessionTimer);
    sessionTimer = setTimeout(() => {
        if (confirm('Your session is about to expire. Stay logged in?')) {
            // Make AJAX call to extend session
            resetSessionTimer();
        } else {
            window.location.href = '/auth/logout';
        }
    }, sessionTimeout);
}

// Reset timer on user activity
['mousedown', 'keydown', 'scroll', 'touchstart'].forEach(event => {
    document.addEventListener(event, resetSessionTimer, true);
});

// Initialize session timer
resetSessionTimer();

// ===== CONSOLE LOG =====
console.log('🚀 SmartFit Admin Panel Loaded Successfully!');
console.log('📊 Charts:', activityChart ? 'Initialized' : 'Not found');
console.log('🔍 Search:', userSearch ? 'Active' : 'Not found');
console.log('📱 Responsive:', sidebar ? 'Enabled' : 'Not found');