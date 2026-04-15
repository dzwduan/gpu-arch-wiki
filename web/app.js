// 初始化
document.addEventListener('DOMContentLoaded', () => {
    initNavigation();
    renderFormatCards();
    renderHardwareMatrix();
    initLightbox();

    // 初始化当前 active section 的目录
    const activeSection = document.querySelector('.content-section.active');
    if (activeSection) {
        const toc = activeSection.querySelector('.page-toc');
        if (toc) toc.classList.add('visible');
    }
});

// 图片放大查看
function initLightbox() {
    const lightbox = document.getElementById('imgLightbox');
    const lightboxImg = document.getElementById('lightboxImg');

    // 点击图片打开
    document.addEventListener('click', (e) => {
        const img = e.target.closest('.arch-figure img, .arch-figure-half img, .paper-figure img, .full-width-figure img');
        if (img) {
            lightboxImg.src = img.src;
            lightbox.classList.add('active');
        }
    });

    // 点击关闭
    lightbox.addEventListener('click', () => {
        lightbox.classList.remove('active');
    });

    // ESC 关闭
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') lightbox.classList.remove('active');
    });
}

// 导航切换
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.content-section');

    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const targetSection = item.dataset.section;

            // 更新导航状态
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // 更新内容区显示
            sections.forEach(section => {
                section.classList.remove('active');
                if (section.id === targetSection) {
                    section.classList.add('active');
                }
            });

            // 切换页面时滚动到顶部
            window.scrollTo(0, 0);

            // 只显示当前 section 的目录
            document.querySelectorAll('.page-toc').forEach(toc => toc.classList.remove('visible'));
            const activeToc = document.querySelector(`#${targetSection} .page-toc`);
            if (activeToc) activeToc.classList.add('visible');
        });
    });
}

// 渲染格式卡片
function renderFormatCards() {
    const container = document.getElementById('formatCards');
    container.innerHTML = '';

    // 定义显示顺序：按分类组织
    const orderedIds = [
        // 标准浮点
        'fp64', 'fp32', 'fp16',
        // AI 专用
        'tf32', 'bf16', 'fp8_e4m3', 'fp8_e5m2', 'fp6_e3m2', 'fp6_e2m3', 'nvfp4',
        // 量化格式
        'int16', 'int8', 'int4', 'int1',
        'fp4', 'nf4', 'mxfp4',
        // 扩展格式
        'posit', 'bfp'
    ];

    // 按顺序渲染
    orderedIds.forEach(id => {
        const format = formatsData.find(f => f.id === id);
        if (format) {
            const card = createFormatCard(format);
            container.appendChild(card);
        }
    });
}

// 创建单个格式卡片
function createFormatCard(format) {
    const card = document.createElement('div');
    card.className = 'format-card';
    card.dataset.id = format.id;
    card.dataset.category = format.category;
    card.dataset.name = format.name.toLowerCase();

    const usageTags = [];
    if (format.training) usageTags.push('<span class="usage-tag training">训练</span>');
    if (format.inference) usageTags.push('<span class="usage-tag inference">推理</span>');
    if (format.hpc) usageTags.push('<span class="usage-tag hpc">HPC</span>');
    if (format.quantization) usageTags.push('<span class="usage-tag">量化</span>');

    const bitPreview = generateBitPreview(format);

    card.innerHTML = `
        <div class="format-header">
            <div class="format-name">${format.name}</div>
            <div class="format-category">${format.categoryName}</div>
        </div>
        ${bitPreview}
        <div class="format-bits">
            <span>${format.bits} 位</span>
            ${format.exponent > 0 ? `<span>E${format.exponent}</span>` : ''}
            ${format.mantissa > 0 ? `<span>M${format.mantissa}</span>` : ''}
        </div>
        <div class="format-description">${format.description}</div>
        <div class="format-usage">
            ${usageTags.join('')}
        </div>
    `;

    // 点击展开详情
    card.addEventListener('click', () => {
        showFormatDetail(format);
    });

    return card;
}

// 显示格式详情模态框
function showFormatDetail(format) {
    const modal = document.getElementById('formatModal');
    const modalBody = document.getElementById('modalBody');

    // 生成位结构可视化
    const bitViz = generateBitVisualization(format);

    modalBody.innerHTML = `
        <div class="modal-header">
            <div class="modal-title">${format.name}</div>
            <div class="modal-subtitle">${format.categoryName} · ${format.standard}</div>
        </div>

        ${bitViz ? `
        <div class="modal-section">
            <h3>位结构可视化</h3>
            <div class="bit-visualization">
                ${bitViz}
            </div>
        </div>
        ` : ''}

        <div class="modal-section">
            <h3>基本信息</h3>
            <p>${format.description}</p>
            <div class="bit-structure">
                <div class="bit-item">
                    <div class="label">总位宽</div>
                    <div class="value">${format.bits}</div>
                </div>
                <div class="bit-item">
                    <div class="label">符号位</div>
                    <div class="value">${format.sign}</div>
                </div>
                <div class="bit-item">
                    <div class="label">指数位</div>
                    <div class="value">${format.exponent || 'N/A'}</div>
                </div>
                <div class="bit-item">
                    <div class="label">尾数位</div>
                    <div class="value">${format.mantissa || 'N/A'}</div>
                </div>
                <div class="bit-item">
                    <div class="label">每参数内存</div>
                    <div class="value">${format.memoryPerParam || 'N/A'} B</div>
                </div>
                <div class="bit-item">
                    <div class="label">相对速度</div>
                    <div class="value">${format.relativeSpeed || 'N/A'}×</div>
                </div>
            </div>
        </div>

        <div class="modal-section">
            <h3>特性</h3>
            <p><strong>动态范围:</strong> ${format.dynamicRange}</p>
            <p><strong>精度:</strong> ${format.precision}</p>
            <p><strong>典型用途:</strong> ${format.usage}</p>
            <p><strong>混合精度搭配:</strong> ${format.mixedPrecision}</p>
        </div>

        <div class="modal-section">
            <div class="pros-cons">
                <div class="pros">
                    <h4>✓ 优点</h4>
                    <p>${format.pros}</p>
                </div>
                <div class="cons">
                    <h4>✗ 缺点</h4>
                    <p>${format.cons}</p>
                </div>
            </div>
        </div>

        ${format.codeExamples && format.codeExamples.length > 0 ? `
        <div class="modal-section">
            <h3>代码示例</h3>
            ${format.codeExamples.map(example => `
                <div class="code-example">
                    <div class="code-lang-label">${example.lang}</div>
                    <pre>${highlightCode(example.code)}</pre>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;

    modal.classList.add('active');

    // 关闭模态框
    const closeBtn = modal.querySelector('.modal-close');
    closeBtn.onclick = () => modal.classList.remove('active');
    modal.onclick = (e) => {
        if (e.target === modal) modal.classList.remove('active');
    };
}

// 渲染硬件支持矩阵
function renderHardwareMatrix() {
    const table = document.getElementById('hardwareMatrix');
    let html = '<thead><tr><th>格式</th>';

    // 表头：厂商和架构
    hardwareData.vendors.forEach(vendor => {
        vendor.families.forEach(family => {
            html += `<th><div>${vendor.name}</div><div style="font-size:11px;color:var(--text-dim)">${family.name}</div></th>`;
        });
    });
    html += '</tr></thead><tbody>';

    // 行：主要格式
    const mainFormats = ['fp64', 'fp32', 'tf32', 'bf16', 'fp16', 'fp8_e4m3', 'fp8_e5m2', 'fp6_e3m2', 'fp6_e2m3', 'nvfp4', 'fp4', 'int8', 'int4'];

    mainFormats.forEach(formatId => {
        const format = formatsData.find(f => f.id === formatId);
        if (!format) return;

        html += `<tr><td style="text-align:left;font-weight:600">${format.name}</td>`;

        hardwareData.vendors.forEach(vendor => {
            vendor.families.forEach(family => {
                const key = `${vendor.id}-${family.id}`;
                const support = hardwareSupport[formatId]?.[key] || 'none';
                const supportClass = `support-${support}`;
                const title = {
                    'native': '原生支持',
                    'full': '完整支持',
                    'partial': '部分支持',
                    'none': '不支持'
                }[support] || '不支持';

                html += `<td><span class="support-level ${supportClass}" title="${title}"></span></td>`;
            });
        });

        html += '</tr>';
    });

    html += '</tbody>';
    table.innerHTML = html;
}
