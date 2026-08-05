// SEOScope Frontend Dashboard Application Logic

let currentReportData = null;
let currentReportId = null;
let categoryChartInstance = null;

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

function initApp() {
    setupEventListeners();
    checkUserAuth();
}

function setupEventListeners() {
    // Scan Form Submission
    const scanForm = document.getElementById('scanForm');
    if (scanForm) {
        scanForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const url = document.getElementById('urlInput').value.trim();
            if (url) {
                runScan(url);
            }
        });
    }

    // Preset Demo Buttons
    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const url = btn.getAttribute('data-url');
            document.getElementById('urlInput').value = url;
            runScan(url);
        });
    });

    // Tab Buttons Switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');
            switchTab(targetTab, btn);
        });
    });

    // Issue Filter Pills
    document.querySelectorAll('.pill-btn').forEach(pill => {
        pill.addEventListener('click', () => {
            document.querySelectorAll('.pill-btn').forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            const filter = pill.getAttribute('data-filter');
            filterIssues(filter);
        });
    });

    // Download PDF Button
    document.getElementById('btnDownloadPdf').addEventListener('click', () => {
        if (currentReportId) {
            window.open(`/api/reports/${currentReportId}/pdf`, '_blank');
        } else {
            alert('Please run a scan first to download the report.');
        }
    });

    // Download CSV Button
    document.getElementById('btnDownloadCsv').addEventListener('click', () => {
        if (currentReportId) {
            window.open(`/api/reports/${currentReportId}/csv`, '_blank');
        } else {
            alert('Please run a scan first to export CSV.');
        }
    });

    // Print Button
    document.getElementById('btnPrintReport').addEventListener('click', () => {
        window.print();
    });

    // History Modal
    document.getElementById('btnHistory').addEventListener('click', openHistoryModal);
    document.getElementById('closeHistoryModal').addEventListener('click', () => {
        document.getElementById('historyModal').classList.add('hidden');
    });

    // Auth Modal
    document.getElementById('btnLoginModal').addEventListener('click', openAuthModal);
    document.getElementById('closeAuthModal').addEventListener('click', () => {
        document.getElementById('authModal').classList.add('hidden');
    });

    document.getElementById('toggleAuthMode').addEventListener('click', (e) => {
        e.preventDefault();
        toggleAuthMode();
    });

    document.getElementById('authForm').addEventListener('submit', handleAuthSubmit);
}

// --- SCAN EXECUTION & ANIMATION ---
async function runScan(targetUrl) {
    const overlay = document.getElementById('scanOverlay');
    document.getElementById('progressUrl').textContent = targetUrl;
    overlay.classList.remove('hidden');

    resetScanProgressAnimation();
    animateScanSteps();

    try {
        const response = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: targetUrl })
        });

        const result = await response.json();

        if (result.success) {
            currentReportData = result.data;
            currentReportId = result.report_id;
            
            // Finish animation then show dashboard
            setTimeout(() => {
                overlay.classList.add('hidden');
                renderDashboard(result.data);
            }, 1200);
        } else {
            overlay.classList.add('hidden');
            alert(`Scan Error: ${result.error}`);
        }
    } catch (err) {
        overlay.classList.add('hidden');
        alert(`Network Error: ${err.message}`);
    }
}

function resetScanProgressAnimation() {
    for (let i = 1; i <= 6; i++) {
        const step = document.getElementById(`step${i}`);
        step.className = i === 1 ? 'active' : 'pending';
        step.querySelector('i').className = i === 1 ? 'fa-solid fa-spinner fa-spin' : 'fa-regular fa-circle';
    }
}

function animateScanSteps() {
    const stepDelays = [200, 400, 600, 800, 1000];
    stepDelays.forEach((delay, idx) => {
        setTimeout(() => {
            const prevStep = document.getElementById(`step${idx + 1}`);
            if (prevStep) {
                prevStep.className = 'done';
                prevStep.querySelector('i').className = 'fa-solid fa-circle-check';
            }
            const nextStep = document.getElementById(`step${idx + 2}`);
            if (nextStep) {
                nextStep.className = 'active';
                nextStep.querySelector('i').className = 'fa-solid fa-spinner fa-spin';
            }
        }, delay);
    });
}

// --- DASHBOARD RENDER ---
function renderDashboard(data) {
    const dashboard = document.getElementById('dashboard');
    dashboard.classList.remove('hidden');
    dashboard.scrollIntoView({ behavior: 'smooth' });

    // Target URL & Date
    document.getElementById('displayTargetUrl').textContent = data.target_url;
    document.getElementById('displayAuditDate').innerHTML = `<i class="fa-regular fa-calendar-check"></i> Scanned: ${data.audit_date}`;

    const simTag = document.getElementById('simulatedTag');
    if (data.is_simulated) {
        simTag.style.display = 'inline-block';
    } else {
        simTag.style.display = 'none';
    }

    // Overall Score Ring
    const scores = data.scores || {};
    const overallScore = scores.overall_score || 0;
    document.getElementById('displayScoreNum').textContent = overallScore;

    const ringCircle = document.getElementById('scoreRingCircle');
    const maxOffset = 314; // circumference = 2 * pi * 50
    const offset = maxOffset - (maxOffset * overallScore / 100);
    ringCircle.style.strokeDashoffset = offset;

    const ratingBadge = document.getElementById('displayRatingGrade');
    ratingBadge.textContent = `${scores.rating_grade} (${overallScore}/100)`;
    ratingBadge.style.backgroundColor = `${scores.rating_color}25`;
    ratingBadge.style.color = scores.rating_color;
    ringCircle.style.stroke = scores.rating_color;

    // Category Scores
    const cat = scores.category_scores || {};
    updateCatScore('catTechVal', 'catTechBar', cat.technical || 0);
    updateCatScore('catContentVal', 'catContentBar', cat.content || 0);
    updateCatScore('catImagesVal', 'catImagesBar', cat.images || 0);
    updateCatScore('catLinksVal', 'catLinksBar', cat.links || 0);

    // Summary Counts
    const summary = scores.summary || {};
    document.getElementById('overviewCriticalCount').textContent = summary.critical_count || 0;
    document.getElementById('overviewWarningCount').textContent = summary.warning_count || 0;
    document.getElementById('overviewPassedCount').textContent = summary.passed_count || 0;

    document.getElementById('filterCritCount').textContent = summary.critical_count || 0;
    document.getElementById('filterWarnCount').textContent = summary.warning_count || 0;
    document.getElementById('filterPassCount').textContent = summary.passed_count || 0;
    document.getElementById('issuesBadgeCount').textContent = summary.total_issues || 0;

    // Render Sub-panes
    renderOverviewHighlights(scores);
    renderCategoryChart(cat);
    renderMetadataPane(data);
    renderHeadingsPane(data);
    renderImagesPane(data);
    renderTechnicalPane(data);
    renderIssuesList(scores);
    renderRecommendations(scores.recommendations || []);
}

function updateCatScore(valId, barId, val) {
    document.getElementById(valId).textContent = `${val}%`;
    document.getElementById(barId).style.width = `${val}%`;
}

// --- OVERVIEW HIGHLIGHTS ---
function renderOverviewHighlights(scores) {
    const container = document.getElementById('overviewQuickIssues');
    container.innerHTML = '';

    const issues = scores.issues || {};
    const criticals = issues.critical || [];
    const warnings = issues.warning || [];

    const topIssues = [...criticals, ...warnings].slice(0, 4);

    if (topIssues.length === 0) {
        container.innerHTML = '<div class="issue-item passed"><p>🎉 Great job! No critical errors or major warnings found.</p></div>';
        return;
    }

    topIssues.forEach(item => {
        const div = document.createElement('div');
        div.className = `issue-item ${item.type}`;
        div.innerHTML = `
            <div class="issue-header">
                <span class="issue-title-text">${item.title}</span>
                <span class="badge">${item.category}</span>
            </div>
            <p class="issue-desc">${item.description}</p>
        `;
        container.appendChild(div);
    });
}

// --- CHART.JS CATEGORY CHART ---
function renderCategoryChart(catScores) {
    const ctx = document.getElementById('categoryChart').getContext('2d');

    if (categoryChartInstance) {
        categoryChartInstance.destroy();
    }

    categoryChartInstance = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Technical SEO', 'Content', 'Images', 'Links'],
            datasets: [{
                label: 'SEO Sub-Score %',
                data: [
                    catScores.technical || 0,
                    catScores.content || 0,
                    catScores.images || 0,
                    catScores.links || 0
                ],
                backgroundColor: [
                    '#6366f1',
                    '#06b6d4',
                    '#f59e0b',
                    '#a855f7'
                ],
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: 'rgba(255, 255, 255, 0.08)' },
                    ticks: { color: '#94a3b8' }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#94a3b8' }
                }
            },
            plugins: {
                legend: { display: false }
            }
        }
    });
}

// --- METADATA PANE ---
function renderMetadataPane(data) {
    const meta = data.metadata || {};
    const title = meta.title || {};
    const desc = meta.description || {};

    document.getElementById('metaTitleText').textContent = title.value || '(No Title Tag Found)';
    document.getElementById('metaTitleLen').textContent = title.length || 0;
    
    const tBadge = document.getElementById('metaTitleBadge');
    tBadge.textContent = title.status ? title.status.toUpperCase() : 'UNKNOWN';

    document.getElementById('metaDescText').textContent = desc.value || '(No Meta Description Found)';
    document.getElementById('metaDescLen').textContent = desc.length || 0;

    const dBadge = document.getElementById('metaDescBadge');
    dBadge.textContent = desc.status ? desc.status.toUpperCase() : 'UNKNOWN';

    // Google SERP Snippet Preview
    document.getElementById('serpUrlPreview').textContent = data.final_url || data.target_url;
    document.getElementById('serpTitlePreview').textContent = title.value || 'Missing Page Title';
    document.getElementById('serpDescPreview').textContent = desc.value || 'No meta description tag was provided for this webpage.';
}

// --- HEADINGS & KEYWORDS PANE ---
function renderHeadingsPane(data) {
    const headings = data.headings || {};
    const breakdown = headings.breakdown || {};
    
    const countersGrid = document.getElementById('headingCountersGrid');
    countersGrid.innerHTML = `
        <div class="h-counter-card"><span class="tag">H1</span><div class="val">${breakdown.h1_count || 0}</div></div>
        <div class="h-counter-card"><span class="tag">H2</span><div class="val">${breakdown.h2_count || 0}</div></div>
        <div class="h-counter-card"><span class="tag">H3</span><div class="val">${breakdown.h3_count || 0}</div></div>
        <div class="h-counter-card"><span class="tag">H4</span><div class="val">${breakdown.h4_count || 0}</div></div>
        <div class="h-counter-card"><span class="tag">H5</span><div class="val">${breakdown.h5_count || 0}</div></div>
        <div class="h-counter-card"><span class="tag">H6</span><div class="val">${breakdown.h6_count || 0}</div></div>
    `;

    const h1List = headings.headings_data?.h1 || [];
    document.getElementById('h1TextDisplay').textContent = h1List.length > 0 ? h1List[0].text : '(No H1 Tag Found)';

    // Keywords Table
    const kwData = data.keywords || {};
    const topKw = kwData.top_keywords_1gram || [];
    const tbody = document.getElementById('keywordTableBody');
    tbody.innerHTML = '';

    topKw.slice(0, 8).forEach(item => {
        const tr = document.createElement('tr');
        const statusBadge = item.density > 4.5 
            ? '<span class="badge" style="background:rgba(244,63,94,0.2);color:#f43f5e;">High Density</span>' 
            : '<span class="badge" style="background:rgba(16,185,129,0.2);color:#10b981;">Good</span>';
        
        tr.innerHTML = `
            <td><strong>${item.keyword}</strong></td>
            <td>${item.count}</td>
            <td>${item.density}%</td>
            <td>${statusBadge}</td>
        `;
        tbody.appendChild(tr);
    });
}

// --- IMAGES PANE ---
function renderImagesPane(data) {
    const imgData = data.images || {};
    document.getElementById('imgTotalNum').textContent = imgData.total_images || 0;
    document.getElementById('imgMissingAltNum').textContent = (imgData.missing_alt_count || 0) + (imgData.empty_alt_count || 0);
    document.getElementById('imgOptimizedNum').textContent = imgData.optimized_alt_count || 0;
    document.getElementById('imgAltScoreNum').textContent = `${imgData.alt_score_percentage || 0}%`;

    const tbody = document.getElementById('imageDetailsTableBody');
    tbody.innerHTML = '';

    const details = imgData.details || {};
    const missing = details.missing_alt || [];
    const empty = details.empty_alt || [];

    const allIssuesList = [...missing, ...empty].slice(0, 10);

    if (allIssuesList.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" style="text-align:center;">All images contain valid, descriptive ALT text attributes!</td></tr>';
        return;
    }

    allIssuesList.forEach(item => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><code style="color:#38bdf8;">${item.src || 'Embedded Image'}</code></td>
            <td><em style="color:#94a3b8;">${item.alt || 'Missing'}</em></td>
            <td><span class="badge" style="background:rgba(244,63,94,0.2);color:#f43f5e;">Missing ALT</span></td>
        `;
        tbody.appendChild(tr);
    });
}

// --- TECHNICAL PANE ---
function renderTechnicalPane(data) {
    const tech = data.technical || {};
    document.getElementById('techHttpsStatus').textContent = tech.is_https ? 'Active (HTTPS)' : 'Insecure (HTTP)';
    document.getElementById('techHttpsStatus').style.color = tech.is_https ? '#10b981' : '#f43f5e';

    document.getElementById('techResponseTime').textContent = `${tech.response_time_ms || 0} ms`;
    document.getElementById('techRobotsStatus').textContent = tech.has_robots_txt ? 'Detected (/robots.txt)' : 'Missing';
    document.getElementById('techSitemapStatus').textContent = tech.has_xml_sitemap ? 'Detected (/sitemap.xml)' : 'Missing';
}

// --- ISSUES LIST & FILTER ---
function renderIssuesList(scores) {
    const issues = scores.issues || {};
    const container = document.getElementById('fullIssuesList');
    container.innerHTML = '';

    const all = [
        ...(issues.critical || []),
        ...(issues.warning || []),
        ...(issues.passed || [])
    ];

    all.forEach(item => {
        const div = document.createElement('div');
        div.className = `issue-item ${item.type}`;
        div.setAttribute('data-type', item.type);
        div.innerHTML = `
            <div class="issue-header">
                <span class="issue-title-text">${item.title}</span>
                <span class="badge">${item.category} &bull; ${item.type.toUpperCase()}</span>
            </div>
            <p class="issue-desc">${item.description}</p>
        `;
        container.appendChild(div);
    });
}

function filterIssues(filterType) {
    const items = document.querySelectorAll('#fullIssuesList .issue-item');
    items.forEach(item => {
        if (filterType === 'all' || item.getAttribute('data-type') === filterType) {
            item.style.display = 'block';
        } else {
            item.style.display = 'none';
        }
    });
}

// --- RECOMMENDATIONS PANE ---
function renderRecommendations(recs) {
    const container = document.getElementById('recommendationsList');
    container.innerHTML = '';

    if (recs.length === 0) {
        container.innerHTML = '<div class="rec-card"><div class="rec-content"><h4>No Action Required</h4><p>Your website passed all primary SEO rules!</p></div></div>';
        return;
    }

    recs.forEach(r => {
        const pClass = r.priority === 'High' ? 'priority-high' : r.priority === 'Medium' ? 'priority-medium' : 'priority-low';
        const div = document.createElement('div');
        div.className = 'rec-card';
        div.innerHTML = `
            <div class="rec-priority-tag ${pClass}">${r.priority}</div>
            <div class="rec-content">
                <h4>${r.action}</h4>
                <p><strong>How to Fix:</strong> ${r.how_to_fix}</p>
            </div>
        `;
        container.appendChild(div);
    });
}

// --- TAB SWITCHING ---
function switchTab(targetTabId, btnEl) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    btnEl.classList.add('active');
    const pane = document.getElementById(targetTabId);
    if (pane) {
        pane.classList.add('active');
    }
}

// --- HISTORY MODAL ---
async function openHistoryModal() {
    const modal = document.getElementById('historyModal');
    modal.classList.remove('hidden');

    try {
        const res = await fetch('/api/reports');
        const data = await res.json();
        if (data.success) {
            renderHistoryTable(data.reports);
        }
    } catch (err) {
        console.error("Failed to load audit history:", err);
    }
}

function renderHistoryTable(reports) {
    const tbody = document.getElementById('historyTableBody');
    tbody.innerHTML = '';

    if (reports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No past audit reports found in database.</td></tr>';
        return;
    }

    reports.forEach(r => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${r.id}</td>
            <td><code style="color:#38bdf8;">${r.website_url}</code></td>
            <td><strong>${r.seo_score} / 100</strong></td>
            <td>${r.date}</td>
            <td>
                <button class="btn btn-outline" style="padding:0.25rem 0.5rem;" onclick="loadReportFromHistory(${r.id})">View</button>
                <a href="/api/reports/${r.id}/pdf" target="_blank" class="btn btn-outline" style="padding:0.25rem 0.5rem;">PDF</a>
                <button class="btn btn-outline" style="padding:0.25rem 0.5rem;color:#f43f5e;" onclick="deleteReportFromHistory(${r.id})">Delete</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

async function loadReportFromHistory(id) {
    document.getElementById('historyModal').classList.add('hidden');
    try {
        const res = await fetch(`/api/reports/${id}`);
        const result = await res.json();
        if (result.success && result.report.audit_data) {
            currentReportData = result.report.audit_data;
            currentReportId = result.report.id;
            renderDashboard(currentReportData);
        }
    } catch (err) {
        alert("Error loading report from database.");
    }
}

async function deleteReportFromHistory(id) {
    if (!confirm("Are you sure you want to delete this report?")) return;
    try {
        await fetch(`/api/reports/${id}`, { method: 'DELETE' });
        openHistoryModal();
    } catch (err) {
        alert("Failed to delete report.");
    }
}

// --- AUTHENTICATION MODAL ---
let isRegisterMode = false;

function openAuthModal() {
    document.getElementById('authModal').classList.remove('hidden');
}

function toggleAuthMode() {
    isRegisterMode = !isRegisterMode;
    const title = document.getElementById('authModalTitle');
    const groupName = document.getElementById('groupName');
    const btnSubmit = document.getElementById('btnSubmitAuth');
    const toggleText = document.getElementById('authToggleText');

    if (isRegisterMode) {
        title.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create Account';
        groupName.classList.remove('hidden');
        btnSubmit.textContent = 'Create Account';
        toggleText.innerHTML = 'Already have an account? <a href="#" id="toggleAuthMode">Sign In</a>';
    } else {
        title.innerHTML = '<i class="fa-solid fa-user-lock"></i> Account Sign In';
        groupName.classList.add('hidden');
        btnSubmit.textContent = 'Sign In';
        toggleText.innerHTML = 'Don\'t have an account? <a href="#" id="toggleAuthMode">Create account</a>';
    }

    document.getElementById('toggleAuthMode').addEventListener('click', (e) => {
        e.preventDefault();
        toggleAuthMode();
    });
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value;
    const password = document.getElementById('authPassword').value;
    const name = document.getElementById('authName').value;

    const endpoint = isRegisterMode ? '/api/auth/register' : '/api/auth/login';
    const body = isRegisterMode ? { name, email, password } : { email, password };

    try {
        const res = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        const result = await res.json();
        if (result.success) {
            document.getElementById('authModal').classList.add('hidden');
            updateUserNav(result.user);
        } else {
            alert(`Auth Error: ${result.error}`);
        }
    } catch (err) {
        alert("Authentication failed.");
    }
}

async function checkUserAuth() {
    try {
        const res = await fetch('/api/auth/me');
        const result = await res.json();
        if (result.authenticated) {
            updateUserNav(result.user);
        }
    } catch (err) {
        console.log("Not authenticated.");
    }
}

function updateUserNav(user) {
    const container = document.getElementById('userAuthContainer');
    container.innerHTML = `
        <span style="color:#38bdf8;font-weight:600;font-size:0.9rem;"><i class="fa-solid fa-circle-user"></i> ${user.name}</span>
        <button class="btn btn-outline" onclick="handleLogout()"><i class="fa-solid fa-right-from-bracket"></i> Logout</button>
    `;
}

async function handleLogout() {
    await fetch('/api/auth/logout', { method: 'POST' });
    location.reload();
}
