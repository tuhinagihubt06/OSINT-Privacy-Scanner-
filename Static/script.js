/* ============================================================
   OSINT Privacy Scanner — script.js
   Handles API calls, DOM rendering, charts, and animations.
   ============================================================ */

"use strict";

let riskChart = null;

/* ─────────────────────────────────────────────
   SCAN
───────────────────────────────────────────── */

async function runScan() {
  const input    = document.getElementById("usernameInput");
  const btn      = document.getElementById("scanBtn");
  const btnText  = document.getElementById("scanBtnText");
  const sweep    = document.getElementById("scanSweep");
  const username = input.value.trim();

  if (!username) {
    setStatus("⚠  Username cannot be empty.", "error");
    input.focus();
    return;
  }

  // Scanning state
  btn.disabled = true;
  btn.classList.add("scanning");
  btnText.textContent = "SCANNING…";
  sweep.classList.add("active");
  setStatus(`> Initiating target scan: ${username}`, "");
  document.getElementById("resultsSection").style.display = "none";

  try {
    const res  = await fetch("/api/scan", {
      method:  "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ username }),
    });
    const data = await res.json();

    if (!res.ok) {
      setStatus(`✖  ${data.error || "Scan failed."}`, "error");
      return;
    }

    renderResults(data);
    const found = data.platforms.filter(p => p.found).length;
    setStatus(`✔  Scan complete — ${found}/${data.platforms.length} platforms detected.`, "success");
    loadDashboard();

  } catch (err) {
    setStatus("✖  Network error. Is the Flask server running?", "error");
    console.error(err);
  } finally {
    btn.disabled = false;
    btn.classList.remove("scanning");
    btnText.textContent = "INITIATE SCAN";
    sweep.classList.remove("active");
  }
}

// Enter key triggers scan
document.getElementById("usernameInput")
  .addEventListener("keydown", e => { if (e.key === "Enter") runScan(); });

/* ─────────────────────────────────────────────
   RENDER RESULTS
───────────────────────────────────────────── */

function renderResults(data) {
  const section = document.getElementById("resultsSection");
  section.style.display    = "flex";
  section.style.flexDirection = "column";
  section.style.gap        = "20px";

  // ── Score ──
  countUp("scoreNumber", 0, data.score, 1100);
  document.getElementById("scoreDenom").textContent = `/${data.max_score}`;

  const pct    = (data.score / data.max_score) * 100;
  const colMap = { High: "#ff3b5c", Moderate: "#fbbf24", Low: "#00ff88" };
  const col    = colMap[data.risk] || "#00d4ff";
  const fill   = document.getElementById("progressFill");
  fill.style.background = col;
  setTimeout(() => { fill.style.width = `${pct}%`; }, 80);

  document.getElementById("scoreSubLabel").textContent =
    `${pct.toFixed(0)}% exposure across ${data.platforms.length} platforms`;

  // ── Risk card ──
  const riskCard = document.getElementById("riskCard");
  riskCard.className = "card risk-card";
  const cls = { High: "risk-high", Moderate: "risk-mod", Low: "risk-low" };
  if (cls[data.risk]) riskCard.classList.add(cls[data.risk]);

  const icons = { High: "◉", Moderate: "◎", Low: "○" };
  document.getElementById("riskIcon").textContent  = icons[data.risk] || "◉";
  document.getElementById("riskLevel").textContent = data.risk.toUpperCase();

  const descs = {
    High:     "Username widely detected across multiple platforms. Significant cross-platform exposure risk.",
    Moderate: "Username found on several platforms. Moderate exposure — review your profile settings.",
    Low:      "Username found on few platforms. Low exposure risk detected.",
  };
  document.getElementById("riskDesc").textContent = descs[data.risk] || "";

  // ── Platform tiles ──
  const grid = document.getElementById("platformsGrid");
  grid.innerHTML = "";
  data.platforms.forEach((p, i) => {
    const tile = document.createElement("div");
    tile.className = `platform-tile ${p.found ? "found" : "missing"}`;
    tile.innerHTML = `
      <span class="tile-name">${esc(p.platform)}</span>
      <span class="tile-status">${p.found ? "✅" : "❌"}</span>
    `;
    grid.appendChild(tile);
    setTimeout(() => tile.classList.add("show"), 70 * i + 120);
  });

  // ── Recommendations ──
  const recs = {
    High: [
      "→  Change your username to something unique and non-identifiable.",
      "→  Use different usernames across platforms to prevent identity correlation.",
      "→  Strip personal info (real name, birthdate) from all profiles.",
      "→  Review and tighten privacy settings on every platform found.",
      "→  Enable two-factor authentication on all accounts immediately.",
    ].join("\n"),
    Moderate: [
      "→  Review visibility settings on platforms where you were detected.",
      "→  Change your username if it contains any personal information.",
      "→  Check for linked accounts or shared data that could expose you.",
      "→  Use a unique, strong password on each platform.",
    ].join("\n"),
    Low: [
      "→  Your exposure is low — maintain good habits going forward.",
      "→  Use strong, unique passwords for each account.",
      "→  Enable two-factor authentication wherever it's available.",
      "→  Periodically audit your profiles for any sensitive information.",
    ].join("\n"),
  };
  document.getElementById("recsBody").textContent = recs[data.risk] || "";

  section.scrollIntoView({ behavior: "smooth", block: "start" });
}

/* ─────────────────────────────────────────────
   DASHBOARD
───────────────────────────────────────────── */

async function loadDashboard() {
  await Promise.all([loadStats(), loadHistory()]);
}

async function loadStats() {
  try {
    const res  = await fetch("/api/stats");
    const data = await res.json();

    document.getElementById("statTotal").textContent = data.total_scans ?? "—";

    const bd = {};
    (data.risk_breakdown || []).forEach(r => { bd[r.risk] = r.count; });
    document.getElementById("statHigh").textContent = bd["High"]     ?? 0;
    document.getElementById("statMod").textContent  = bd["Moderate"] ?? 0;
    document.getElementById("statLow").textContent  = bd["Low"]      ?? 0;

    renderChart(bd);
  } catch (err) {
    console.error("Stats load error:", err);
  }
}

async function loadHistory(username = null) {
  try {
    const url = username
      ? `/api/search?username=${encodeURIComponent(username)}`
      : "/api/history?limit=10";
    const res  = await fetch(url);
    const rows = await res.json();
    renderTable(Array.isArray(rows) ? rows : []);
  } catch (err) {
    console.error("History load error:", err);
  }
}

async function searchHistory() {
  const q = document.getElementById("historySearch").value.trim();
  await loadHistory(q || null);
}

document.getElementById("historySearch")
  .addEventListener("keydown", e => { if (e.key === "Enter") searchHistory(); });

function renderTable(rows) {
  const tbody = document.getElementById("historyBody");
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="4" class="table-empty">No records found.</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td>${esc(r.username)}</td>
      <td>${r.score}</td>
      <td><span class="rbadge ${esc(r.risk)}">${esc(r.risk)}</span></td>
      <td>${esc(r.timestamp)}</td>
    </tr>
  `).join("");
}

function renderChart(bd) {
  const ctx    = document.getElementById("riskChart").getContext("2d");
  const labels = ["High", "Moderate", "Low"];
  const values = [bd["High"] || 0, bd["Moderate"] || 0, bd["Low"] || 0];
  const colors = ["#ff3b5c", "#fbbf24", "#00ff88"];

  if (riskChart) riskChart.destroy();

  riskChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data:                  values,
        backgroundColor:       colors.map(c => c + "28"),
        borderColor:           colors,
        borderWidth:           2,
        hoverBackgroundColor:  colors.map(c => c + "55"),
      }]
    },
    options: {
      responsive:        false,
      cutout:            "72%",
      animation:         { duration: 900, easing: "easeOutQuart" },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            color:          "#4a6080",
            font:           { family: "'JetBrains Mono', monospace", size: 11 },
            padding:        14,
            usePointStyle:  true,
          }
        },
        tooltip: {
          backgroundColor: "#0f1623",
          borderColor:     "#1c2a3a",
          borderWidth:     1,
          titleColor:      "#c9d8e8",
          bodyColor:       "#4a6080",
          titleFont:       { family: "'JetBrains Mono', monospace" },
          bodyFont:        { family: "'JetBrains Mono', monospace" },
        }
      }
    }
  });
}

/* ─────────────────────────────────────────────
   UTILITIES
───────────────────────────────────────────── */

function setStatus(msg, type = "") {
  const el      = document.getElementById("statusLine");
  el.textContent = msg;
  el.className   = `status-line ${type}`.trim();
}

// Animated number counter
function countUp(id, from, to, duration) {
  const el    = document.getElementById(id);
  const start = performance.now();
  function step(now) {
    const t   = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(from + (to - from) * easeOutCubic(t));
    if (t < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function easeOutCubic(t) { return 1 - Math.pow(1 - t, 3); }

// Sanitise HTML to prevent XSS
function esc(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

/* ─────────────────────────────────────────────
   INIT
───────────────────────────────────────────── */
document.addEventListener("DOMContentLoaded", loadDashboard);