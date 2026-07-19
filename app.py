from flask import Flask

app = Flask(__name__)

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research Tool</title>
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
    padding: 56px 20px 40px;
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

  .brand { text-align: center; margin-bottom: 28px; }
  .brand-mark { display: block; font-size: 30px; font-weight: 700; letter-spacing: -0.02em; color: #fff; }
  .brand-sub { display: block; margin-top: 5px; font-size: 12px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-faint); }

  .box { width: 100%; max-width: 900px; }

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

  .quick-row { display: flex; align-items: center; gap: 10px; width: 100%; max-width: 650px; margin: 0 auto;}

  .pill-glass {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    border-radius: 999px;
    padding: 13px 20px;
    font-size: 13px;
    font-weight: 600;
    color: var(--ink-dim);
    cursor: pointer;
    transition: color 0.2s, background 0.2s;
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

  .settings-panel {
    display: none;
    background: rgba(0,0,0,0.32);
    border-radius: var(--radius-md);
    padding: 16px;
    margin-bottom: 20px;
    border: 1px solid var(--glass-border-soft);
    max-width: 650px;
    margin-left: auto; margin-right: auto;
  }
  .settings-panel-head {
    font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase;
    color: var(--ink-dim); justify-content: space-between; display: flex; margin-bottom: 14px;
  }
  .settings-panel-head span:last-child { color: var(--accent-2); cursor: pointer; text-transform: none; letter-spacing: 0; font-size: 12px; }

  .cookie-group { margin-bottom: 12px; }
  .cookie-group:last-child { margin-bottom: 0; }
  .cookie-group label { display: block; font-size: 10px; font-weight: 600; color: var(--ink-dim); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.06em; }
  .settings-panel textarea {
    width: 100%; height: 50px; background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border-soft);
    color: #a1a1a6; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 11px;
    padding: 11px; resize: vertical; outline: none; border-radius: var(--radius-sm); transition: border 0.2s;
  }
  .settings-panel textarea:focus { border-color: rgba(255,255,255,0.3); }

  .settings-panel select {
    width: 100%; background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border-soft);
    color: var(--ink); font-family: inherit; font-size: 13px; font-weight: 500;
    padding: 12px 14px; outline: none; border-radius: var(--radius-sm); transition: border 0.2s;
    appearance: none; -webkit-appearance: none;
    background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='%23a1a1a6' stroke-width='2'><polyline points='6 9 12 15 18 9'></polyline></svg>");
    background-repeat: no-repeat;
    background-position: right 12px center;
  }
  .settings-panel select:focus { border-color: rgba(255,255,255,0.3); }

  .main-input {
    width: 100%; max-width: 650px; display: block; margin: 0 auto 16px auto;
    background: rgba(0,0,0,0.28); border: 1px solid var(--glass-border-soft);
    color: var(--ink); padding: 16px; font-family: inherit; font-size: 14px; line-height: 1.5;
    border-radius: var(--radius-md); outline: none;
    transition: all 0.2s; box-shadow: inset 0 2px 6px rgba(0,0,0,0.25);
  }
  .main-input:focus { border-color: rgba(255,255,255,0.24); background: rgba(0,0,0,0.42); box-shadow: 0 0 0 4px rgba(10,132,255,0.12); }
  .main-input::placeholder { color: var(--ink-faint); }

  button { border: none; cursor: pointer; font-family: inherit; transition: all 0.15s; }
  button.solid {
    background: #fff; color: #000; padding: 15px 24px; font-size: 14px; font-weight: 600;
    border-radius: 16px; width: 100%; max-width: 650px; display: block; margin: 0 auto;
  }
  button.solid:hover { opacity: 0.9; transform: scale(0.99); }
  button.solid:active { transform: scale(0.97); }
  button.solid:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }

  .status { font-size: 13px; font-weight: 500; color: var(--ink-dim); min-height: 20px; margin-top: 16px; text-align: center; }
  .status.active { color: var(--accent-2); }
  .status.error { color: #ff453a; }
  .status.success { color: #32d74b; }

  .list-header {
    font-size: 11px; font-weight: 600; color: var(--ink-dim); text-transform: uppercase; letter-spacing: 0.06em;
    margin-top: 32px; margin-bottom: 12px; display: none; justify-content: space-between;
  }

  .table-container {
    width: 100%;
    overflow-x: auto;
    max-height: 500px;
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
    background: rgba(30, 30, 35, 0.85);
    backdrop-filter: blur(12px);
    color: var(--ink-dim);
    font-weight: 600;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    z-index: 2;
  }
  
  /* --- SORTING STYLES --- */
  .sortable { cursor: pointer; user-select: none; transition: background 0.2s; }
  .sortable:hover { background: rgba(255,255,255,0.08); color: #fff; }
  
  .glass-table td {
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    color: var(--ink);
  }
  .glass-table tr:hover td {
    background: rgba(255,255,255,0.05);
  }
  
  .trunc { max-width: 180px; overflow: hidden; text-overflow: ellipsis; }

  .progress-bar-bg {
    width: 60px; height: 6px; background: rgba(255,255,255,0.15); 
    border-radius: 4px; display: inline-block; vertical-align: middle; margin-right: 8px; overflow: hidden;
  }
  .progress-bar-fill {
    height: 100%; background: var(--accent); border-radius: 4px;
  }
  .progress-val { font-size: 11px; color: var(--ink-dim); }

  .table-btn {
    font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 6px;
    background: rgba(255,255,255,0.1); color: #fff; text-decoration: none; transition: background 0.2s;
  }
  .table-btn:hover { background: rgba(255,255,255,0.2); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }

  @media (max-width: 480px) {
    body { padding: 40px 14px 32px; }
    .brand-mark { font-size: 26px; }
    .glass-panel { padding: 16px; }
  }
</style>
</head>
<body>

<div class="brand">
  <span class="brand-mark">Research Tool</span>
  <span class="brand-sub">YouTube Intelligence Engine</span>
</div>

<div class="quick-row">
  <div class="pill-glass glass mode-active" id="modeKeywordBtn" onclick="setMode('keyword')">🔍 Research Tool</div>
  <div class="pill-glass glass" id="modeTrendingBtn" onclick="setMode('trending')">⚡ Trending Now</div>
  
  <div class="icon-glass glass" id="settingsBtn" onclick="toggleSettings()" title="Settings" role="button" aria-label="Settings" aria-expanded="false">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
  </div>
</div>

<div class="box">
  <div class="glass-panel glass">
    <div class="settings-panel" id="settingsPanel">
      <div class="settings-panel-head">
        <span>API &amp; Search Settings</span>
        <span onclick="saveSettings()">Save Settings</span>
      </div>

      <div class="cookie-group">
        <label>YouTube API v3 Key</label>
        <textarea id="ytApiKey" placeholder="AIzaSy..."></textarea>
      </div>

      <div class="cookie-group">
        <label>Time Period</label>
        <select id="periodSelect">
          <option value="1">Last 24 Hours</option>
          <option value="7" selected>Last 7 Days</option>
          <option value="30">Last 30 Days</option>
        </select>
      </div>

      <div class="cookie-group">
        <label>Number of Results</label>
        <select id="maxResultsSelect">
          <option value="10">10</option>
          <option value="20" selected>20</option>
          <option value="30">30</option>
          <option value="40">40</option>
          <option value="50">50</option>
        </select>
      </div>
    </div>

    <input type="text" id="keywordInput" class="main-input" placeholder="e.g. minecraft speedrun, true crime, budget travel">

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
  let mode = 'keyword'; 
  
  // --- GLOBALS FOR SORTING ---
  window.lastFetchedResults = [];
  window.sortState = { col: null, dir: 0 }; // 0: default, 1: desc (high-to-low), 2: asc (low-to-high)

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("ytApiKey").value = localStorage.getItem("yt_api_key") || "";
    document.getElementById("periodSelect").value = localStorage.getItem("yt_period") || "7";
    document.getElementById("maxResultsSelect").value = localStorage.getItem("yt_max_results") || "20";
    updateModeUI();
  });

  function toggleSettings() {
    const panel = document.getElementById("settingsPanel");
    const btn = document.getElementById("settingsBtn");
    const isOpen = panel.style.display === "block";
    panel.style.display = isOpen ? "none" : "block";
    btn.classList.toggle("is-open", !isOpen);
    btn.setAttribute("aria-expanded", String(!isOpen));
  }

  function saveSettings() {
    localStorage.setItem("yt_api_key", document.getElementById("ytApiKey").value.trim());
    localStorage.setItem("yt_period", document.getElementById("periodSelect").value);
    localStorage.setItem("yt_max_results", document.getElementById("maxResultsSelect").value);
    setStatus("Settings saved.", "success");
    toggleSettings();
  }

  function getApiKey() {
    return localStorage.getItem("yt_api_key") || document.getElementById("ytApiKey").value.trim();
  }

  function setMode(newMode) {
    mode = newMode;
    updateModeUI();
  }

  function updateModeUI() {
    document.getElementById("modeTrendingBtn").classList.toggle("mode-active", mode === "trending");
    document.getElementById("modeKeywordBtn").classList.toggle("mode-active", mode === "keyword");

    const input = document.getElementById("keywordInput");
    const btn = document.getElementById("actionBtn");

    if (mode === "trending") {
      input.style.display = "none";
      btn.textContent = "Refresh Trending";
    } else {
      input.style.display = "block";
      btn.textContent = "Find Exploding Content";
    }
  }

  function setStatus(msg, type = '') {
    const el = document.getElementById('mainStatus');
    el.textContent = msg;
    el.className = 'status ' + type;
  }

  async function runSearch() {
    const apiKey = getApiKey();
    if (!apiKey) {
      setStatus("Add your YouTube API key in Settings first.", "error");
      return;
    }

    const btn = document.getElementById('actionBtn');
    btn.disabled = true;

    try {
      if (mode === 'trending') {
        await fetchTrending(apiKey);
      } else {
        const keyword = document.getElementById('keywordInput').value.trim();
        if (!keyword) {
          setStatus("Enter a keyword first.", "error");
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

  async function fetchTrending(apiKey) {
    setStatus("Fetching trending videos...", "active");
    const url = `${API_BASE}/videos?part=snippet,statistics&chart=mostPopular&maxResults=25&key=${apiKey}`;
    const res = await fetch(url);
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    await renderResults(apiKey, data.items || []);
  }

  async function fetchKeywordSearch(apiKey, keyword) {
    setStatus("Searching for exploding content...", "active");
    const days = parseInt(localStorage.getItem("yt_period") || "7", 10);
    const maxResults = parseInt(localStorage.getItem("yt_max_results") || "20", 10);
    const afterDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
    const searchUrl = `${API_BASE}/search?part=snippet&q=${encodeURIComponent(keyword)}&type=video&order=viewCount&publishedAfter=${afterDate}&maxResults=${maxResults}&key=${apiKey}`;
    const searchRes = await fetch(searchUrl);
    const searchData = await searchRes.json();
    if (searchData.error) throw new Error(searchData.error.message);

    const videoIds = (searchData.items || []).map(item => item.id.videoId).filter(Boolean);
    if (videoIds.length === 0) {
      setStatus("No results for that keyword/time period. Try widening the time period.", "error");
      window.lastFetchedResults = [];
      renderTable([]);
      return;
    }

    const videosUrl = `${API_BASE}/videos?part=snippet,statistics&id=${videoIds.join(',')}&key=${apiKey}`;
    const videosRes = await fetch(videosUrl);
    const videosData = await videosRes.json();
    if (videosData.error) throw new Error(videosData.error.message);
    await renderResults(apiKey, videosData.items || []);
  }

  async function renderResults(apiKey, videoItems) {
    if (videoItems.length === 0) {
      setStatus("No results found.", "error");
      window.lastFetchedResults = [];
      renderTable([]);
      return;
    }

    const channelIds = [...new Set(videoItems.map(v => v.snippet.channelId))];
    const channelsUrl = `${API_BASE}/channels?part=snippet,statistics&id=${channelIds.join(',')}&key=${apiKey}`;
    const channelsRes = await fetch(channelsUrl);
    const channelsData = await channelsRes.json();
    const channelsById = {};
    (channelsData.items || []).forEach(c => { channelsById[c.id] = c; });

    const results = videoItems.map(item => {
      const cId = item.snippet.channelId;
      const cInfo = channelsById[cId];
      const pubDate = cInfo ? new Date(cInfo.snippet.publishedAt) : new Date();
      const ageDays = Math.floor((Date.now() - pubDate.getTime()) / (1000 * 60 * 60 * 24));
      const videoId = typeof item.id === 'string' ? item.id : item.id.videoId;

      return {
        title: item.snippet.title,
        channel: item.snippet.channelTitle,
        views: item.statistics ? parseInt(item.statistics.viewCount || 0, 10) : 0,
        subs: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.subscriberCount || 0, 10) : 0,
        videos: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.videoCount || 0, 10) : 0,
        ageDays: ageDays,
        videoLink: `https://www.youtube.com/watch?v=${videoId}`,
        channelLink: `https://www.youtube.com/channel/${cId}`
      };
    });

    // Reset sort state and save original data fetch
    window.lastFetchedResults = results;
    window.sortState = { col: null, dir: 0 };
    renderTable(results);
    setStatus(`${results.length} videos found.`, "success");
  }

  function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
  }
  
  function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }

  // --- SORTING LOGIC ---
  function handleSort(col) {
    if (window.sortState.col === col) {
      window.sortState.dir = (window.sortState.dir + 1) % 3;
    } else {
      window.sortState.col = col;
      window.sortState.dir = 1; // 1 = high to low first
    }

    let toRender = [...window.lastFetchedResults];

    if (window.sortState.dir !== 0) {
      toRender.sort((a, b) => {
        let valA = a[col];
        let valB = b[col];
        if (window.sortState.dir === 1) return valB - valA; // High to Low
        return valA - valB; // Low to High
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
    count.textContent = `${results.length} Videos Found`;

    let html = `
      <div class="table-container">
        <table class="glass-table">
          <thead>
            <tr>
              <th>Title</th>
              <th>Channel</th>
              <th class="sortable" onclick="handleSort('views')" title="Sort by Views">Views${getSortIndicator('views')}</th>
              <th class="sortable" onclick="handleSort('subs')" title="Sort by Subscribers">Subs${getSortIndicator('subs')}</th>
              <th class="sortable" onclick="handleSort('videos')" title="Sort by Videos">Videos${getSortIndicator('videos')}</th>
              <th class="sortable" onclick="handleSort('ageDays')" title="Sort by Age">Channel Age${getSortIndicator('ageDays')}</th>
              <th>Video Link</th>
              <th>Channel Link</th>
            </tr>
          </thead>
          <tbody>
    `;

    results.forEach(r => {
      let agePercent = Math.min((r.ageDays / 730) * 100, 100);
      
      html += `
        <tr>
          <td class="trunc" title="${escapeHtml(r.title)}">${escapeHtml(r.title)}</td>
          <td class="trunc" title="${escapeHtml(r.channel)}">${escapeHtml(r.channel)}</td>
          <td>${r.views.toLocaleString()} 👁️</td>
          <td>${r.subs.toLocaleString()} 👥</td>
          <td>${r.videos.toLocaleString()}</td>
          <td>
            <div class="progress-bar-bg" title="${r.ageDays} days">
              <div class="progress-bar-fill" style="width: ${agePercent}%"></div>
            </div>
            <span class="progress-val">${r.ageDays} days</span>
          </td>
          <td><a class="table-btn" href="${r.videoLink}" target="_blank">▶️ Watch</a></td>
          <td><a class="table-btn" href="${r.channelLink}" target="_blank">👤 Open Channel</a></td>
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
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/health")
def health():
    return {"status": "ok"}, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
