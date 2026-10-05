from flask import Flask, request, jsonify, render_template_string
import os
import json
import time

app = Flask(__name__)

# In-memory mock cloud store (In production, replace with PostgreSQL/MongoDB/Firebase)
CLOUD_WORKSPACES = {}

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>YouTube Research & Intelligence Tool</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

  :root {
    --glass-fill: rgba(255, 255, 255, 0.07);
    --glass-fill-strong: rgba(255, 255, 255, 0.12);
    --glass-border: rgba(255, 255, 255, 0.14);
    --glass-border-soft: rgba(255, 255, 255, 0.07);
    --ink: #f5f5f7;
    --ink-dim: rgba(245, 245, 247, 0.55);
    --ink-faint: rgba(245, 245, 247, 0.32);
    --accent: #0a84ff;
    --accent-2: #64d2ff;
    --success: #32d74b;
    --danger: #ff453a;
    --radius-lg: 28px;
    --radius-md: 18px;
    --radius-sm: 12px;
  }

  body {
    background: #030304;
    color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 40px 20px 40px;
    position: relative;
    overflow-x: hidden;
  }

  body::before, body::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(130px);
    z-index: -1;
    opacity: 0.45;
    animation: drift 18s infinite alternate ease-in-out;
  }
  body::before { top: -12%; left: -14%; width: 46vw; height: 46vw; background: #5e5ce6; }
  body::after { bottom: -14%; right: -12%; width: 42vw; height: 42vw; background: #bf5af2; animation-delay: -6s; }
  @keyframes drift { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(4%, 4%) scale(1.12); } }

  .brand { text-align: center; margin-bottom: 24px; }
  .brand-mark { display: block; font-size: 30px; font-weight: 700; letter-spacing: -0.02em; color: #fff; }
  .brand-sub { display: block; margin-top: 5px; font-size: 12px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-faint); }

  .box { width: 100%; max-width: 960px; }

  .glass {
    position: relative;
    background: var(--glass-fill);
    -webkit-backdrop-filter: blur(28px) saturate(160%);
    backdrop-filter: blur(28px) saturate(160%);
    border: 1px solid var(--glass-border);
    box-shadow: 0 1px 0 rgba(255,255,255,0.14) inset, 0 20px 50px rgba(0,0,0,0.45);
  }
  .glass::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    padding: 1px;
    background: linear-gradient(180deg, rgba(255,255,255,0.35), rgba(255,255,255,0) 40%);
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
  }

  .glass-panel { border-radius: var(--radius-lg); padding: 24px; margin-top: 16px; }

  .quick-row { display: flex; align-items: center; gap: 10px; width: 100%; max-width: 750px; margin: 0 auto;}

  .pill-glass {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border-radius: 999px;
    padding: 12px 18px;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink-dim);
    cursor: pointer;
    transition: all 0.2s;
  }
  .pill-glass:active { transform: scale(0.97); }
  .pill-glass.mode-active { color: #fff; background: var(--accent) !important; border-color: transparent; }

  .icon-glass {
    flex-shrink: 0;
    width: 44px;
    height: 44px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--ink-dim);
    cursor: pointer;
    transition: color 0.2s, transform 0.15s;
  }
  .icon-glass:hover { color: #fff; }
  .icon-glass:active { transform: scale(0.92); }
  .icon-glass.is-open { color: var(--accent-2); }
  .icon-glass svg { width: 18px; height: 18px; }

  .drawer-panel {
    display: none;
    background: rgba(0,0,0,0.45);
    border-radius: var(--radius-md);
    padding: 18px;
    margin-bottom: 20px;
    border: 1px solid var(--glass-border-soft);
    max-width: 750px;
    margin-left: auto; margin-right: auto;
  }
  .panel-head {
    font-size: 12px; font-weight: 700; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--accent-2); justify-content: space-between; display: flex; margin-bottom: 14px;
  }
  .panel-head span.action { color: var(--ink-dim); cursor: pointer; text-transform: none; letter-spacing: 0; font-size: 12px; }
  .panel-head span.action:hover { color: #fff; }

  .form-group { margin-bottom: 14px; }
  .form-group:last-child { margin-bottom: 0; }
  .form-group label { display: block; font-size: 11px; font-weight: 600; color: var(--ink-dim); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.06em; }
  
  .drawer-panel input[type="text"], .drawer-panel input[type="password"], .drawer-panel textarea, .drawer-panel select {
    width: 100%; background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border-soft);
    color: var(--ink); font-family: inherit; font-size: 12px;
    padding: 10px 12px; outline: none; border-radius: var(--radius-sm); transition: border 0.2s;
  }
  .drawer-panel textarea { height: 60px; resize: vertical; font-family: ui-monospace, SFMono-Regular, monospace; }
  .drawer-panel select {
    appearance: none; -webkit-appearance: none;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23a1a1a6' stroke-width='2'><polyline points='6 9 12 15 18 9'></polyline></svg>");
    background-repeat: no-repeat;
    background-position: right 12px center;
  }
  .drawer-panel input:focus, .drawer-panel textarea:focus, .drawer-panel select:focus { border-color: var(--accent); }

  .btn-row { display: flex; gap: 8px; margin-top: 10px; }
  .btn-sm {
    background: rgba(255,255,255,0.12); color: #fff; border: 1px solid var(--glass-border-soft);
    padding: 8px 14px; font-size: 12px; font-weight: 600; border-radius: 8px; cursor: pointer; transition: background 0.2s;
  }
  .btn-sm:hover { background: rgba(255,255,255,0.22); }
  .btn-sm.primary { background: var(--accent); border-color: transparent; }

  .main-input {
    width: 100%; max-width: 750px; display: block; margin: 0 auto 16px auto;
    background: rgba(0,0,0,0.28); border: 1px solid var(--glass-border-soft);
    color: var(--ink); padding: 14px 16px; font-family: inherit; font-size: 14px; line-height: 1.5;
    border-radius: var(--radius-md); outline: none;
    transition: all 0.2s; box-shadow: inset 0 2px 6px rgba(0,0,0,0.25);
  }
  .main-input:focus { border-color: rgba(255,255,255,0.24); background: rgba(0,0,0,0.42); box-shadow: 0 0 0 4px rgba(10,132,255,0.12); }
  .main-input::placeholder { color: var(--ink-faint); }

  .filter-bar {
    display: flex; gap: 10px; width: 100%; max-width: 750px; margin: 0 auto 16px auto; justify-content: center; flex-wrap: wrap;
  }
  .filter-item { flex: 1; min-width: 180px; }
  .filter-item label { display: block; font-size: 10px; font-weight: 600; text-transform: uppercase; color: var(--ink-dim); margin-bottom: 4px; }
  .filter-item select {
    width: 100%; background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border-soft); color: var(--ink);
    padding: 8px 12px; border-radius: var(--radius-sm); font-size: 12px; outline: none;
  }

  button.solid {
    background: #fff; color: #000; padding: 14px 24px; font-size: 14px; font-weight: 600;
    border-radius: 16px; width: 100%; max-width: 750px; display: block; margin: 0 auto;
  }
  button.solid:hover { opacity: 0.9; transform: scale(0.99); }
  button.solid:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }

  .status { font-size: 13px; font-weight: 500; color: var(--ink-dim); min-height: 20px; margin-top: 16px; text-align: center; }
  .status.active { color: var(--accent-2); }
  .status.error { color: var(--danger); }
  .status.success { color: var(--success); }

  .list-header {
    font-size: 11px; font-weight: 600; color: var(--ink-dim); text-transform: uppercase; letter-spacing: 0.06em;
    margin-top: 28px; margin-bottom: 12px; display: none; justify-content: space-between; align-items: center;
  }

  .table-container {
    width: 100%;
    overflow-x: auto;
    max-height: 520px;
    overflow-y: auto;
    border-radius: var(--radius-sm);
    background: rgba(255,255,255,0.03);
    border: 1px solid var(--glass-border-soft);
  }
  table.glass-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
    text-align: left;
    white-space: nowrap;
  }
  .glass-table th {
    position: sticky;
    top: 0;
    background: rgba(25, 25, 30, 0.92);
    backdrop-filter: blur(12px);
    color: var(--ink-dim);
    font-weight: 600;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    z-index: 2;
  }
  
  .sortable { cursor: pointer; user-select: none; transition: background 0.2s, color 0.2s; }
  .sortable:hover { background: rgba(255,255,255,0.12); color: #fff; }
  
  .glass-table td {
    padding: 12px 14px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: var(--ink);
  }
  .glass-table tr:hover td { background: rgba(255,255,255,0.05); }
  .trunc { max-width: 180px; overflow: hidden; text-overflow: ellipsis; }

  .progress-bar-bg {
    width: 50px; height: 6px; background: rgba(255,255,255,0.15); 
    border-radius: 4px; display: inline-block; vertical-align: middle; margin-right: 6px; overflow: hidden;
  }
  .progress-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; }
  .progress-val { font-size: 11px; color: var(--ink-dim); }

  .table-btn {
    font-size: 11px; font-weight: 600; padding: 5px 10px; border-radius: 6px;
    background: rgba(255,255,255,0.1); color: #fff; text-decoration: none; transition: background 0.2s;
  }
  .table-btn:hover { background: rgba(255,255,255,0.22); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
</style>
</head>
<body>

<div class="brand">
  <span class="brand-mark">Research Tool</span>
  <span class="brand-sub">YouTube Channel &amp; Keyword Intelligence Engine</span>
</div>

<div class="quick-row">
  <div class="pill-glass glass mode-active" id="modeKeywordBtn" onclick="setMode('keyword')">🔍 Keyword Search</div>
  <div class="pill-glass glass" id="modeChannelBtn" onclick="setMode('channel')">📺 Channel Analysis</div>
  <div class="pill-glass glass" id="modeTrendingBtn" onclick="setMode('trending')">⚡ Trending</div>
  
  <div class="icon-glass glass" id="cloudBtn" onclick="toggleDrawer('cloudPanel')" title="Cloud Workspace Sync">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"></path></svg>
  </div>
  <div class="icon-glass glass" id="settingsBtn" onclick="toggleDrawer('settingsPanel')" title="API Settings">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
  </div>
</div>

<div class="box">
  <div class="glass-panel glass">
    <!-- SETTINGS DRAWER -->
    <div class="drawer-panel" id="settingsPanel">
      <div class="panel-head">
        <span>⚙️ API &amp; Search Settings</span>
        <span class="action" onclick="saveSettings()">Save &amp; Close</span>
      </div>

      <div class="form-group">
        <label>YouTube API v3 Key</label>
        <textarea id="ytApiKey" placeholder="AIzaSy..."></textarea>
      </div>

      <div class="form-group">
        <label>Default Max Results Per Search</label>
        <select id="maxResultsSelect">
          <option value="10">10</option>
          <option value="20" selected>20</option>
          <option value="50">50</option>
          <option value="100">100</option>
        </select>
      </div>
    </div>

    <!-- CLOUD WORKSPACE DRAWER -->
    <div class="drawer-panel" id="cloudPanel">
      <div class="panel-head">
        <span>☁️ Cloud Workspace Login &amp; Sync</span>
        <span class="action" onclick="toggleDrawer('cloudPanel')">Close</span>
      </div>

      <div class="form-group">
        <label>Cloud User Code / Key</label>
        <input type="text" id="cloudUserKey" placeholder="Enter your Workspace ID or Secret Key">
      </div>

      <div class="btn-row">
        <button class="btn-sm primary" onclick="cloudLogin()">Login / Sync Cloud</button>
        <button class="btn-sm" onclick="exportWorkspace()">Export Workspace (JSON)</button>
        <button class="btn-sm" onclick="importWorkspace()">Import Workspace (JSON)</button>
        <input type="file" id="importFileInput" style="display:none;" accept=".json" onchange="handleFileImport(event)">
      </div>
      <div id="cloudStatus" style="font-size:11px; margin-top:8px; color:var(--accent-2);"></div>
    </div>

    <!-- MAIN INPUT FIELD -->
    <input type="text" id="mainInput" class="main-input" placeholder="e.g. minecraft speedrun, true crime, budget travel">

    <!-- CHANNEL / ANALYSIS SPECIFIC FILTERS -->
    <div class="filter-bar" id="filterBar">
      <div class="filter-item">
        <label>Time Horizon Filter</label>
        <select id="timeHorizonSelect">
          <option value="12h">Last 12 Hours</option>
          <option value="24h" selected>Last 24 Hours (Today)</option>
          <option value="7d">Last 7 Days (Last Week)</option>
          <option value="30d">Last 30 Days</option>
          <option value="all">All Available</option>
        </select>
      </div>

      <div class="filter-item" id="videoLimitBox">
        <label>Channel Analysis Mode</label>
        <select id="channelFetchMode">
          <option value="time" selected>Use Time Window (12h, 24h, 7d...)</option>
          <option value="10">Last 10 Videos Only</option>
          <option value="20">Last 20 Videos Only</option>
          <option value="50">Last 50 Videos Only</option>
        </select>
      </div>
    </div>

    <button class="solid" id="actionBtn" onclick="runSearch()">Find Exploding Content</button>

    <div class="status" id="mainStatus">Ready to search.</div>

    <div class="list-header" id="listHeader">
      <span id="listCount">0 Videos Found</span>
    </div>
    
    <div id="resultsTableContainer"></div>
  </div>
</div>

<script>
  const API_BASE = 'https://www.googleapis.com/youtube/v3';
  let mode = 'keyword'; // 'keyword', 'channel', 'trending'
  
  // --- GLOBALS FOR SORTING ---
  window.lastFetchedResults = [];
  window.sortState = { col: null, dir: 0 }; // 0: default, 1: desc (high-to-low), 2: asc (low-to-high)

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("ytApiKey").value = localStorage.getItem("yt_api_key") || "";
    document.getElementById("maxResultsSelect").value = localStorage.getItem("yt_max_results") || "20";
    document.getElementById("cloudUserKey").value = localStorage.getItem("yt_cloud_key") || "";
    updateModeUI();
  });

  function toggleDrawer(panelId) {
    const panel = document.getElementById(panelId);
    const isOpen = panel.style.display === "block";
    panel.style.display = isOpen ? "none" : "block";
  }

  function saveSettings() {
    localStorage.setItem("yt_api_key", document.getElementById("ytApiKey").value.trim());
    localStorage.setItem("yt_max_results", document.getElementById("maxResultsSelect").value);
    setStatus("Settings saved.", "success");
    toggleDrawer("settingsPanel");
  }

  function getApiKey() {
    return localStorage.getItem("yt_api_key") || document.getElementById("ytApiKey").value.trim();
  }

  function setMode(newMode) {
    mode = newMode;
    updateModeUI();
  }

  function updateModeUI() {
    document.getElementById("modeKeywordBtn").classList.toggle("mode-active", mode === "keyword");
    document.getElementById("modeChannelBtn").classList.toggle("mode-active", mode === "channel");
    document.getElementById("modeTrendingBtn").classList.toggle("mode-active", mode === "trending");

    const input = document.getElementById("mainInput");
    const btn = document.getElementById("actionBtn");

    if (mode === "trending") {
      input.style.display = "none";
      btn.textContent = "Refresh Trending Content";
    } else if (mode === "channel") {
      input.style.display = "block";
      input.placeholder = "Enter Channel Handles or IDs separated by commas (e.g. @MrBeast, @Veritasium, UC...)";
      btn.textContent = "Analyze Channels";
    } else {
      input.style.display = "block";
      input.placeholder = "e.g. minecraft speedrun, true crime, budget travel";
      btn.textContent = "Find Exploding Content";
    }
  }

  function setStatus(msg, type = '') {
    const el = document.getElementById('mainStatus');
    el.textContent = msg;
    el.className = 'status ' + type;
  }

  function getPublishedAfterISO(horizonKey) {
    const now = Date.now();
    let millis = 0;
    if (horizonKey === '12h') millis = 12 * 60 * 60 * 1000;
    else if (horizonKey === '24h') millis = 24 * 60 * 60 * 1000;
    else if (horizonKey === '7d') millis = 7 * 24 * 60 * 60 * 1000;
    else if (horizonKey === '30d') millis = 30 * 24 * 60 * 60 * 1000;
    else return null;

    return new Date(now - millis).toISOString();
  }

  async function runSearch() {
    const apiKey = getApiKey();
    if (!apiKey) {
      setStatus("Please add your YouTube API key in Settings first.", "error");
      toggleDrawer("settingsPanel");
      return;
    }

    const btn = document.getElementById('actionBtn');
    btn.disabled = true;

    try {
      if (mode === 'trending') {
        await fetchTrending(apiKey);
      } else if (mode === 'channel') {
        const inputVal = document.getElementById('mainInput').value.trim();
        if (!inputVal) {
          setStatus("Please enter at least one Channel handle or ID.", "error");
          btn.disabled = false;
          return;
        }
        await analyzeChannelsBatched(apiKey, inputVal);
      } else {
        const keyword = document.getElementById('mainInput').value.trim();
        if (!keyword) {
          setStatus("Please enter a keyword first.", "error");
          btn.disabled = false;
          return;
        }
        await fetchKeywordSearch(apiKey, keyword);
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`, "error");
    }

    btn.disabled = false;
  }

  // --- HELPER FOR BATCH CHUNKING (Fixes 388 channels drop/crash) ---
  function chunkArray(array, chunkSize) {
    const results = [];
    for (let i = 0; i < array.length; i += chunkSize) {
      results.push(array.slice(i, i + chunkSize));
    }
    return results;
  }

  // --- BATCHED CHANNEL ANALYSIS (Fixes 388 channels timeout) ---
  async function analyzeChannelsBatched(apiKey, channelsInput) {
    const rawList = channelsInput.split(',').map(s => s.trim()).filter(Boolean);
    if (rawList.length === 0) return;

    setStatus(`Processing ${rawList.length} channels in safe batches...`, "active");

    const horizonKey = document.getElementById('timeHorizonSelect').value;
    const publishedAfter = getPublishedAfterISO(horizonKey);
    const fetchMode = document.getElementById('channelFetchMode').value;
    const maxLimit = fetchMode === 'time' ? 50 : parseInt(fetchMode, 10);

    let allVideoItems = [];
    const chunks = chunkArray(rawList, 50); // Process in batches of 50 to prevent connection timeouts

    let processedCount = 0;

    for (let i = 0; i < chunks.length; i++) {
      const chunk = chunks[i];
      setStatus(`Analyzing channels ${processedCount + 1} to ${Math.min(processedCount + chunk.length, rawList.length)} of ${rawList.length}...`, "active");

      for (const channelRef of chunk) {
        try {
          let channelId = channelRef;
          // Resolve handle if needed
          if (channelRef.startsWith('@')) {
            const res = await fetch(`${API_BASE}/search?part=snippet&type=channel&q=${encodeURIComponent(channelRef)}&key=${apiKey}`);
            const data = await res.json();
            if (data.items && data.items.length > 0) {
              channelId = data.items[0].snippet.channelId;
            }
          }

          let searchUrl = `${API_BASE}/search?part=snippet&channelId=${channelId}&type=video&order=date&maxResults=${maxLimit}&key=${apiKey}`;
          if (fetchMode === 'time' && publishedAfter) {
            searchUrl += `&publishedAfter=${publishedAfter}`;
          }

          const vRes = await fetch(searchUrl);
          const vData = await vRes.json();
          if (vData.items) {
            allVideoItems.push(...vData.items);
          }
        } catch (e) {
          console.warn(`Failed fetching channel ${channelRef}:`, e);
        }
      }

      processedCount += chunk.length;
      // Small pause to prevent rate limit spikes & connection drops
      await new Promise(r => setTimeout(r, 150));
    }

    if (allVideoItems.length === 0) {
      setStatus("No recent videos found for the specified channels/time period.", "error");
      window.lastFetchedResults = [];
      renderTable([]);
      return;
    }

    const videoIds = allVideoItems.map(item => item.id.videoId).filter(Boolean);
    await fetchAndRenderFullVideos(apiKey, videoIds);
  }

  async function fetchKeywordSearch(apiKey, keyword) {
    setStatus("Searching for exploding content...", "active");
    const horizonKey = document.getElementById('timeHorizonSelect').value;
    const publishedAfter = getPublishedAfterISO(horizonKey);
    const maxResults = parseInt(localStorage.getItem("yt_max_results") || "20", 10);

    let searchUrl = `${API_BASE}/search?part=snippet&q=${encodeURIComponent(keyword)}&type=video&order=viewCount&maxResults=${maxResults}&key=${apiKey}`;
    if (publishedAfter) {
      searchUrl += `&publishedAfter=${publishedAfter}`;
    }

    const searchRes = await fetch(searchUrl);
    const searchData = await searchRes.json();
    if (searchData.error) throw new Error(searchData.error.message);

    const videoIds = (searchData.items || []).map(item => item.id.videoId).filter(Boolean);
    if (videoIds.length === 0) {
      setStatus("No results for that keyword/time period. Try widening the time horizon.", "error");
      window.lastFetchedResults = [];
      renderTable([]);
      return;
    }

    await fetchAndRenderFullVideos(apiKey, videoIds);
  }

  async function fetchTrending(apiKey) {
    setStatus("Fetching trending videos...", "active");
    const url = `${API_BASE}/videos?part=snippet,statistics&chart=mostPopular&maxResults=25&key=${apiKey}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    await processVideoDetailsAndRender(apiKey, data.items || []);
  }

  async function fetchAndRenderFullVideos(apiKey, videoIds) {
    // Chunk video details calls in batches of 50
    const idChunks = chunkArray(videoIds, 50);
    let fullVideoItems = [];

    for (const chunk of idChunks) {
      const videosUrl = `${API_BASE}/videos?part=snippet,statistics&id=${chunk.join(',')}&key=${apiKey}`;
      const videosRes = await fetch(videosUrl);
      const videosData = await videosRes.json();
      if (videosData.error) throw new Error(videosData.error.message);
      if (videosData.items) fullVideoItems.push(...videosData.items);
    }

    await processVideoDetailsAndRender(apiKey, fullVideoItems);
  }

  async function processVideoDetailsAndRender(apiKey, videoItems) {
    if (videoItems.length === 0) {
      setStatus("No results found.", "error");
      window.lastFetchedResults = [];
      renderTable([]);
      return;
    }

    const channelIds = [...new Set(videoItems.map(v => v.snippet.channelId))];
    const channelChunks = chunkArray(channelIds, 50);
    const channelsById = {};

    for (const cChunk of channelChunks) {
      const channelsUrl = `${API_BASE}/channels?part=snippet,statistics&id=${cChunk.join(',')}&key=${apiKey}`;
      const channelsRes = await fetch(channelsUrl);
      const channelsData = await channelsRes.json();
      (channelsData.items || []).forEach(c => { channelsById[c.id] = c; });
    }

    const results = videoItems.map(item => {
      const cId = item.snippet.channelId;
      const cInfo = channelsById[cId];
      const pubDate = item.snippet.publishedAt ? new Date(item.snippet.publishedAt) : new Date();
      const channelCreated = cInfo ? new Date(cInfo.snippet.publishedAt) : new Date();
      const ageDays = Math.floor((Date.now() - channelCreated.getTime()) / (1000 * 60 * 60 * 24));
      const videoId = typeof item.id === 'string' ? item.id : item.id.videoId;

      return {
        title: item.snippet.title,
        channel: item.snippet.channelTitle,
        pubDateISO: pubDate.toISOString(),
        pubDateFormatted: pubDate.toLocaleDateString(),
        views: item.statistics ? parseInt(item.statistics.viewCount || 0, 10) : 0,
        subs: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.subscriberCount || 0, 10) : 0,
        videos: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.videoCount || 0, 10) : 0,
        ageDays: ageDays,
        videoLink: `https://www.youtube.com/watch?v=${videoId}`,
        channelLink: `https://www.youtube.com/channel/${cId}`
      };
    });

    window.lastFetchedResults = results;
    window.sortState = { col: null, dir: 0 };
    renderTable(results);
    setStatus(`Successfully analyzed ${results.length} videos across channels.`, "success");
  }

  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // --- SORTING LOGIC FOR ALL COLUMNS ---
  function handleSort(col) {
    if (window.sortState.col === col) {
      window.sortState.dir = (window.sortState.dir + 1) % 3;
    } else {
      window.sortState.col = col;
      window.sortState.dir = 1; // 1 = High-to-Low / Newest-First
    }

    let toRender = [...window.lastFetchedResults];

    if (window.sortState.dir !== 0) {
      toRender.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];

        if (col === 'pubDateISO') {
          valA = new Date(valA).getTime();
          valB = new Date(valB).getTime();
        }

        if (window.sortState.dir === 1) return valB - valA; // Descending
        return valA - valB; // Ascending
      });
    }
    
    renderTable(toRender);
  }

  function getSortIndicator(col) {
    if (window.sortState && window.sortState.col === col) {
      if (window.sortState.dir === 1) return ' ↓';
      if (window.sortState.dir === 2) return ' ↑';
    }
    return '';
  }

  function renderTable(results) {
    const container = document.getElementById('resultsTableContainer');
    const header = document.getElementById('listHeader');
    const count = document.getElementById('listCount');

    if (results.length === 0) {
      container.innerHTML = '';
      header.style.display = 'none';
      return;
    }

    header.style.display = 'flex';
    count.textContent = `${results.length} Videos Analyzed`;

    let html = `
      <div class="table-container">
        <table class="glass-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Channel</th>
              <th class="sortable" onclick="handleSort('pubDateISO')" title="Sort by Date">Published${getSortIndicator('pubDateISO')}</th>
              <th class="sortable" onclick="handleSort('views')" title="Sort by Views">Views${getSortIndicator('views')}</th>
              <th class="sortable" onclick="handleSort('subs')" title="Sort by Subscribers">Subs${getSortIndicator('subs')}</th>
              <th class="sortable" onclick="handleSort('videos')" title="Sort by Videos">Videos${getSortIndicator('videos')}</th>
              <th class="sortable" onclick="handleSort('ageDays')" title="Sort by Age">Channel Age${getSortIndicator('ageDays')}</th>
              <th>Video Link</th>
            </tr>
          </thead>
          <tbody>
    `;

    results.forEach(r => {
      let agePercent = Math.min((r.ageDays / 730) * 100, 100);
      
      html += `
        <tr>
          <td class="trunc" title="${escapeHtml(r.title)}">${escapeHtml(r.title)}</td>
          <td class="trunc" title="${escapeHtml(r.channel)}"><a href="${r.channelLink}" target="_blank" style="color:inherit;">${escapeHtml(r.channel)}</a></td>
          <td>${r.pubDateFormatted}</td>
          <td>${r.views.toLocaleString()} 👁️</td>
          <td>${r.subs.toLocaleString()} 👥</td>
          <td>${r.videos.toLocaleString()}</td>
          <td>
            <div class="progress-bar-bg" title="${r.ageDays} days">
              <div class="progress-bar-fill" style="width: ${agePercent}%"></div>
            </div>
            <span class="progress-val">${r.ageDays}d</span>
          </td>
          <td><a class="table-btn" href="${r.videoLink}" target="_blank">▶️ Watch</a></td>
        </tr>
      `;
    });

    html += `
          </tbody>
        </table>
      </div>
    `;

    container.innerHTML = html;
  }

  // --- CLOUD SYNC & WORKSPACE IMPORT / EXPORT ---
  async function cloudLogin() {
    const key = document.getElementById("cloudUserKey").value.trim();
    if (!key) {
      document.getElementById("cloudStatus").textContent = "Enter a User Code/Key to sync.";
      return;
    }

    localStorage.setItem("yt_cloud_key", key);
    document.getElementById("cloudStatus").textContent = "Syncing with cloud...";

    try {
      const res = await fetch("/api/workspace/load", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_key: key })
      });
      const data = await res.json();
      if (data.status === "ok" && data.workspace) {
        if (data.workspace.api_key) {
          localStorage.setItem("yt_api_key", data.workspace.api_key);
          document.getElementById("ytApiKey").value = data.workspace.api_key;
        }
        if (data.workspace.input) {
          document.getElementById("mainInput").value = data.workspace.input;
        }
        document.getElementById("cloudStatus").textContent = "Cloud Workspace Loaded Successfully!";
      } else {
        // Save current as initial cloud state
        await cloudSave();
      }
    } catch (e) {
      document.getElementById("cloudStatus").textContent = "Cloud connection failed: " + e.message;
    }
  }

  async function cloudSave() {
    const key = localStorage.getItem("yt_cloud_key");
    if (!key) return;

    const payload = {
      user_key: key,
      workspace: {
        api_key: getApiKey(),
        input: document.getElementById("mainInput").value,
        mode: mode
      }
    };

    await fetch("/api/workspace/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    document.getElementById("cloudStatus").textContent = "Workspace synced to cloud!";
  }

  function exportWorkspace() {
    const data = {
      api_key: getApiKey(),
      input_queries: document.getElementById("mainInput").value,
      mode: mode,
      time_horizon: document.getElementById("timeHorizonSelect").value,
      results_count: window.lastFetchedResults.length
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "workspace_backup.json";
    a.click();
    URL.revokeObjectURL(url);
  }

  function importWorkspace() {
    document.getElementById("importFileInput").click();
  }

  function handleFileImport(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function(e) {
      try {
        const imported = JSON.parse(e.target.result);
        if (imported.api_key) {
          document.getElementById("ytApiKey").value = imported.api_key;
          localStorage.setItem("yt_api_key", imported.api_key);
        }
        if (imported.input_queries) {
          document.getElementById("mainInput").value = imported.input_queries;
        }
        setStatus("Workspace imported successfully!", "success");
      } catch (err) {
        setStatus("Invalid workspace JSON file.", "error");
      }
    };
    reader.readAsText(file);
  }
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_UI)

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# --- CLOUD WORKSPACE ENDPOINTS ---
@app.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    user_key = data.get("user_key")
    if not user_key:
        return jsonify({"status": "error", "message": "Missing user_key"}), 400
    return jsonify({"status": "ok", "user_key": user_key, "token": f"session_{user_key}"})

@app.route("/api/workspace/save", methods=["POST"])
def workspace_save():
    data = request.json or {}
    user_key = data.get("user_key")
    workspace = data.get("workspace")
    if not user_key or not workspace:
        return jsonify({"status": "error", "message": "Invalid parameters"}), 400

    CLOUD_WORKSPACES[user_key] = workspace
    return jsonify({"status": "ok", "message": "Workspace saved"})

@app.route("/api/workspace/load", methods=["POST"])
def workspace_load():
    data = request.json or {}
    user_key = data.get("user_key")
    if not user_key:
        return jsonify({"status": "error", "message": "Missing user_key"}), 400

    workspace = CLOUD_WORKSPACES.get(user_key)
    return jsonify({"status": "ok", "workspace": workspace})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
