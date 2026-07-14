
// ===== NUTRITION DASHBOARD INITIALIZATION =====
function initNutrition() {
    console.log('🥗 Nutrition Intelligence Initialized');
    
    // Initialize tooltips or other components if needed
    const tooltips = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    if (typeof bootstrap !== 'undefined' && tooltips.length > 0) {
        tooltips.forEach(el => new bootstrap.Tooltip(el));
    }
}

// Preview meal image before upload
function previewCompact(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = function (e) {
        const placeholder = document.getElementById('compactPlaceholder');
        const preview = document.getElementById('compactPreview');
        if (placeholder) placeholder.style.display = 'none';
        if (preview) {
            preview.src = e.target.result;
            preview.style.display = 'block';
        }
    };
    reader.readAsDataURL(file);
}

// Open the smart meal plan modal
function openDaySmartModal(el) {
    const day = el.getAttribute('data-day');
    const meals = JSON.parse(el.getAttribute('data-meals'));

    const titleEl = document.getElementById('smartDayTitle');
    if (titleEl) titleEl.innerText = day + "'s Smart Diet Plan";
    
    const container = document.getElementById('smartMealContainer');
    if (container) {
        container.innerHTML = '';

        meals.forEach(meal => {
            const div = document.createElement('div');
            div.className = 'smart-meal-item animate-scale';
            div.innerHTML = `
                <div class="s-meal-header">
                    <span class="s-meal-type">${meal.meal_type}</span>
                    <span class="fw-bold">${meal.calories} kcal</span>
                </div>
                <h4 class="s-meal-name">${meal.meal_name}</h4>
                ${meal.intake_time ? `<div class="mb-2 text-muted small"><i class="far fa-clock me-1"></i> ${meal.intake_time}</div>` : ''}
                <p class="s-meal-desc">${meal.description || 'No description available for this meal.'}</p>
                <div class="s-meal-actions">
                    <a href="/dashboard/complete_meal/${meal.id}" class="btn-s-complete"><i class="fas fa-check me-2"></i> Complete</a>
                    <a href="/dashboard/skip_meal/${meal.id}" class="btn-s-skip" onclick="return confirm('Skip this meal?')"><i class="fas fa-forward"></i></a>
                </div>
            `;
            container.appendChild(div);
        });
    }

    if (typeof bootstrap !== 'undefined') {
        const modalEl = document.getElementById('smartPlanModal');
        if (modalEl) {
            const modal = new bootstrap.Modal(modalEl);
            modal.show();
        }
    }
}

// Auto-run if on nutrition page
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('.nutrition-container')) {
        initNutrition();
    }
});
