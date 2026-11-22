/**
 * AI Desk Scanner & Aquatic Tank Composite Renderer (plant_assistant.html)
 * CSP-compliant external script: no inline <script> or HTML style attributes required.
 */
(function () {
    'use strict';

    const tabAiBtn = document.getElementById('tab-btn-ai');
    const tabFilterBtn = document.getElementById('tab-btn-filter');
    const panelAi = document.getElementById('panel-ai');
    const panelFilter = document.getElementById('panel-filter');

    function switchTab(mode) {
        if (!panelAi || !panelFilter || !tabAiBtn || !tabFilterBtn) return;
        const isAi = mode === 'ai';
        panelAi.classList.toggle('hidden', !isAi);
        panelFilter.classList.toggle('hidden', isAi);

        tabAiBtn.setAttribute('aria-selected', isAi ? 'true' : 'false');
        tabFilterBtn.setAttribute('aria-selected', isAi ? 'false' : 'true');

        tabAiBtn.className = isAi
            ? 'px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5 bg-[#3D6B4E] text-white shadow-sm'
            : 'px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5 text-slate-700 hover:text-slate-900';

        tabFilterBtn.className = !isAi
            ? 'px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5 bg-[#3D6B4E] text-white shadow-sm'
            : 'px-3.5 py-2 text-xs font-bold transition flex items-center gap-1.5 text-slate-700 hover:text-slate-900';
    }

    if (tabAiBtn && tabFilterBtn) {
        tabAiBtn.addEventListener('click', function () { switchTab('ai'); });
        tabFilterBtn.addEventListener('click', function () { switchTab('filter'); });
    }

    const scanForm = document.getElementById('ai-scan-form');
    if (!scanForm) return;

    const scanUrl = scanForm.dataset.scanUrl || '/api/ai-desk-scan/';
    const renderUrl = scanForm.dataset.renderUrl || '/api/ai-desk-render/';
    const IS_USER_AUTHENTICATED = scanForm.dataset.authenticated === '1';

    const imageInput = document.getElementById('desk-image-input');
    const dropzone = document.getElementById('desk-dropzone');
    const placeholder = document.getElementById('dropzone-placeholder');
    const previewWrap = document.getElementById('dropzone-preview-wrap');
    const previewImg = document.getElementById('dropzone-preview-img');
    const fileLabel = document.getElementById('dropzone-file-label');

    const scanErrorBox = document.getElementById('ai-scan-error');
    const scanBtn = document.getElementById('ai-scan-submit-btn');
    const emptyState = document.getElementById('ai-empty-state');
    const loadingState = document.getElementById('ai-loading-state');
    const resultBox = document.getElementById('ai-result-container');

    const renderBtn = document.getElementById('ai-render-btn');
    const renderErrBox = document.getElementById('ai-render-error');
    const renderLoading = document.getElementById('ai-render-loading');
    const renderResultWrap = document.getElementById('ai-render-result-wrap');

    let selectedFile = null;
    let previewDataUrl = '';
    let activeRenderContextToken = '';
    let latestScanData = null;
    let activePresetId = null;
    let activePresetData = null;
    let activePlacementPos = 'auto';
    let activeTankScale = 'balanced';
    let latestRenderedDataUrl = '';
    const PENDING_SCAN_STORAGE_KEY = 'aquaplant_pending_ai_scan';

    function savePendingScan() {
        if (!latestScanData || !activeRenderContextToken) return;
        try {
            sessionStorage.setItem(PENDING_SCAN_STORAGE_KEY, JSON.stringify({
                savedAt: Date.now(),
                scanData: latestScanData,
                previewDataUrl: previewDataUrl || '',
            }));
        } catch (_) {}
    }

    function clearPendingScan() {
        try { sessionStorage.removeItem(PENDING_SCAN_STORAGE_KEY); } catch (_) {}
    }

    function bindPillGroup(selector, dataKey, onChange) {
        const btns = Array.from(document.querySelectorAll(selector));
        btns.forEach(function (btn) {
            btn.addEventListener('click', function () {
                const val = btn.dataset[dataKey];
                if (!val) return;
                onChange(val);
                btns.forEach(function (b) {
                    const isActive = b.dataset[dataKey] === val;
                    b.className = isActive
                        ? 'px-2.5 py-1 border border-[#3D6B4E] bg-[#3D6B4E] text-white font-bold transition'
                        : 'px-2.5 py-1 border border-slate-300 bg-white text-slate-700 hover:border-[#3D6B4E] font-semibold transition';
                });
            });
        });
    }

    bindPillGroup('.ai-pos-btn', 'pos', function (v) { activePlacementPos = v; });
    bindPillGroup('.ai-scale-btn', 'scale', function (v) { activeTankScale = v; });

    const sliderRange = document.getElementById('ai-slider-range');
    const sliderBeforeLayer = document.getElementById('ai-slider-before-layer');
    const sliderDivider = document.getElementById('ai-slider-divider');
    const sliderStage = document.getElementById('ai-slider-stage');
    const sideBySideStage = document.getElementById('ai-sidebyside-stage');
    const btnModeSlider = document.getElementById('btn-mode-slider');
    const btnModeSide = document.getElementById('btn-mode-sidebyside');
    const lightboxModal = document.getElementById('ai-lightbox-modal');
    const lightboxImg = document.getElementById('ai-lightbox-img');
    const lightboxOpenBtn = document.getElementById('ai-lightbox-open');
    const lightboxCloseBtn = document.getElementById('ai-lightbox-close');

    function updateSplitSlider(pct) {
        const safePct = Math.max(0, Math.min(100, Number(pct) || 50));
        if (sliderBeforeLayer) sliderBeforeLayer.style.clipPath = 'inset(0 ' + (100 - safePct) + '% 0 0)';
        if (sliderDivider) sliderDivider.style.left = safePct + '%';
    }
    if (sliderRange) {
        sliderRange.addEventListener('input', function (e) { updateSplitSlider(e.target.value); });
    }

    function setCompareMode(mode) {
        const isSlider = mode === 'slider';
        if (sliderStage) sliderStage.classList.toggle('hidden', !isSlider);
        if (sideBySideStage) sideBySideStage.classList.toggle('hidden', isSlider);
        if (btnModeSlider) {
            btnModeSlider.className = isSlider
                ? 'px-3 py-1 bg-white text-[#2F5C3E] font-bold shadow-sm transition'
                : 'px-3 py-1 text-slate-600 hover:text-slate-900 font-semibold transition';
        }
        if (btnModeSide) {
            btnModeSide.className = !isSlider
                ? 'px-3 py-1 bg-white text-[#2F5C3E] font-bold shadow-sm transition'
                : 'px-3 py-1 text-slate-600 hover:text-slate-900 font-semibold transition';
        }
    }
    if (btnModeSlider) btnModeSlider.addEventListener('click', function () { setCompareMode('slider'); });
    if (btnModeSide) btnModeSide.addEventListener('click', function () { setCompareMode('sidebyside'); });

    function openLightbox() {
        if (!lightboxModal || !lightboxImg || !latestRenderedDataUrl) return;
        lightboxImg.src = latestRenderedDataUrl;
        lightboxModal.classList.remove('hidden');
    }
    function closeLightbox() {
        if (lightboxModal) lightboxModal.classList.add('hidden');
    }
    if (lightboxOpenBtn) lightboxOpenBtn.addEventListener('click', openLightbox);
    if (lightboxCloseBtn) lightboxCloseBtn.addEventListener('click', closeLightbox);
    const compareAfterImg = document.getElementById('ai-compare-after');
    if (compareAfterImg) compareAfterImg.addEventListener('click', openLightbox);
    if (lightboxModal) {
        lightboxModal.addEventListener('click', function (e) {
            if (e.target === lightboxModal) closeLightbox();
        });
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') closeLightbox();
        });
    }

    function getCsrfToken() {
        const inp = scanForm.querySelector('input[name="csrfmiddlewaretoken"]');
        return inp ? inp.value : '';
    }

    function showScanError(msg) {
        scanErrorBox.textContent = msg;
        scanErrorBox.classList.remove('hidden');
    }

    function clearScanError() {
        scanErrorBox.textContent = '';
        scanErrorBox.classList.add('hidden');
    }

    function updateQuotaBadges(quota) {
        if (!quota) return;
        const mBadge = document.getElementById('quota-monthly-badge');
        const uBadge = document.getElementById('quota-user-badge');
        if (mBadge) {
            mBadge.textContent = 'còn ' + quota.monthly_remaining + '/' + quota.monthly_cap + ' ảnh';
        }
        if (uBadge) {
            uBadge.textContent = 'còn ' + quota.user_remaining_today + '/' + quota.user_daily_cap + ' lượt';
        }
    }

    function handleChosenFile(file) {
        if (!file) return;
        selectedFile = file;
        clearScanError();

        const reader = new FileReader();
        reader.onload = function (ev) {
            previewDataUrl = ev.target.result || '';
            previewImg.src = previewDataUrl;
            fileLabel.textContent = file.name + ' (' + Math.max(1, Math.round(file.size / 1024)) + ' KB)';
            placeholder.classList.add('hidden');
            previewWrap.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }

    imageInput.addEventListener('change', function (e) {
        if (e.target.files && e.target.files[0]) {
            handleChosenFile(e.target.files[0]);
        }
    });

    dropzone.addEventListener('dragover', function (e) {
        e.preventDefault();
        dropzone.classList.add('border-[#3D6B4E]', 'bg-[#EEF5F0]/50');
    });
    dropzone.addEventListener('dragleave', function () {
        dropzone.classList.remove('border-[#3D6B4E]', 'bg-[#EEF5F0]/50');
    });
    dropzone.addEventListener('drop', function (e) {
        e.preventDefault();
        dropzone.classList.remove('border-[#3D6B4E]', 'bg-[#EEF5F0]/50');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleChosenFile(e.dataTransfer.files[0]);
        }
    });

    function downscaleImageFile(file) {
        return new Promise(function (resolve) {
            const img = new Image();
            const objUrl = URL.createObjectURL(file);
            img.onload = function () {
                try {
                    const maxDim = 1024;
                    let w = img.naturalWidth || img.width;
                    let h = img.naturalHeight || img.height;
                    if (!w || !h || (w <= maxDim && h <= maxDim && file.size <= 350000)) {
                        URL.revokeObjectURL(objUrl);
                        resolve(file);
                        return;
                    }
                    if (w > h && w > maxDim) {
                        h = Math.round((h * maxDim) / w);
                        w = maxDim;
                    } else if (h >= w && h > maxDim) {
                        w = Math.round((w * maxDim) / h);
                        h = maxDim;
                    }
                    const canvas = document.createElement('canvas');
                    canvas.width = w;
                    canvas.height = h;
                    const ctx = canvas.getContext('2d');
                    ctx.drawImage(img, 0, 0, w, h);
                    canvas.toBlob(function (blob) {
                        URL.revokeObjectURL(objUrl);
                        if (blob) {
                            resolve(new File([blob], 'desk_scan.jpg', { type: 'image/jpeg' }));
                        } else {
                            resolve(file);
                        }
                    }, 'image/jpeg', 0.80);
                } catch (_) {
                    URL.revokeObjectURL(objUrl);
                    resolve(file);
                }
            };
            img.onerror = function () {
                URL.revokeObjectURL(objUrl);
                resolve(file);
            };
            img.src = objUrl;
        });
    }

    function buildProductCard(prod, csrfToken) {
        const card = document.createElement('div');
        card.className = 'bg-white border border-slate-200 p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:border-[#3D6B4E] transition';

        const left = document.createElement('div');
        left.className = 'flex items-center gap-4';

        const imgLink = document.createElement('a');
        imgLink.href = prod.detail_url;
        imgLink.className = 'w-20 h-20 border border-slate-200 overflow-hidden flex-shrink-0';
        const img = document.createElement('img');
        img.src = prod.image_url;
        img.alt = prod.name;
        img.width = 80;
        img.height = 80;
        img.loading = 'lazy';
        img.className = 'w-full h-full object-cover';
        imgLink.appendChild(img);

        const meta = document.createElement('div');
        meta.className = 'text-xs space-y-1';

        const badge = document.createElement('span');
        badge.className = 'inline-block px-2 py-0.5 bg-[#EEF5F0] text-[#2F5C3E] border border-[#C5DEC9] text-[10px] font-bold';
        badge.textContent = prod.layer_role || prod.position_display;

        const titleH3 = document.createElement('h3');
        titleH3.className = 'font-bold text-sm text-slate-900';
        const titleA = document.createElement('a');
        titleA.href = prod.detail_url;
        titleA.className = 'hover:text-[#2F5C3E]';
        titleA.textContent = prod.name;
        titleH3.appendChild(titleA);

        const specsP = document.createElement('p');
        specsP.className = 'text-slate-600 text-[11px]';
        specsP.textContent = (prod.co2_display || '') + ' · ' + (prod.light_display || '');

        const reasonP = document.createElement('p');
        reasonP.className = 'text-[#2F5C3E] font-semibold text-[11px]';
        reasonP.textContent = '✓ ' + (prod.reason || '');

        meta.appendChild(badge);
        meta.appendChild(titleH3);
        meta.appendChild(specsP);
        meta.appendChild(reasonP);

        left.appendChild(imgLink);
        left.appendChild(meta);

        const right = document.createElement('div');
        right.className = 'flex sm:flex-col items-center sm:items-end justify-between gap-2 flex-shrink-0 border-t sm:border-t-0 pt-3 sm:pt-0';

        const priceSpan = document.createElement('span');
        priceSpan.className = 'font-mono font-black text-base text-rose-700';
        priceSpan.textContent = prod.price_display;

        const cartForm = document.createElement('form');
        cartForm.method = 'POST';
        cartForm.action = prod.add_to_cart_url;

        const csrfInput = document.createElement('input');
        csrfInput.type = 'hidden';
        csrfInput.name = 'csrfmiddlewaretoken';
        csrfInput.value = csrfToken;

        const qtyInput = document.createElement('input');
        qtyInput.type = 'hidden';
        qtyInput.name = 'quantity';
        qtyInput.value = '1';

        const addBtn = document.createElement('button');
        addBtn.type = 'submit';
        addBtn.className = 'bg-[#3D6B4E] hover:bg-[#2F5C3E] text-white text-xs font-bold px-4 py-2 transition';
        const icon = document.createElement('i');
        icon.className = 'fa-solid fa-cart-plus mr-1';
        icon.setAttribute('aria-hidden', 'true');
        addBtn.appendChild(icon);
        addBtn.appendChild(document.createTextNode('Thêm Giỏ'));

        cartForm.appendChild(csrfInput);
        cartForm.appendChild(qtyInput);
        cartForm.appendChild(addBtn);

        right.appendChild(priceSpan);
        right.appendChild(cartForm);

        card.appendChild(left);
        card.appendChild(right);
        return card;
    }

    function renderPresetPicker(presets) {
        const wrap = document.getElementById('ai-preset-picker-wrap');
        const grid = document.getElementById('ai-preset-picker-grid');
        const selectedLabel = document.getElementById('ai-preset-selected-label');
        const btnLabel = document.getElementById('ai-render-btn-label');
        if (!wrap || !grid) return;

        grid.textContent = '';
        activePresetId = null;
        activePresetData = null;

        if (!Array.isArray(presets) || presets.length === 0) {
            wrap.classList.add('hidden');
            if (selectedLabel) selectedLabel.textContent = '';
            if (btnLabel) btnLabel.textContent = 'Xem Phối Cảnh Đặt Bể Lên Bàn';
            return;
        }

        wrap.classList.remove('hidden');
        const cardButtons = [];

        function selectPreset(pr) {
            activePresetId = pr.id;
            activePresetData = pr;
            if (selectedLabel) {
                selectedLabel.textContent = 'Đang chọn: ' + pr.name + ' (' + (pr.tank_size || '') + ')';
            }
            if (btnLabel) {
                btnLabel.textContent = 'Ghép Mẫu Bể Này Lên Bàn';
            }
            cardButtons.forEach(function (entry) {
                if (entry.id === pr.id) {
                    entry.btn.className = 'border-2 border-[#3D6B4E] ring-2 ring-[#3D6B4E]/30 bg-[#EEF5F0] overflow-hidden text-left transition flex flex-col';
                } else {
                    entry.btn.className = 'border border-slate-200 bg-white hover:border-[#3D6B4E] overflow-hidden text-left transition flex flex-col';
                }
            });
        }

        presets.forEach(function (pr) {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'border border-slate-200 bg-white hover:border-[#3D6B4E] overflow-hidden text-left transition flex flex-col';

            const thumbBox = document.createElement('div');
            thumbBox.className = 'relative w-full h-20 bg-slate-100 overflow-hidden';

            const img = document.createElement('img');
            img.src = pr.image_url || '';
            img.alt = pr.name || 'Mẫu bể thủy sinh';
            img.width = 160;
            img.height = 80;
            img.loading = 'lazy';
            img.className = 'w-full h-full object-cover';
            thumbBox.appendChild(img);

            if (pr.is_recommended) {
                const recBadge = document.createElement('span');
                recBadge.className = 'absolute top-1 left-1 bg-[#3D6B4E] text-white text-[9px] font-bold px-1.5 py-0.5 uppercase';
                recBadge.textContent = 'AI gợi ý';
                thumbBox.appendChild(recBadge);
            }

            const body = document.createElement('div');
            body.className = 'p-1.5 space-y-0.5 flex-1';

            const title = document.createElement('div');
            title.className = 'font-bold text-[10px] text-slate-900 leading-tight line-clamp-2';
            title.textContent = pr.name || '';

            const sub = document.createElement('div');
            sub.className = 'text-[9px] text-slate-600 leading-tight';
            sub.textContent = (pr.tank_size || '') + ' · ' + (pr.license_name || 'Open');

            body.appendChild(title);
            body.appendChild(sub);

            btn.appendChild(thumbBox);
            btn.appendChild(body);
            btn.addEventListener('click', function () {
                selectPreset(pr);
            });

            grid.appendChild(btn);
            cardButtons.push({ id: pr.id, btn: btn });
        });

        selectPreset(presets[0]);
    }

    function renderScanResult(data) {
        const a = data.analysis || {};
        const tank = a.recommended_tank || {};
        latestScanData = data;
        activeRenderContextToken = data.render_context_token || '';
        savePendingScan();

        document.getElementById('ai-style-badge').textContent = a.detected_style || 'Không gian bàn';
        document.getElementById('ai-width-est-badge').textContent = a.estimated_free_width_cm || '';

        const annotatedImg = document.getElementById('ai-annotated-img');
        annotatedImg.src = previewDataUrl;

        const box = Array.isArray(a.placement_box) && a.placement_box.length === 4 ? a.placement_box : [350, 250, 750, 750];
        const overlay = document.getElementById('ai-placement-overlay');
        overlay.style.top = (box[0] / 10) + '%';
        overlay.style.left = (box[1] / 10) + '%';
        overlay.style.height = Math.max(8, (box[2] - box[0]) / 10) + '%';
        overlay.style.width = Math.max(8, (box[3] - box[1]) / 10) + '%';
        document.getElementById('ai-placement-label').textContent = 'Vị trí đặt bể · ' + (tank.size_cm || '30x20x25 cm');

        document.getElementById('ai-tank-title').textContent = (tank.size_cm || '') + ' · ' + (tank.style_name || '');
        document.getElementById('ai-tank-meta').textContent = (tank.shape || '') + (tank.volume_liters ? ' · ' + tank.volume_liters : '');
        document.getElementById('ai-tank-reason').textContent = tank.placement_reason || '';
        document.getElementById('ai-space-summary').textContent = a.space_summary || '';
        document.getElementById('ai-lighting-summary').textContent = a.lighting_assessment || '';

        const tipsUl = document.getElementById('ai-tips-list');
        tipsUl.textContent = '';
        (a.placement_tips || []).forEach(function (tip) {
            const li = document.createElement('li');
            li.textContent = tip;
            tipsUl.appendChild(li);
        });

        const productsWrap = document.getElementById('ai-products-list');
        productsWrap.textContent = '';
        const csrfToken = getCsrfToken();
        (data.recommended_products || []).forEach(function (prod) {
            productsWrap.appendChild(buildProductCard(prod, csrfToken));
        });

        const presetBox = document.getElementById('ai-preset-box');
        if (data.recommended_preset) {
            document.getElementById('ai-preset-title').textContent = data.recommended_preset.name;
            document.getElementById('ai-preset-meta').textContent =
                data.recommended_preset.tank_size + ' · ' + data.recommended_preset.style + ' · Giá set tham khảo: ' + data.recommended_preset.total_price_display;
            document.getElementById('ai-preset-link').href = data.recommended_preset.url;
            presetBox.classList.remove('hidden');
        } else {
            presetBox.classList.add('hidden');
        }

        if (renderResultWrap) renderResultWrap.classList.add('hidden');
        if (renderErrBox) {
            renderErrBox.textContent = '';
            renderErrBox.classList.add('hidden');
        }
        renderPresetPicker(data.candidate_presets || (data.recommended_preset ? [data.recommended_preset] : []));

        updateQuotaBadges(data.quota);
        emptyState.classList.add('hidden');
        loadingState.classList.add('hidden');
        resultBox.classList.remove('hidden');
    }

    scanForm.addEventListener('submit', async function (e) {
        e.preventDefault();
        clearScanError();

        if (!selectedFile) {
            showScanError('Vui lòng chụp hoặc chọn ảnh góc bàn trước khi bấm quét nhé!');
            return;
        }

        const loadingTitle = document.getElementById('ai-loading-title');
        let sec = 0;
        if (loadingTitle) loadingTitle.textContent = 'Đang phân tích góc bàn của bạn... (0s)';
        const scanTimer = setInterval(function () {
            sec += 1;
            if (loadingTitle) {
                loadingTitle.textContent = sec >= 20
                    ? 'Hệ thống phản hồi chậm hơn bình thường, đang chờ hoàn tất... (' + sec + 's)'
                    : 'Đang phân tích góc bàn của bạn... (' + sec + 's)';
            }
        }, 1000);

        const controller = new AbortController();
        const timeoutId = setTimeout(function () { controller.abort(); }, 65000);

        scanBtn.disabled = true;
        emptyState.classList.add('hidden');
        resultBox.classList.add('hidden');
        loadingState.classList.remove('hidden');

        try {
            const preparedFile = await downscaleImageFile(selectedFile);
            const formData = new FormData();
            formData.append('desk_image', preparedFile);
            formData.append('desk_width_cm', document.getElementById('desk-width-input').value.trim());
            formData.append('user_note', document.getElementById('desk-note-input').value.trim());

            const resp = await fetch(scanUrl, {
                method: 'POST',
                headers: { 'X-CSRFToken': getCsrfToken() },
                body: formData,
                signal: controller.signal,
            });
            const data = await resp.json();
            if (!resp.ok || !data.success) {
                loadingState.classList.add('hidden');
                emptyState.classList.remove('hidden');
                showScanError(data.message || 'Không thể phân tích ảnh lúc này.');
                updateQuotaBadges(data.quota);
                return;
            }
            renderScanResult(data);
        } catch (err) {
            loadingState.classList.add('hidden');
            emptyState.classList.remove('hidden');
            showScanError(
                err && err.name === 'AbortError'
                    ? 'Quá thời gian chờ phản hồi AI (65 giây). Vui lòng bấm Quét lại hoặc thử ảnh gọn hơn.'
                    : 'Mất kết nối tới máy chủ khi phân tích ảnh. Vui lòng thử lại.'
            );
        } finally {
            clearInterval(scanTimer);
            clearTimeout(timeoutId);
            scanBtn.disabled = false;
        }
    });

    if (renderBtn) {
        renderBtn.addEventListener('click', async function () {
            if (!activeRenderContextToken) return;

            const renderLoadingText = document.getElementById('ai-render-loading-text');
            let rSec = 0;
            if (renderLoadingText) renderLoadingText.textContent = 'Đang dựng ảnh phối cảnh... (0s)';
            const renderTimer = setInterval(function () {
                rSec += 1;
                if (renderLoadingText) {
                    renderLoadingText.textContent = 'Đang dựng ảnh phối cảnh... (' + rSec + 's)';
                }
            }, 1000);

            const rController = new AbortController();
            const rTimeoutId = setTimeout(function () { rController.abort(); }, 80000);

            renderErrBox.textContent = '';
            renderErrBox.classList.add('hidden');
            renderBtn.disabled = true;
            renderLoading.classList.remove('hidden');

            try {
                const formData = new FormData();
                formData.append('render_context_token', activeRenderContextToken);
                if (activePresetId) {
                    formData.append('preset_id', String(activePresetId));
                }
                formData.append('placement_position', activePlacementPos || 'auto');
                formData.append('tank_scale', activeTankScale || 'balanced');

                const resp = await fetch(renderUrl, {
                    method: 'POST',
                    headers: { 'X-CSRFToken': getCsrfToken() },
                    body: formData,
                    signal: rController.signal,
                });
                const data = await resp.json();
                if (!resp.ok || !data.success) {
                    renderErrBox.textContent = '';
                    const msgSpan = document.createElement('span');
                    msgSpan.textContent = data.message || 'Không thể vẽ phối cảnh lúc này.';
                    renderErrBox.appendChild(msgSpan);
                    if (resp.status === 401 && data.login_required && data.login_url) {
                        savePendingScan();
                        const loginLink = document.createElement('a');
                        loginLink.href = data.login_url;
                        loginLink.className = 'inline-block ml-2 underline font-bold text-[#2F5C3E] hover:text-slate-900';
                        loginLink.textContent = 'Đăng nhập ngay →';
                        renderErrBox.appendChild(loginLink);
                    }
                    renderErrBox.classList.remove('hidden');
                    updateQuotaBadges(data.quota);
                    return;
                }

                latestRenderedDataUrl = data.image_data_url || '';
                document.getElementById('ai-compare-before').src = previewDataUrl;
                document.getElementById('ai-compare-after').src = latestRenderedDataUrl;
                const sBefore = document.getElementById('ai-slider-before');
                const sAfter = document.getElementById('ai-slider-after');
                if (sBefore) sBefore.src = previewDataUrl;
                if (sAfter) sAfter.src = latestRenderedDataUrl;
                if (sliderRange) {
                    sliderRange.value = '50';
                    updateSplitSlider(50);
                }
                setCompareMode('slider');
                document.getElementById('ai-render-download').href = latestRenderedDataUrl;

                const tplCol = document.getElementById('ai-compare-template-col');
                if (tplCol) {
                    const tpl = data.used_preset || activePresetData;
                    if (tpl && tpl.image_url) {
                        tplCol.classList.remove('hidden');
                        document.getElementById('ai-compare-template-img').src = tpl.image_url;
                        document.getElementById('ai-compare-template-meta').textContent =
                            (tpl.name || '') + (tpl.tank_size ? ' · ' + tpl.tank_size : '');
                        const licEl = document.getElementById('ai-compare-template-license');
                        licEl.textContent = '';
                        const prefix = document.createTextNode(
                            'Bản quyền: ' + (tpl.license_name || 'Open License') + (tpl.source_attribution ? ' · Nguồn: ' : '')
                        );
                        licEl.appendChild(prefix);
                        if (tpl.source_attribution) {
                            const safeUrl = (tpl.source_url || '').trim();
                            if (/^https?:\/\//i.test(safeUrl)) {
                                const srcLink = document.createElement('a');
                                srcLink.href = safeUrl;
                                srcLink.target = '_blank';
                                srcLink.rel = 'noopener noreferrer';
                                srcLink.className = 'text-[#2F5C3E] hover:underline font-medium';
                                srcLink.textContent = tpl.source_attribution;
                                licEl.appendChild(srcLink);
                            } else {
                                licEl.appendChild(document.createTextNode(tpl.source_attribution));
                            }
                        }
                    } else {
                        tplCol.classList.add('hidden');
                    }
                }

                renderResultWrap.classList.remove('hidden');
                updateQuotaBadges(data.quota);
            } catch (err) {
                renderErrBox.textContent =
                    err && err.name === 'AbortError'
                        ? 'Quá thời gian chờ dựng ảnh (80 giây). Vui lòng thử bấm lại lần nữa nhé.'
                        : 'Lỗi kết nối khi tạo phối cảnh AI. Vui lòng thử lại.';
                renderErrBox.classList.remove('hidden');
            } finally {
                clearInterval(renderTimer);
                clearTimeout(rTimeoutId);
                renderLoading.classList.add('hidden');
                renderBtn.disabled = false;
            }
        });
    }

    if (IS_USER_AUTHENTICATED) {
        try {
            const rawSaved = sessionStorage.getItem(PENDING_SCAN_STORAGE_KEY);
            if (rawSaved) {
                const parsedSaved = JSON.parse(rawSaved);
                if (
                    parsedSaved
                    && parsedSaved.scanData
                    && parsedSaved.scanData.render_context_token
                    && parsedSaved.savedAt
                    && (Date.now() - parsedSaved.savedAt) < 15 * 60 * 1000
                ) {
                    previewDataUrl = parsedSaved.previewDataUrl || '';
                    renderScanResult(parsedSaved.scanData);
                }
                clearPendingScan();
            }
        } catch (_) {}
    }
})();
