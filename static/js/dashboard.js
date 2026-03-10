/**
 * dashboard.js — SaaS Analytics Dashboard
 */
let fbToken = sessionStorage.getItem('fbToken') || '';
let fbUser = JSON.parse(sessionStorage.getItem('fbUser') || '{}');
let churnChart = null;
let fcChart = null;
let regionData = [];
let selectedDuration = 30;

(function () {
    if (!fbToken) window.location.href = '/login';
})();

function authHeaders() {
    return { 'Authorization': `Bearer ${fbToken}`, 'Content-Type': 'application/json' };
}

async function api(url, options = {}) {
    const res = await fetch(url, { ...options, headers: { ...authHeaders(), ...options.headers } });
    if (res.status === 401) { sessionStorage.clear(); window.location.href = '/login'; return null; }
    if (!res.ok) throw new Error(`API error ${res.status}`);
    return res.json();
}

document.addEventListener('DOMContentLoaded', () => {
    // Extract operator from displayName if persisted as "Name|Operator"
    let name = fbUser.displayName || fbUser.email?.split('@')[0] || 'Analyst';
    let op = fbUser.operator || '';

    if (name.includes('|')) {
        const parts = name.split('|');
        name = parts[0];
        op = parts[1];
    } else if (!fbUser.operator) {
        // LEGACY USER detected: show modal, stop data fetching
        document.getElementById('legacyOpModal').style.display = 'flex';
        return;
    }

    document.getElementById('userName').textContent = name;
    document.getElementById('userAvatar').textContent = name.charAt(0).toUpperCase();

    // Show operator role if available
    const roleEl = document.querySelector('.user-role');
    if (roleEl) {
        roleEl.textContent = op ? `${op} Analyst` : 'Analyst';
    }

    // Attach op to fbUser for later use
    fbUser.operator = op;

    // Lock operator dropdowns if the user belongs to an operator
    if (op) {
        const churnOp = document.getElementById('churnOperator');
        if (churnOp) {
            churnOp.value = op;
            churnOp.disabled = true;
        }
        const fcOp = document.getElementById('fcOperator');
        if (fcOp) {
            fcOp.value = op;
            fcOp.disabled = true;
        }
    }

    startClock();
    loadOverview();
});

async function saveLegacyOperator() {
    const op = document.getElementById('legacyOperatorSelect').value;
    if (!op) return alert("Please select an operator");

    const btn = document.getElementById('saveLegacyOpBtn');
    btn.disabled = true;
    btn.innerText = "Updating profile...";

    try {
        const cfgRes = await fetch('/api/firebase-config');
        const cfg = await cfgRes.json();
        if (!firebase.apps.length) firebase.initializeApp(cfg);
        const auth = firebase.auth();
        const user = auth.currentUser;

        if (!user) throw new Error("User not authenticated in Firebase");

        // Persist operator in displayName as "Name|Operator"
        const cleanName = (user.displayName || user.email.split('@')[0] || 'Analyst').split('|')[0];
        const combinedName = `${cleanName}|${op}`;

        await user.updateProfile({ displayName: combinedName });

        // Update local session storage
        fbUser.displayName = combinedName;
        fbUser.operator = op;
        sessionStorage.setItem('fbUser', JSON.stringify(fbUser));

        // Reload to apply changes
        window.location.reload();
    } catch (e) {
        console.error(e);
        alert("Failed to update profile: " + e.message);
        btn.disabled = false;
        btn.innerText = "Save & Continue";
    }
}

function startClock() {
    function tick() {
        document.getElementById('headerTime').textContent = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
    }
    tick();
    setInterval(tick, 30000);
}

const SECTION_META = {
    overview: { title: 'Dashboard Overview', subtitle: 'Operational intelligence at a glance' },
    regions: { title: 'Region Monitoring', subtitle: 'Customer distribution across all areas' },
    churn: { title: 'Churn Prediction', subtitle: 'AI-powered customer retention analytics' },
    forecast: { title: 'Demand Forecasting', subtitle: '30 / 60 / 90 day demand projections' },
    operators: { title: 'Operator Analytics', subtitle: 'Comparative performance metrics' },
};

function showSection(name) {
    document.querySelectorAll('.dash-section').forEach(s => s.style.display = 'none');
    const el = document.getElementById(`section-${name}`);
    if (el) el.style.display = 'block';

    document.querySelectorAll('.nav-item').forEach(b => b.classList.remove('active'));
    const navBtn = document.getElementById(`nav-${name}`);
    if (navBtn) navBtn.classList.add('active');

    const meta = SECTION_META[name];
    document.getElementById('pageTitle').textContent = meta.title;
    document.getElementById('pageSubtitle').textContent = meta.subtitle;

    if (name === 'regions' && !regionData.length) loadRegions();
    if (name === 'churn') initChurnDropdowns();
    if (name === 'forecast') initForecastDropdowns();
    if (name === 'operators') loadOperators();
}

function handleLogout() {
    sessionStorage.clear();
    window.location.href = '/';
}


// OVERVIEW
async function loadOverview() {
    try {
        const opQuery = fbUser.operator ? `?op=${encodeURIComponent(fbUser.operator.split(' ')[0])}` : '';
        const data = await api('/api/overview' + opQuery);
        if (!data) return;

        animateCounter('kpiTotal', data.total_customers, 0, 1500);
        animateCounter('kpiCities', data.active_cities, 0, 1000);

        // Calculate 5G adoption% for the KPI
        const totalNet = data.network_4g + data.network_5g;
        const netPct = totalNet > 0 ? Math.round((data.network_5g / totalNet) * 100) : 0;
        document.getElementById('kpiNet').textContent = netPct + '%';

        document.getElementById('kpiUsage').textContent = data.average_usage.toFixed(1) + '%';
        document.getElementById('kpiStates').textContent = `${data.active_states} states covered`;
        document.getElementById('kpiTrend').textContent = `Demand trend: ${data.demand_trend}%`;

        loadOperatorSnapshot();
        loadRecentCustomers();
    } catch (e) { console.error(e); }
}

function animateCounter(id, target, from, duration) {
    const el = document.getElementById(id);
    if (!el) return;
    const start = performance.now();
    requestAnimationFrame(function up(now) {
        const p = Math.min((now - start) / duration, 1);
        el.textContent = Math.round(from + (target - from) * (1 - Math.pow(1 - p, 3))).toLocaleString('en-IN');
        if (p < 1) requestAnimationFrame(up);
    });
}

async function loadOperatorSnapshot() {
    const data = await api('/api/operators');
    if (!data) return;
    const container = document.getElementById('operatorSnapshot');
    const opColors = { Airtel: '#2563eb', BSNL: '#06b6d4', Jio: '#ef4444', Vi: '#f59e0b' };

    // Only show the user's operator if they have one
    let entries = Object.entries(data);
    if (fbUser.operator) {
        entries = entries.filter(([op, info]) => op === fbUser.operator);
    }

    container.innerHTML = entries.map(([op, info]) => `
    <div class="glass-card" style="padding:20px;">
      <div style="font-weight:700;font-size:1.1rem;color:${opColors[op]};margin-bottom:12px">${op}</div>
      <div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:0.9rem">
        <span style="color:var(--text-muted)">Customers</span><span style="font-weight:600">${info.customers.toLocaleString('en-IN')}</span>
      </div>
      <div style="display:flex;justify-content:space-between;font-size:0.9rem">
        <span style="color:var(--text-muted)">Churn Rate</span><span style="font-weight:600;color:var(--red)">${info.churn_rate}%</span>
      </div>
    </div>`).join('');
}

async function loadRecentCustomers() {
    const tbody = document.getElementById('customerTableBody');
    if (!tbody) return;
    try {
        const op = fbUser.operator ? fbUser.operator.split(' ')[0] : '';
        const opQuery = op ? `?op=${encodeURIComponent(op)}&limit=10` : '?limit=10';
        const data = await api('/api/customers' + opQuery);
        if (!data || data.length === 0) {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--text-muted)">No customers found.</td></tr>`;
            return;
        }

        renderCustomerRows(data, false);
    } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;padding:40px;color:var(--red)">Failed to load customers.</td></tr>`;
        console.error(e);
    }
}

function renderCustomerRows(data, append = false) {
    const tbody = document.getElementById('customerTableBody');
    const html = data.map(r => {
        const netCls = r.plan.includes('5G') ? 'status-good' : 'status-warning';
        return `<tr>
            <td style="font-weight:600">ID-${r.customer_id.toString().padStart(6, '0')}</td>
            <td>${r.city}</td>
            <td>${r.plan}</td>
            <td>${r.months_active}</td>
            <td><span class="status-badge ${netCls}">${r.plan.includes('5G') ? '5G' : '4G'}</span></td>
        </tr>`;
    }).join('');

    if (append) tbody.innerHTML += html;
    else tbody.innerHTML = html;
}

async function loadAllCustomers() {
    const btn = document.getElementById('loadAllCustomersBtn');
    const tbody = document.getElementById('customerTableBody');
    btn.disabled = true;
    btn.innerText = "Loading all data...";

    try {
        const op = fbUser.operator ? fbUser.operator.split(' ')[0] : '';
        const opQuery = op ? `?op=${encodeURIComponent(op)}&limit=100000&offset=10` : '?limit=100000&offset=10';
        const data = await api('/api/customers' + opQuery);
        if (data && data.length > 0) {
            renderCustomerRows(data, true);
            btn.style.display = 'none'; // Hide button after loading everything
        } else {
            btn.innerText = "No more data";
        }
    } catch (e) {
        alert("Failed to load full dataset");
        btn.disabled = false;
        btn.innerText = "Load Full Operator Dataset";
    }
}


// REGIONS
async function loadRegions() {
    const tbody = document.getElementById('regionTableBody');
    try {
        const op = fbUser.operator ? fbUser.operator.split(' ')[0] : '';
        const opQuery = op ? `&op=${encodeURIComponent(op)}` : '';
        regionData = await api(`/api/regions?limit=100${opQuery}`);
        renderRegionTable(regionData);
    } catch (e) {
        console.error("Regions load error:", e);
        tbody.innerHTML = `<tr><td colspan="9" style="color:red; text-align:center; padding:20px;">Failed to load region data. Please check server logs.</td></tr>`;
    }
}
function renderRegionTable(rows) {
    const tbody = document.getElementById('regionTableBody');
    document.getElementById('regionCount').textContent = `${rows.length} areas`;
    tbody.innerHTML = rows.map(r => {
        const sCls = r.status === 'Good' ? 'status-good' : r.status === 'Warning' ? 'status-warning' : 'status-critical';
        return `<tr>
      <td>${r.state}</td><td>${r.city}</td><td>${r.area}</td>
      <td style="font-weight:600">${r.customer_count.toLocaleString('en-IN')}</td>
      <td>${r.avg_signal} dBm</td>
      <td>${r.avg_latency} ms</td>
      <td>${r.avg_throughput} Mbps</td>
      <td style="color:${r.churn_pct > 35 ? 'var(--red)' : 'inherit'}">${r.churn_pct}%</td>
      <td><span class="status-badge ${sCls}">${r.status}</span></td>
    </tr>`;
    }).join('');
}
function filterRegionTable() {
    const q = document.getElementById('regionSearch').value.toLowerCase();
    renderRegionTable(regionData.filter(r => r.state.toLowerCase().includes(q) || r.city.toLowerCase().includes(q) || r.area.toLowerCase().includes(q)));
}


// DROPDOWNS
async function populateStates(id) {
    const states = await api('/api/geo/states') || [];
    document.getElementById(id).innerHTML = '<option value="" disabled selected>Select state</option>' + states.map(s => `<option value="${s}">${s}</option>`).join('');
}
async function populateCities(id, state, clearId) {
    const cities = await api(`/api/geo/cities?state=${encodeURIComponent(state)}`) || [];
    const el = document.getElementById(id);
    el.innerHTML = '<option value="" disabled selected>Select city</option>' + cities.map(c => `<option value="${c}">${c}</option>`).join('');
    el.disabled = false;
    if (clearId) { const a = document.getElementById(clearId); a.innerHTML = '<option selected disabled>Select area</option>'; a.disabled = true; }
}
async function populateAreas(id, state, city) {
    const areas = await api(`/api/geo/areas?state=${encodeURIComponent(state)}&city=${encodeURIComponent(city)}`) || [];
    const el = document.getElementById(id);
    el.innerHTML = '<option value="" disabled selected>Select area</option>' + areas.map(a => `<option value="${a}">${a}</option>`).join('');
    el.disabled = false;
}

async function initChurnDropdowns() { await populateStates('churnState'); }
async function loadChurnCities() { await populateCities('churnCity', document.getElementById('churnState').value, 'churnArea'); }
async function loadChurnAreas() { await populateAreas('churnArea', document.getElementById('churnState').value, document.getElementById('churnCity').value); }
async function initForecastDropdowns() { await populateStates('fcState'); }
async function loadFcCities() { await populateCities('fcCity', document.getElementById('fcState').value, 'fcArea'); }
async function loadFcAreas() { await populateAreas('fcArea', document.getElementById('fcState').value, document.getElementById('fcCity').value); }


function selectDuration(btn) {
    document.querySelectorAll('.duration-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedDuration = parseInt(btn.dataset.days);
}

// CHURN & LATENCY PREDICTOR
async function runChurnPrediction() {
    const state = document.getElementById('churnState').value;
    const network = document.getElementById('churnNetwork').value;
    const plan = document.getElementById('churnPlan').value;
    const signal = parseInt(document.getElementById('churnSignal').value || '-85');
    const months = parseInt(document.getElementById('churnMonths').value || '12');
    const issues = parseInt(document.getElementById('churnIssues').value || '0');

    if (!state) return alert("Select state first");
    const btn = document.getElementById('churnBtn');
    btn.innerText = "Predicting..."; btn.disabled = true;
    try {
        const body = {
            operator: fbUser.operator || '',
            state: state,
            network_type: network,
            plan_type: plan,
            signal_dbm: signal,
            months_active: months,
            issues_resolved: issues
        };
        const data = await api('/api/predict_churn_latency', { method: 'POST', body: JSON.stringify(body) });

        document.getElementById('churnEmpty').style.display = 'none';
        document.getElementById('churnResults').style.display = 'flex';

        document.getElementById('rLatency').textContent = data.predicted_latency_ms + " ms";

        // Binary Churn Status (0/1)
        const binaryChurn = data.churn_probability_pct > 50 ? 1 : 0;
        const churnEl = document.getElementById('rChurnRate');
        churnEl.textContent = binaryChurn;
        churnEl.style.color = binaryChurn === 1 ? 'var(--red)' : 'var(--green)';

        // Performance Metrics Calculation
        let quality = "Poor";
        if (signal >= -70) quality = "Excellent";
        else if (signal >= -85) quality = "Good";
        else if (signal >= -100) quality = "Fair";

        document.getElementById('rSignalQuality').textContent = quality;

        const baseTp = network === "5G" ? 300 : 50;
        const signalFactor = Math.max(0.1, (signal + 110) / 50); // -110 to -60 map to 0.1 to 1.0
        const estThroughput = Math.round(baseTp * signalFactor);
        document.getElementById('rThroughput').textContent = estThroughput + " Mbps";

        const confidenceEl = document.getElementById('rConfidence');
        if (confidenceEl) {
            confidenceEl.textContent = data.confidence_score + "%";
        }

        // Hide distribution chart as risk status is removed
        const chartW = document.querySelector('#churnResults .chart-wrapper');
        if (chartW) chartW.style.display = 'none';

    } catch (e) { alert("Prediction failed"); console.error(e); }
    btn.innerText = "Run Prediction"; btn.disabled = false;
}

// FORECAST
async function runForecast() {
    const state = document.getElementById('fcState').value; const city = document.getElementById('fcCity').value; const area = document.getElementById('fcArea').value;
    if (!state || !city || !area) return alert("Select geography first");
    const btn = document.getElementById('forecastBtn'); btn.innerText = "Generating..."; btn.disabled = true;
    try {
        const data = await api('/api/forecast', { method: 'POST', body: JSON.stringify({ operator: document.getElementById('fcOperator').value, state, city, area, days: selectedDuration }) });
        document.getElementById('forecastEmpty').style.display = 'none';
        document.getElementById('forecastResults').style.display = 'flex';
        document.getElementById('fcAvg').textContent = data.avg_demand.toLocaleString();
        document.getElementById('fcPeak').textContent = data.peak_demand.toLocaleString();
        document.getElementById('fcGrowth').textContent = data.growth_trend_pct + '%';
        document.getElementById('fcPeakDate').textContent = "Peak Date: " + data.peak_date;

        if (fcChart) fcChart.destroy();
        fcChart = new Chart(document.getElementById('forecastChart'), {
            type: 'line',
            data: {
                labels: data.series.map(s => s.date),
                datasets: [{
                    label: `AI Forecast (${data.unit || 'Mbps'})`,
                    data: data.series.map(s => s.demand),
                    borderColor: '#2563eb',
                    fill: true,
                    backgroundColor: 'rgba(37,99,235,0.1)',
                    tension: 0.4, // Smoother weather-report curve
                    pointRadius: selectedDuration > 30 ? 2 : 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    intersect: false,
                    mode: 'index',
                },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `SARIMAX Prediction: ${ctx.parsed.y} ${data.unit || 'Mbps'}`
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        title: {
                            display: true,
                            text: 'Throughput (Mbps)',
                            font: { weight: 'bold', size: 12 }
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            autoSkip: true,
                            maxTicksLimit: selectedDuration === 30 ? 30 : 15 // Keeps labels descriptive but not crowded
                        }
                    }
                }
            }
        });
    } catch (e) { alert("Failed"); }
    btn.innerText = "Generate Forecast"; btn.disabled = false;
}

// OPERATORS
async function loadOperators() {
    const data = await api('/api/operators');
    if (!data) return;
    const grid = document.getElementById('opPerfCards');
    const cols = { Airtel: '#2563eb', BSNL: '#06b6d4', Jio: '#ef4444', Vi: '#f59e0b' };

    let entries = Object.entries(data);
    if (fbUser.operator) {
        entries = entries.filter(([op, info]) => op === fbUser.operator);
    }

    grid.innerHTML = entries.map(([op, info]) => `
    <div class="glass-card" style="padding:24px; min-width:300px; flex:1">
      <div style="font-weight:700;font-size:1.2rem;color:${cols[op]};margin-bottom:16px; border-bottom:2px solid ${cols[op]}44; padding-bottom:8px">${op}</div>
      <div class="op-stats-grid">
        <div class="op-stat-item">
            <span class="op-stat-label">Market Share</span>
            <span class="op-stat-value">${info.customers.toLocaleString('en-IN')} Users</span>
        </div>
        <div class="op-stat-item">
            <span class="op-stat-label">Churn Rate</span>
            <span class="op-stat-value" style="color:${info.churn_rate > 30 ? 'var(--red)' : 'var(--green)'}">${info.churn_rate}%</span>
        </div>
        <div class="op-stat-item">
            <span class="op-stat-label">Avg. Signal</span>
            <span class="op-stat-value">${info.avg_signal} dBm</span>
        </div>
        <div class="op-stat-item">
            <span class="op-stat-label">Avg. Latency</span>
            <span class="op-stat-value">${info.avg_latency} ms</span>
        </div>
        <div class="op-stat-item">
            <span class="op-stat-label">Throughput</span>
            <span class="op-stat-value">${info.avg_throughput} Mbps</span>
        </div>
        <div class="op-stat-item">
            <span class="op-stat-label">5G Adoption</span>
            <span class="op-stat-value">${Math.round((info.network_5g / (info.network_4g + info.network_5g)) * 100)}%</span>
        </div>
      </div>
    </div>`).join('');

    // Remove old chart if exists (it was removed from HTML anyway)
    if (window.churnChart) { window.churnChart.destroy(); window.churnChart = null; }
}
