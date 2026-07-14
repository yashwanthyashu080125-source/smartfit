// ===== MOBILE SIDEBAR TOGGLE =====
function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    if (sidebar) {
        sidebar.classList.toggle('active');
    }
}

// Close sidebar when clicking outside on mobile
document.addEventListener('click', function(event) {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.querySelector('.mobile-toggle');

    if (window.innerWidth <= 992) {
        if (sidebar && toggle && !sidebar.contains(event.target) && !toggle.contains(event.target)) {
            sidebar.classList.remove('active');
        }
    }
});

// ===== ANIMATE PROGRESS BARS ON LOAD =====
window.addEventListener('load', function() {
    const progressBars = document.querySelectorAll('.progress-bar');
    progressBars.forEach(bar => {
        const width = bar.style.width;
        bar.style.width = '0';
        setTimeout(() => {
            bar.style.width = width;
        }, 300);
    });
});

// ===== AUTO-HIDE ALERTS =====
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        const dismissTimer = setTimeout(() => {
            if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } else {
                alert.style.opacity = '0';
                alert.style.transition = 'opacity 0.3s ease';
                setTimeout(() => alert.remove(), 300);
            }
        }, 5000);

        // Clear timer if manually closed
        alert.addEventListener('close.bs.alert', () => {
            clearTimeout(dismissTimer);
        });
    });
});

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
    const statNumbers = document.querySelectorAll('.stat-number, .stat-value');
    statNumbers.forEach(stat => {
        const target = parseInt(stat.textContent.replace(/,/g, ''));
        if (!isNaN(target) && target > 0) {
            stat.textContent = '0';
            animateCounter(stat, target);
        }
    });
});

// ===== SMOOTH SCROLL =====
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
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

// ===== NAVIGATION ACTIVE STATE =====
document.querySelectorAll('.nav-item').forEach(navItem => {
    navItem.addEventListener('click', function() {
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        this.classList.add('active');
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

// ===== LOADING STATE FOR BUTTONS =====
document.querySelectorAll('form button[type="submit"]:not(.btn-danger):not([onclick*="delete"])').forEach(button => {
    button.addEventListener('click', function(e) {
        const form = this.closest('form');
        if (form && form.checkValidity()) {
            const originalText = button.innerHTML;
            // Use a slight delay to allow form submission to trigger
            setTimeout(() => {
                button.disabled = true;
                button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            }, 0);

            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = originalText;
            }, 3000);
        }
    });
});

// ===== TABLE ROW HIGHLIGHT =====
document.querySelectorAll('table tbody tr').forEach(row => {
    row.addEventListener('mouseenter', function() {
        this.style.transform = 'scale(1.01)';
        this.style.transition = 'transform 0.2s ease';
    });
    row.addEventListener('mouseleave', function() {
        this.style.transform = 'scale(1)';
    });
});

// ===== CONSOLE LOG =====
console.log('🚀 SmartFit Dashboard Loaded Successfully!');
console.log('📊 Animations: Enabled');
console.log('📱 Responsive: Enabled');

// ===== DASHBOARD INITIALIZATION =====
function initDashboard() {
    console.log('🏠 Dashboard Initialized');
}