/*  ═══════════════════════════════════════════════════════
    AI-Powered Preventive Healthcare Score System
    Frontend JavaScript — API helpers, charts, UI logic
    ═══════════════════════════════════════════════════════ */

const API_BASE = window.location.origin;

// ─── API Helper ──────────────────────────────────────────

async function api(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
        credentials: "include",
        headers: { "Content-Type": "application/json" },
        ...options,
    };
    try {
        const res = await fetch(url, config);
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.error || `Request failed (${res.status})`);
        }
        return data;
    } catch (err) {
        if (err.message.includes("Failed to fetch") || err.message.includes("NetworkError")) {
            throw new Error("Cannot connect to server. Make sure the backend is running on port 5000.");
        }
        throw err;
    }
}

// ─── Auth Helpers ────────────────────────────────────────

async function checkAuth() {
    try {
        const data = await api("/check-session");
        return data.authenticated ? data.user : null;
    } catch {
        return null;
    }
}

async function requireAuth() {
    const user = await checkAuth();
    if (!user) {
        window.location.href = "login.html";
        return null;
    }
    return user;
}

async function handleLogout() {
    try {
        await api("/logout", { method: "POST" });
    } catch { }
    window.location.href = "login.html";
}

// ─── Toast Notifications ────────────────────────────────

function showToast(message, type = "info") {
    let container = document.querySelector(".toast-container");
    if (!container) {
        container = document.createElement("div");
        container.className = "toast-container";
        document.body.appendChild(container);
    }
    const toast = document.createElement("div");
    toast.className = `toast alert-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(-10px)";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ─── Alert Message ──────────────────────────────────────

function showAlert(containerId, message, type = "error") {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = `<div class="alert alert-${type}">${type === "error" ? "⚠️" : type === "success" ? "✅" : "ℹ️"} ${message}</div>`;
    setTimeout(() => { container.innerHTML = ""; }, 5000);
}

// ─── BMI Calculator ─────────────────────────────────────

function calculateBMI(height, weight) {
    if (!height || !weight || height <= 0) return { bmi: 0, category: "N/A" };
    const heightM = height / 100;
    const bmi = weight / (heightM * heightM);
    let category;
    if (bmi < 18.5) category = "Underweight";
    else if (bmi < 25) category = "Normal";
    else if (bmi < 30) category = "Overweight";
    else category = "Obese";
    return { bmi: Math.round(bmi * 10) / 10, category };
}

// ─── Score Color ────────────────────────────────────────

function getScoreColor(score) {
    if (score >= 80) return "#10b981";
    if (score >= 60) return "#f59e0b";
    if (score >= 40) return "#ef4444";
    return "#dc2626";
}

function getRiskClass(riskLevel) {
    const map = {
        "Healthy": "risk-healthy",
        "Moderate": "risk-moderate",
        "Risk": "risk-risk",
        "High Risk": "risk-high-risk"
    };
    return map[riskLevel] || "risk-moderate";
}

// ─── Score Circle Renderer ──────────────────────────────

function renderScoreCircle(containerId, score, label = "Health Score") {
    const container = document.getElementById(containerId);
    if (!container) return;
    const color = getScoreColor(score);
    const circumference = 2 * Math.PI * 60;
    const offset = circumference - (score / 100) * circumference;

    container.innerHTML = `
        <div class="score-circle">
            <svg viewBox="0 0 140 140">
                <circle class="bg" cx="70" cy="70" r="60"/>
                <circle class="progress" cx="70" cy="70" r="60"
                    stroke="${color}"
                    stroke-dasharray="${circumference}"
                    stroke-dashoffset="${circumference}"
                    style="transition: stroke-dashoffset 1.5s ease"/>
            </svg>
            <div class="score-text">
                <div class="score-number" style="color:${color}">${score}</div>
                <div class="score-label">${label}</div>
            </div>
        </div>`;

    // Animate
    requestAnimationFrame(() => {
        const circle = container.querySelector(".progress");
        if (circle) circle.style.strokeDashoffset = offset;
    });
}

// ─── Charts ─────────────────────────────────────────────

let scoreChart = null;
let radarChart = null;

function renderScoreTrendChart(canvasId, history) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !history.length) return;

    if (scoreChart) scoreChart.destroy();

    const labels = history.map((h) => {
        const d = new Date(h.timestamp);
        return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    });
    const scores = history.map((h) => h.score);

    scoreChart = new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: [{
                label: "Health Score",
                data: scores,
                borderColor: "#3b82f6",
                backgroundColor: "rgba(59,130,246,0.1)",
                fill: true,
                tension: 0.4,
                pointBackgroundColor: "#3b82f6",
                pointBorderColor: "#fff",
                pointBorderWidth: 2,
                pointRadius: 5,
                pointHoverRadius: 7,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(17,24,39,0.95)",
                    titleColor: "#f1f5f9",
                    bodyColor: "#94a3b8",
                    borderColor: "rgba(255,255,255,0.1)",
                    borderWidth: 1,
                    padding: 12,
                    cornerRadius: 8,
                },
            },
            scales: {
                y: {
                    min: 0, max: 100,
                    grid: { color: "rgba(255,255,255,0.04)" },
                    ticks: { color: "#64748b", font: { size: 11 } },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748b", font: { size: 11 } },
                },
            },
        },
    });
}

function renderRadarChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    if (radarChart) radarChart.destroy();

    // Normalize values to 0-100 scale
    const normalize = (val, min, max) => Math.min(100, Math.max(0, ((val - min) / (max - min)) * 100));

    const metrics = {
        "Sleep": normalize(parseFloat(data.sleep_hours || 0), 0, 10),
        "Exercise": normalize(parseFloat(data.exercise_minutes || 0), 0, 120),
        "Steps": normalize(parseFloat(data.steps_per_day || 0), 0, 15000),
        "Water": normalize(parseFloat(data.water_intake || 0), 0, 5),
        "Heart Rate": normalize(100 - Math.abs(72 - parseFloat(data.heart_rate || 72)), 0, 100),
        "BMI": normalize(100 - Math.abs(22 - parseFloat(data.bmi || 22)) * 4, 0, 100),
    };

    radarChart = new Chart(canvas, {
        type: "radar",
        data: {
            labels: Object.keys(metrics),
            datasets: [{
                label: "Health Metrics",
                data: Object.values(metrics),
                backgroundColor: "rgba(139,92,246,0.15)",
                borderColor: "#8b5cf6",
                borderWidth: 2,
                pointBackgroundColor: "#8b5cf6",
                pointBorderColor: "#fff",
                pointBorderWidth: 2,
                pointRadius: 4,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                r: {
                    min: 0, max: 100,
                    ticks: { display: false },
                    grid: { color: "rgba(255,255,255,0.06)" },
                    pointLabels: { color: "#94a3b8", font: { size: 12 } },
                    angleLines: { color: "rgba(255,255,255,0.06)" },
                },
            },
        },
    });
}

// ─── Dashboard Rendering ────────────────────────────────

function renderDashboard(data) {
    // Score circle
    renderScoreCircle("scoreCircle", data.latest.score);

    // Risk badge
    const riskEl = document.getElementById("riskBadge");
    if (riskEl) {
        riskEl.className = `risk-badge ${getRiskClass(data.latest.risk_level)}`;
        riskEl.textContent = data.latest.risk_level;
    }

    // Summary
    const summaryEl = document.getElementById("healthSummary");
    if (summaryEl) summaryEl.textContent = data.latest.summary || "";

    // Metric cards
    setMetric("bmiValue", data.latest.bmi, "");
    setMetric("bpValue", data.latest.blood_pressure, "");
    setMetric("sugarValue", data.latest.sugar_level, "mg/dL");
    setMetric("hrValue", data.latest.heart_rate, "bpm");

    // Trackers
    setMetric("stepsValue", Math.round(data.latest.steps_per_day || 0), "");
    setMetric("waterValue", data.latest.water_intake, "L");
    setMetric("sleepValue", data.latest.sleep_hours, "hrs");
    setMetric("exerciseValue", data.latest.exercise_minutes, "min");

    // Progress bars
    setProgress("stepsBar", (data.latest.steps_per_day || 0) / 10000 * 100, "#10b981");
    setProgress("waterBar", (data.latest.water_intake || 0) / 3 * 100, "#3b82f6");
    setProgress("sleepBar", (data.latest.sleep_hours || 0) / 9 * 100, "#8b5cf6");
    setProgress("exerciseBar", (data.latest.exercise_minutes || 0) / 60 * 100, "#f59e0b");

    // Charts
    renderScoreTrendChart("scoreTrendChart", data.history);
    renderRadarChart("radarChart", data.latest);

    // Recommendations
    renderRecommendations("recList", data.latest.recommendations || []);

    // Doctor recommendations
    renderDoctorRecs("doctorRecs", data.doctor_recommendations || []);
}

function setMetric(id, value, unit) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = `${value ?? '—'}<span class="metric-unit"> ${unit}</span>`;
}

function setProgress(id, percent, color) {
    const el = document.getElementById(id);
    if (el) {
        el.style.width = Math.min(100, Math.max(0, percent)) + "%";
        el.style.background = color;
    }
}

function renderRecommendations(id, recs) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!recs.length) {
        el.innerHTML = '<li>No recommendations yet.</li>';
        return;
    }
    el.innerHTML = recs.map((r) => `<li>${r}</li>`).join("");
}

function renderDoctorRecs(id, recs) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!recs.length) {
        el.innerHTML = '<p style="color:var(--text-secondary)">No recommendations at this time.</p>';
        return;
    }
    el.innerHTML = recs.map((r) => `
        <div class="doctor-card">
            <div class="doc-icon">🩺</div>
            <div class="doc-info">
                <h4>${r.specialist} <span class="urgency-badge urgency-${r.urgency}">${r.urgency}</span></h4>
                <p>${r.reason}</p>
            </div>
        </div>`).join("");
}

// ─── Report Rendering ───────────────────────────────────

function renderReport(report) {
    // Trend badge
    const trendEl = document.getElementById("trendBadge");
    if (trendEl) {
        const icons = { improving: "📈", stable: "➡️", declining: "📉" };
        trendEl.className = `trend-badge trend-${report.overall_trend}`;
        trendEl.textContent = `${icons[report.overall_trend] || ""} ${report.overall_trend}`;
    }

    // Stats
    setElText("avgScore", Math.round(report.average_score));
    setElText("totalEntries", report.entries?.length || 0);
    setElText("reportMonth", report.month);

    // Summary
    setElText("reportSummary", report.summary || "");

    // Improvements
    renderListItems("improvements", report.key_improvements, "✅");
    renderListItems("concerns", report.areas_of_concern, "⚠️");
    renderListItems("goals", report.next_month_goals, "");

    // Doctor visit
    const docVisit = document.getElementById("doctorVisit");
    if (docVisit) {
        if (report.doctor_visit_recommended) {
            docVisit.innerHTML = `<div class="alert alert-error">🏥 Doctor visit recommended: ${report.doctor_visit_reason}</div>`;
        } else {
            docVisit.innerHTML = `<div class="alert alert-success">✅ No immediate doctor visit needed. Keep up the good work!</div>`;
        }
    }

    // Report chart
    if (report.entries?.length) {
        renderScoreTrendChart("reportChart", report.entries);
    }
}

function setElText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function renderListItems(id, items, icon) {
    const el = document.getElementById(id);
    if (!el) return;
    if (!items?.length) {
        el.innerHTML = "<li>No data available.</li>";
        return;
    }
    el.innerHTML = items.map((item) => `<li>${icon ? icon + " " : ""}${item}</li>`).join("");
}

// ─── Chatbot ────────────────────────────────────────────

let chatHistory = [];

async function sendChatMessage() {
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("chatMessages");
    if (!input || !messages) return;

    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addChatBubble(messages, message, "user");
    input.value = "";
    chatHistory.push({ role: "user", content: message });

    // Typing indicator
    const typing = document.createElement("div");
    typing.className = "chat-bubble bot";
    typing.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
        const data = await api("/chatbot", {
            method: "POST",
            body: JSON.stringify({ message, history: chatHistory }),
        });
        typing.remove();
        addChatBubble(messages, data.response, "bot");
        chatHistory.push({ role: "assistant", content: data.response });
    } catch (err) {
        typing.remove();
        addChatBubble(messages, "Sorry, I couldn't process that. " + err.message, "bot");
    }
}

function addChatBubble(container, text, role) {
    const bubble = document.createElement("div");
    bubble.className = `chat-bubble ${role}`;
    if (role === "bot") {
        bubble.innerHTML = `<div class="bot-label">🤖 AI Health Assistant</div>${formatBotText(text)}`;
    } else {
        bubble.textContent = text;
    }
    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
}

function formatBotText(text) {
    // Simple markdown-like formatting
    return text
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/\n/g, "<br>");
}
