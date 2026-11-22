/**
 * Global interactive behaviors for AquaPlant Shop (CSP-compliant, zero inline scripts/handlers).
 */
(function () {
    'use strict';

    // 1. Account dropdown menu (base.html)
    function initAccountDropdown() {
        const btn = document.getElementById('account-dropdown-btn');
        const menu = document.getElementById('account-dropdown-menu');
        const chevron = document.getElementById('account-dropdown-chevron');
        const wrapper = document.getElementById('account-dropdown-wrapper');
        if (!btn || !menu || !wrapper) return;

        function setOpen(open) {
            menu.classList.toggle('hidden', !open);
            btn.setAttribute('aria-expanded', open ? 'true' : 'false');
            if (chevron) {
                chevron.classList.toggle('rotate-180', open);
            }
        }

        btn.addEventListener('click', function (e) {
            e.stopPropagation();
            setOpen(menu.classList.contains('hidden'));
        });

        document.addEventListener('click', function (e) {
            if (!wrapper.contains(e.target)) {
                setOpen(false);
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                setOpen(false);
            }
        });
    }

    // 2. Subnav horizontal scroll hint (base.html)
    function initSubnavScrollHint() {
        const scroller = document.getElementById('subnav-scroller');
        const hintBtn = document.getElementById('subnav-scroll-hint');
        if (!scroller || !hintBtn) return;

        function syncScrollHint() {
            const canScrollRight = (scroller.scrollWidth - scroller.scrollLeft - scroller.clientWidth) > 8;
            if (canScrollRight) {
                hintBtn.classList.remove('hidden');
                hintBtn.classList.add('flex');
            } else {
                hintBtn.classList.add('hidden');
                hintBtn.classList.remove('flex');
            }
        }

        hintBtn.addEventListener('click', function () {
            scroller.scrollBy({ left: 160, behavior: 'smooth' });
        });
        scroller.addEventListener('scroll', syncScrollHint, { passive: true });
        window.addEventListener('resize', syncScrollHint);
        syncScrollHint();
    }

    // 3. Dismissible alert banners (base.html)
    function initAlertDismiss() {
        document.querySelectorAll('[data-dismiss-alert]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const container = btn.closest('[data-alert-item]') || btn.parentElement;
                if (container) container.remove();
            });
        });
    }

    // 4. Mobile filter toggle & auto-submit sort select (home.html)
    function initHomeControls() {
        const toggleBtn = document.getElementById('mobile-filter-toggle');
        const sidebar = document.getElementById('home-sidebar-filters');
        const chevron = document.getElementById('mobile-filter-chevron');
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', function () {
                const isHidden = sidebar.classList.contains('hidden');
                sidebar.classList.toggle('hidden', !isHidden);
                toggleBtn.setAttribute('aria-expanded', isHidden ? 'true' : 'false');
                if (chevron) chevron.classList.toggle('rotate-180', isHidden);
            });
        }

        document.querySelectorAll('select[data-auto-submit="true"]').forEach(function (sel) {
            sel.addEventListener('change', function () {
                if (sel.form) sel.form.submit();
            });
        });
    }

    // 5. Confirmation forms & quick coupon fill buttons (cart.html)
    function initCartControls() {
        document.querySelectorAll('form[data-confirm-message]').forEach(function (form) {
            form.addEventListener('submit', function (e) {
                const msg = form.dataset.confirmMessage;
                if (msg && !window.confirm(msg)) {
                    e.preventDefault();
                }
            });
        });

        document.querySelectorAll('[data-fill-target][data-fill-value]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const target = document.getElementById(btn.dataset.fillTarget);
                if (target) {
                    target.value = btn.dataset.fillValue;
                    target.focus();
                }
            });
        });
    }

    // 6. FAQ accordion (faq.html)
    function initFaqAccordion() {
        document.querySelectorAll('[data-faq-toggle]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const body = document.getElementById(btn.dataset.faqToggle);
                const icon = btn.dataset.faqIcon ? document.getElementById(btn.dataset.faqIcon) : null;
                if (!body) return;
                const willShow = body.classList.contains('hidden');
                body.classList.toggle('hidden', !willShow);
                btn.setAttribute('aria-expanded', willShow ? 'true' : 'false');
                if (icon) icon.classList.toggle('rotate-180', willShow);
            });
        });
    }

    // 7. Combo preset dynamic calculator (layout_presets.html)
    function initComboCalculator() {
        const checkboxes = document.querySelectorAll('.combo-checkbox');
        if (checkboxes.length === 0) return;

        function recalculateComboTotal(presetId) {
            const group = document.querySelectorAll('.combo-checkbox[data-preset="' + presetId + '"]');
            let total = 0;
            let checkedCount = 0;
            group.forEach(function (cb) {
                if (cb.checked) {
                    const price = parseFloat(cb.getAttribute('data-price')) || 0;
                    const qty = parseInt(cb.getAttribute('data-qty'), 10) || 1;
                    total += price * qty;
                    checkedCount++;
                }
            });
            const totalEl = document.getElementById('combo-total-' + presetId);
            if (totalEl) {
                totalEl.textContent = new Intl.NumberFormat('vi-VN').format(total) + '₫';
            }
            const submitBtn = document.getElementById('combo-submit-' + presetId);
            if (submitBtn) {
                submitBtn.disabled = checkedCount === 0;
                submitBtn.classList.toggle('opacity-50', checkedCount === 0);
                submitBtn.classList.toggle('cursor-not-allowed', checkedCount === 0);
            }
        }

        const seenPresets = new Set();
        checkboxes.forEach(function (cb) {
            const presetId = cb.getAttribute('data-preset');
            cb.addEventListener('change', function () {
                recalculateComboTotal(presetId);
            });
            if (presetId && !seenPresets.has(presetId)) {
                seenPresets.add(presetId);
                recalculateComboTotal(presetId);
            }
        });
    }

    // 8. Product detail gallery, variants, qty stepper, tabs, rating bars (product_detail.html)
    function initProductDetail() {
        const mainImg = document.getElementById('main-product-image');
        const thumbs = document.querySelectorAll('.gallery-thumb[data-gallery-url]');
        thumbs.forEach(function (thumb) {
            thumb.addEventListener('click', function () {
                const url = thumb.dataset.galleryUrl;
                if (mainImg && url) {
                    mainImg.src = url;
                }
                thumbs.forEach(function (t) {
                    t.classList.remove('border-[#3D6B4E]', 'border-2');
                    t.classList.add('border-slate-200', 'border');
                });
                thumb.classList.remove('border-slate-200', 'border');
                thumb.classList.add('border-[#3D6B4E]', 'border-2');
            });
        });

        const variantCards = document.querySelectorAll('.variant-card[data-variant-id]');
        variantCards.forEach(function (card) {
            card.addEventListener('click', function () {
                variantCards.forEach(function (c) {
                    c.classList.remove('border-[#3D6B4E]', 'bg-[#EEF5F0]', 'ring-1', 'ring-[#3D6B4E]');
                    c.classList.add('border-slate-200', 'bg-white');
                    c.setAttribute('aria-pressed', 'false');
                });
                card.classList.add('border-[#3D6B4E]', 'bg-[#EEF5F0]', 'ring-1', 'ring-[#3D6B4E]');
                card.classList.remove('border-slate-200', 'bg-white');
                card.setAttribute('aria-pressed', 'true');

                const hiddenInput = document.getElementById('selected-variant-id');
                if (hiddenInput) hiddenInput.value = card.dataset.variantId || '';

                const priceDisplay = document.getElementById('main-product-price');
                if (priceDisplay && card.dataset.variantPrice) {
                    priceDisplay.textContent = card.dataset.variantPrice + '₫';
                }
                const stockDisplay = document.getElementById('stock-display');
                if (stockDisplay && card.dataset.variantStock) {
                    stockDisplay.textContent = 'Còn ' + card.dataset.variantStock + ' phần';
                }
            });
        });

        const qtyInput = document.getElementById('qty');
        const decBtn = document.getElementById('qty-dec-btn');
        const incBtn = document.getElementById('qty-inc-btn');
        if (qtyInput && decBtn && incBtn) {
            decBtn.addEventListener('click', function () {
                const cur = parseInt(qtyInput.value, 10) || 1;
                if (cur > 1) qtyInput.value = String(cur - 1);
            });
            incBtn.addEventListener('click', function () {
                const cur = parseInt(qtyInput.value, 10) || 1;
                const maxVal = parseInt(qtyInput.getAttribute('max'), 10) || 9999;
                if (cur < maxVal) qtyInput.value = String(cur + 1);
            });
        }

        const tabBtns = document.querySelectorAll('.product-tab-btn[data-tab-target]');
        if (tabBtns.length > 0) {
            tabBtns.forEach(function (btn) {
                btn.addEventListener('click', function () {
                    const targetId = btn.dataset.tabTarget;
                    tabBtns.forEach(function (other) {
                        const panel = document.getElementById(other.dataset.tabTarget);
                        if (panel) panel.classList.add('hidden');
                        other.classList.remove('border-[#3D6B4E]', 'text-[#2F5C3E]', 'bg-[#EEF5F0]');
                        other.classList.add('border-transparent', 'text-slate-600');
                        other.setAttribute('aria-selected', 'false');
                    });
                    const activePanel = document.getElementById(targetId);
                    if (activePanel) activePanel.classList.remove('hidden');
                    btn.classList.remove('border-transparent', 'text-slate-600');
                    btn.classList.add('border-[#3D6B4E]', 'text-[#2F5C3E]', 'bg-[#EEF5F0]');
                    btn.setAttribute('aria-selected', 'true');
                });
            });
        }

        document.querySelectorAll('[data-progress-width]').forEach(function (el) {
            const pct = parseFloat(el.dataset.progressWidth);
            if (!Number.isNaN(pct)) {
                el.style.width = Math.max(0, Math.min(100, pct)) + '%';
            }
        });
    }

    // 9. Print & close window actions (print_packing_slip.html)
    function initPrintActions() {
        document.querySelectorAll('[data-window-action]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const action = btn.dataset.windowAction;
                if (action === 'print') {
                    window.print();
                } else if (action === 'close') {
                    window.close();
                }
            });
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        initAccountDropdown();
        initSubnavScrollHint();
        initAlertDismiss();
        initHomeControls();
        initCartControls();
        initFaqAccordion();
        initComboCalculator();
        initProductDetail();
        initPrintActions();
    });
})();
