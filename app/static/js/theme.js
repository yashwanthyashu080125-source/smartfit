/**
 * SmartFit — Global Theme & Interaction Script
 * Dark Theme | Scroll Reveal | Micro-interactions
 */

document.addEventListener('DOMContentLoaded', function () {

    // =============================
    // SCROLL REVEAL (IntersectionObserver)
    // =============================
    const revealObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                revealObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.12 });

    document.querySelectorAll('.reveal').forEach(el => revealObserver.observe(el));

    // =============================
    // NAVBAR SCROLL EFFECT
    // =============================
    const navbar = document.querySelector('.premium-navbar');
    if (navbar) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 30) {
                navbar.style.background = 'rgba(255, 255, 255, 0.98)';
                navbar.style.boxShadow = '0 2px 20px rgba(0,0,0,0.08)';
            } else {
                navbar.style.background = 'rgba(255, 255, 255, 0.88)';
                navbar.style.boxShadow = '0 2px 16px rgba(0,0,0,0.06)';
            }
        }, { passive: true });
    }

    // =============================
    // TILT EFFECT ON FEAT CARDS
    // =============================
    document.querySelectorAll('.feat-card, .m-card, .hcard').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width - 0.5) * 12;
            const y = ((e.clientY - rect.top) / rect.height - 0.5) * -10;
            card.style.transform = `rotateY(${x}deg) rotateX(${y}deg) translateY(-10px)`;
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
        });
    });

    // =============================
    // SMOOTH ANCHOR SCROLL
    // =============================
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const href = this.getAttribute('href');
            if (href === '#' || href.startsWith('http')) return;
            e.preventDefault();
            const target = document.querySelector(href);
            if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // =============================
    // FORM FOCUS GLOW EFFECT
    // =============================
    document.querySelectorAll('input, textarea, select').forEach(input => {
        input.addEventListener('focus', function () {
            this.style.borderColor = 'rgba(249, 115, 22, 0.5)';
            this.style.boxShadow  = '0 0 0 3px rgba(249, 115, 22, 0.08)';
        });
        input.addEventListener('blur', function () {
            this.style.borderColor = '';
            this.style.boxShadow  = '';
        });
    });

    // =============================
    // BUTTON RIPPLE EFFECT
    // =============================
    document.querySelectorAll('.btn-primary, .btn-register, .btn-hero-primary, .btn-submit-glow').forEach(btn => {
        btn.addEventListener('click', function (e) {
            const circle = document.createElement('span');
            const diameter = Math.max(this.clientWidth, this.clientHeight);
            const radius = diameter / 2;
            const rect = this.getBoundingClientRect();

            circle.style.cssText = `
                position: absolute;
                width: ${diameter}px;
                height: ${diameter}px;
                left: ${e.clientX - rect.left - radius}px;
                top: ${e.clientY - rect.top - radius}px;
                background: rgba(255,255,255,0.25);
                border-radius: 50%;
                pointer-events: none;
                transform: scale(0);
                animation: ripple 0.55s linear;
            `;

            const existing = this.querySelector('.ripple-effect');
            if (existing) existing.remove();

            circle.classList.add('ripple-effect');
            this.style.position = 'relative';
            this.style.overflow = 'hidden';
            this.appendChild(circle);
            setTimeout(() => circle.remove(), 600);
        });
    });

    // Inject ripple keyframes
    const rippleStyle = document.createElement('style');
    rippleStyle.textContent = `
        @keyframes ripple {
            to { transform: scale(4); opacity: 0; }
        }
        @keyframes slideInNotif {
            from { transform: translateX(110%); opacity: 0; }
            to   { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutNotif {
            to { transform: translateX(110%); opacity: 0; }
        }
    `;
    document.head.appendChild(rippleStyle);

    // =============================
    // NOTIFICATION TOAST SYSTEM
    // =============================
    function showToast(message, type = 'info') {
        const existing = document.querySelector('.sf-toast');
        if (existing) existing.remove();

        const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
        const colors = {
            success: { bg: 'rgba(240,253,244,0.98)', border: 'rgba(16,185,129,0.35)',  text: '#065f46' },
            error:   { bg: 'rgba(254,242,242,0.98)', border: 'rgba(239,68,68,0.3)',    text: '#991b1b' },
            warning: { bg: 'rgba(255,251,235,0.98)', border: 'rgba(245,158,11,0.3)',   text: '#92400e' },
            info:    { bg: 'rgba(255,247,237,0.98)', border: 'rgba(249,115,22,0.3)',   text: '#c2410c' },
        };

        const c = colors[type] || colors.info;
        const toast = document.createElement('div');
        toast.className = 'sf-toast';
        toast.style.cssText = `
            position: fixed;
            top: 90px; right: 20px;
            padding: 14px 22px;
            background: ${c.bg};
            border: 1px solid ${c.border};
            color: ${c.text};
            border-radius: 14px;
            box-shadow: 0 8px 30px rgba(0,0,0,0.12);
            z-index: 9999;
            font-weight: 600;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            gap: 10px;
            backdrop-filter: blur(12px);
            max-width: 340px;
            animation: slideInNotif 0.35s ease;
            font-family: 'Inter', system-ui, sans-serif;
        `;
        toast.innerHTML = `<span>${icons[type] || icons.info}</span><span>${message}</span>`;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutNotif 0.35s ease forwards';
            setTimeout(() => toast.remove(), 380);
        }, 4200);
    }

    window.showNotification = showToast;
    window.showToast = showToast;

    // =============================
    // LAZY IMAGE LOADER
    // =============================
    if ('IntersectionObserver' in window) {
        const imgObserver = new IntersectionObserver(entries => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.add('loaded');
                        imgObserver.unobserve(img);
                    }
                }
            });
        });
        document.querySelectorAll('img[data-src]').forEach(img => imgObserver.observe(img));
    }

    // =============================
    // ANIMATED COUNTER
    // =============================
    function animateCounter(el, target, duration = 1800) {
        const start = performance.now();
        const update = (now) => {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.floor(eased * target).toLocaleString();
            if (progress < 1) requestAnimationFrame(update);
            else el.textContent = target.toLocaleString();
        };
        requestAnimationFrame(update);
    }

    const counterObserver = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const el = entry.target;
                const target = parseInt(el.dataset.target, 10);
                if (!isNaN(target)) animateCounter(el, target);
                counterObserver.unobserve(el);
            }
        });
    }, { threshold: 0.5 });

    document.querySelectorAll('[data-target]').forEach(el => counterObserver.observe(el));

    // =============================
    // ACTIVE NAV LINK HIGHLIGHT
    // =============================
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-menu a').forEach(link => {
        const linkPath = new URL(link.href, window.location.origin).pathname;
        if (linkPath === currentPath) {
            link.style.color = '#f97316';
            link.style.background = 'rgba(249,115,22,0.08)';
        }
    });

});

// =============================
// UTILITY: Debounce
// =============================
function debounce(fn, wait) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), wait);
    };
}