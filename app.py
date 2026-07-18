from flask import Flask, render_template_string

app = Flask(__name__)

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Niche Finder</title>
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

  .box { width: 100%; max-width: 650px; }

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

  .quick-row { display: flex; align-items: center; gap: 10px; width: 100%; max-width: 650px; }

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
    width: 100%; background: rgba(0,0,0,0.28); border: 1px solid var(--glass-border-soft);
    color: var(--ink); padding: 16px; font-family: inherit; font-size: 14px; line-height: 1.5;
    border-radius: var(--radius-md); outline: none; margin-bottom: 16px;
    transition: all 0.2s; box-shadow: inset 0 2px 6px rgba(0,0,0,0.25);
  }
  .main-input:focus { border-color: rgba(255,255,255,0.24); background: rgba(0,0,0,0.42); box-shadow: 0 0 0 4px rgba(10,132,255,0.12); }
  .main-input::placeholder { color: var(--ink-faint); }

  button { border: none; cursor: pointer; font-family: inherit; transition: all 0.15s; }

  button.solid {
    background: #fff; color: #000; padding: 15px 24px; font-size: 14px; font-weight: 600;
    border-radius: 16px; width: 100%;
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

  .user-list { display: flex; flex-direction: column; gap: 8px; max-height: 500px; overflow-y: auto; padding-right: 4px; }

  .result-card {
    background: rgba(255,255,255,0.045); border: 1px solid var(--glass-border-soft); border-radius: var(--radius-sm);
    padding: 14px 15px; display: flex; flex-direction: column; gap: 8px;
    font-size: 13px; transition: background 0.2s;
  }
  .result-card:hover { background: rgba(255,255,255,0.085); }

  .result-top { display: flex; align-items: flex-start; gap: 10px; }
  .plat-badge { font-size: 10px; font-weight: 700; padding: 4px 8px; border-radius: 7px; text-transform: uppercase; letter-spacing: 0.05em; text-align: center; flex-shrink: 0; margin-top: 1px; }
  .bg-yt { background: rgba(255, 0, 0, 0.15); color: #ff453a; }
  .bg-new { background: rgba(50, 215, 75, 0.15); color: #32d74b; }

  .result-title { color: var(--ink); font-weight: 600; font-size: 13px; line-height: 1.4; flex: 1; }
  .result-channel { color: var(--ink-dim); font-size: 12px; margin-top: 2px; }

  .result-meta { display: flex; flex-wrap: wrap; gap: 6px 14px; font-size: 11px; color: var(--ink-dim); padding-left: 2px; }
  .result-meta b { color: var(--ink); font-weight: 600; }

  .result-actions { display: flex; gap: 8px; }
  .result-actions a {
    font-size: 11px; font-weight: 600; padding: 7px 13px; border-radius: 8px;
    background: rgba(255,255,255,0.08); color: #fff; text-decoration: none; transition: background 0.2s;
  }
  .result-actions a:hover { background: rgba(255,255,255,0.16); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }

  @media (prefers-reduced-motion: reduce) {
    body::before, body::after { animation: none; }
  }

  @media (max-width: 480px) {
    body { padding: 40px 14px 32px; }
    .brand-mark { font-size: 26px; }
    .glass-panel { padding: 18px; }
  }
</style>
</head>
<body>

<div class="brand">
  <span class="brand-mark">Niche Finder</span>
  <span class="brand-sub">YouTube Explosion Engine</span>
</div>

<div class="quick-row">
  <div class="pill-glass glass mode-active" id="modeTrendingBtn" onclick="setMode('trending')">⚡ Trending Now</div>
  <div class="pill-glass glass" id="modeKeywordBtn" onclick="setMode('keyword')">🔍 Keyword Explosion</div>
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

    <button class="solid" id="actionBtn" onclick="runSearch()">Refresh Trending</button>

    <div class="status" id="mainStatus">Ready to search.</div>

    <div class="list-header" id="listHeader">
      <span id="listCount">0 Videos Found</span>
    </div>
    <div class="user-list" id="resultsList"></div>
  </div>
</div>

<script>
  const API_BASE = 'https://www.googleapis.com/youtube/v3';
  let mode = 'trending'; // 'trending' | 'keyword'

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
      renderList([]);
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
      renderList([]);
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
        ageDays: ageDays,
        videoLink: `https://www.youtube.com/watch?v=${videoId}`,
        channelLink: `https://www.youtube.com/channel/${cId}`
      };
    });

    renderList(results);
    setStatus(`${results.length} videos found.`, "success");
  }

  function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
  }

  function renderList(results) {
    const listDiv = document.getElementById('resultsList');
    const header = document.getElementById('listHeader');
    const count = document.getElementById('listCount');

    listDiv.innerHTML = '';

    if (results.length === 0) {
      header.style.display = 'none';
      return;
    }

    header.style.display = 'flex';
    count.textContent = `${results.length} Videos Found`;

    results.forEach(r => {
      const card = document.createElement('div');
      card.className = 'result-card';

      const isNewChannel = r.ageDays <= 30;

      card.innerHTML = `
        <div class="result-top">
          <div class="plat-badge ${isNewChannel ? 'bg-new' : 'bg-yt'}">${isNewChannel ? 'New Ch' : 'YT'}</div>
          <div>
            <div class="result-title">${escapeHtml(r.title)}</div>
            <div class="result-channel">${escapeHtml(r.channel)}</div>
          </div>
        </div>
        <div class="result-meta">
          <span>👁️ <b>${formatNumber(r.views)}</b> views</span>
          <span>👥 <b>${formatNumber(r.subs)}</b> subs</span>
          <span>📅 Channel age <b>${r.ageDays}d</b></span>
        </div>
        <div class="result-actions">
          <a href="${r.videoLink}" target="_blank" rel="noopener">▶️ Watch</a>
          <a href="${r.channelLink}" target="_blank" rel="noopener">👤 Channel</a>
        </div>
    
