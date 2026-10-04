from flask import Flask, request, Response
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone
import json
import os
import re

app = Flask(__name__)

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research Tool Pro</title>
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
    --accent-purple: #bf5af2;
    --radius-lg: 28px;
    --radius-md: 18px;
    --radius-sm: 12px;
  }

  body {
    background: #030304; color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    min-height: 100vh; display: flex; flex-direction: column; align-items: center;
    padding: 56px 20px 40px; position: relative; overflow-x: hidden;
  }

  body::before, body::after {
    content: ''; position: fixed; border-radius: 50%; filter: blur(130px); z-index: -1; opacity: 0.45;
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
    position: relative; background: var(--glass-fill); -webkit-backdrop-filter: blur(28px) saturate(160%); backdrop-filter: blur(28px) saturate(160%);
    border: 1px solid var(--glass-border); box-shadow: 0 1px 0 rgba(255,255,255,0.14) inset, 0 20px 50px rgba(0,0,0,0.45);
  }

  .glass-panel { border-radius: var(--radius-lg); padding: 24px; margin-top: 16px; }

  .quick-row { display: flex; align-items: center; gap: 10px; width: 100%; max-width: 750px; margin: 0 auto;}

  .pill-glass {
    flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; border-radius: 999px;
    padding: 13px 20px; font-size: 13px; font-weight: 600; color: var(--ink-dim); cursor: pointer; transition: all 0.2s;
  }
  .pill-glass:active { transform: scale(0.97); }
  .pill-glass.mode-active { color: #fff; background: var(--accent) !important; border-color: transparent; }
  .pill-glass.mode-active.auto { background: var(--accent-purple) !important; }

  .icon-glass {
    flex-shrink: 0; width: 44px; height: 44px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; color: var(--ink-dim); cursor: pointer; transition: color 0.2s, transform 0.15s;
  }
  .icon-glass:hover { color: #fff; }
  .icon-glass:active { transform: scale(0.92); }
  .icon-glass.is-open { color: var(--accent-2); }
  .icon-glass svg { width: 18px; height: 18px; }

  .settings-panel {
    display: none; background: rgba(0,0,0,0.32); border-radius: var(--radius-md); padding: 16px; margin-bottom: 20px;
    border: 1px solid var(--glass-border-soft); max-width: 650px; margin-left: auto; margin-right: auto;
  }
  .settings-panel-head { font-size: 11px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--ink-dim); justify-content: space-between; display: flex; margin-bottom: 14px; }
  .settings-panel-head span:last-child { color: var(--accent-2); cursor: pointer; text-transform: none; letter-spacing: 0; font-size: 12px; }

  .cookie-group { margin-bottom: 12px; }
  .cookie-group label { display: block; font-size: 10px; font-weight: 600; color: var(--ink-dim); margin-bottom: 6px; text-transform: uppercase; letter-spacing: 0.06em; }
  .settings-panel textarea, .settings-panel select { width: 100%; background: rgba(0,0,0,0.4); border: 1px solid var(--glass-border-soft); color: var(--ink); font-family: inherit; font-size: 13px; padding: 12px 14px; outline: none; border-radius: var(--radius-sm); transition: border 0.2s; }
  .settings-panel textarea { height: 50px; font-family: monospace; font-size: 11px; padding: 11px; resize: vertical; }
  
  .main-input {
    width: 100%; max-width: 650px; display: block; margin: 0 auto 16px auto; background: rgba(0,0,0,0.28);
    border: 1px solid var(--glass-border-soft); color: var(--ink); padding: 16px; font-family: inherit; font-size: 14px;
    border-radius: var(--radius-md); outline: none; transition: all 0.2s; box-shadow: inset 0 2px 6px rgba(0,0,0,0.25);
  }
  .main-input:focus { border-color: rgba(255,255,255,0.24); background: rgba(0,0,0,0.42); box-shadow: 0 0 0 4px rgba(10,132,255,0.12); }

  button.solid {
    background: #fff; color: #000; padding: 15px 24px; font-size: 14px; font-weight: 600;
    border-radius: 16px; width: 100%; max-width: 650px; display: block; margin: 0 auto; border: none; cursor: pointer; transition: all 0.15s;
  }
  button.solid:hover { opacity: 0.9; transform: scale(0.99); }
  button.solid:disabled { opacity: 0.35; cursor: not-allowed; transform: none; }

  .status { font-size: 13px; font-weight: 500; color: var(--ink-dim); min-height: 20px; margin-top: 16px; text-align: center; }
  .status.active { color: var(--accent-2); }
  .status.error { color: #ff453a; }
  .status.success { color: #32d74b; }

  .list-header { font-size: 11px; font-weight: 600; color: var(--ink-dim); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 32px; margin-bottom: 12px; display: none; justify-content: space-between; }
  
  .table-container { width: 100%; overflow-x: auto; max-height: 500px; overflow-y: auto; border-radius: var(--radius-sm); background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border-soft); margin-top: 16px;}
  .glass-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; white-space: nowrap; }
  .glass-table th { position: sticky; top: 0; background: rgba(30, 30, 35, 0.85); backdrop-filter: blur(12px); color: var(--ink-dim); font-weight: 600; padding: 12px 16px; z-index: 2; }
  .glass-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); color: var(--ink); }
  .glass-table tr:hover td { background: rgba(255,255,255,0.05); }
  
  .sortable { cursor: pointer; user-select: none; transition: background 0.2s; }
  .sortable:hover { background: rgba(255,255,255,0.08); color: #fff; }
  .trunc { max-width: 180px; overflow: hidden; text-overflow: ellipsis; }
  
  .table-btn { font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 6px; background: rgba(255,255,255,0.1); color: #fff; text-decoration: none; transition: background 0.2s; margin-right:4px;}
  .table-btn:hover { background: rgba(255,255,255,0.2); }
  .badge { padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; background: rgba(191, 90, 242, 0.2); color: #bf5af2;}
  
  .progress-bar-bg { width: 60px; height: 6px; background: rgba(255,255,255,0.15); border-radius: 4px; display: inline-block; vertical-align: middle; margin-right: 8px; overflow: hidden; }
  .progress-bar-fill { height: 100%; background: var(--accent); border-radius: 4px; }
  .progress-val { font-size: 11px; color: var(--ink-dim); }

  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.3); }
</style>
</head>
<body>

<div class="brand">
  <span class="brand-mark">Research Tool Pro</span>
  <span class="brand-sub">YouTube Intelligence Engine</span>
</div>

<div class="quick-row">
  <div class="pill-glass glass mode-active" id="modeKeywordBtn" onclick="setMode('keyword')">🔍 Legacy Search</div>
  <div class="pill-glass glass" id="modeTrendingBtn" onclick="setMode('trending')">⚡ Trending</div>
  <div class="pill-glass glass" id="modeAutoBtn" onclick="setMode('auto')">🤖 Auto Pipeline</div>
  
  <div class="icon-glass glass" id="settingsBtn" onclick="toggleSettings()" title="Settings">
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
        <label>Time Period (Legacy)</label>
        <select id="periodSelect">
          <option value="1">Last 24 Hours</option>
          <option value="7" selected>Last 7 Days</option>
          <option value="30">Last 30 Days</option>
        </select>
      </div>
      <div class="cookie-group">
        <label>Number of Results (Legacy)</label>
        <select id="maxResultsSelect">
          <option value="10">10</option><option value="20" selected>20</option><option value="50">50</option>
        </select>
      </div>
    </div>

    <!-- Legacy Inputs -->
    <div id="legacyInputs">
      <input type="text" id="keywordInput" class="main-input" placeholder="e.g. minecraft speedrun, true crime">
    </div>

    <!-- Auto Pipeline Inputs -->
    <div id="autoInputs" style="display:none;">
      <input type="text" id="seedInput" class="main-input" style="margin-bottom: 12px;" placeholder="1. Seed Keyword (e.g. funny animals)">
      <input type="text" id="nicheInput" class="main-input" style="margin-bottom: 12px;" placeholder="2. Niche Qualifications (comma separated, e.g. cat, dog)">
      <input type="number" id="thresholdInput" class="main-input" placeholder="3. Min matches in last 30 videos (e.g. 5)" value="5">
    </div>

    <button class="solid" id="actionBtn" onclick="runSearch()">Execute Search</button>
    <div class="status" id="mainStatus">Ready.</div>

    <div class="list-header" id="listHeader">
      <span id="listCount">0 Videos Found</span>
    </div>
    
    <!-- Render Container for Tables -->
    <div id="resultsTableContainer"></div>
  </div>
</div>

<script>
  const API_BASE = 'https://www.googleapis.com/youtube/v3';
  let mode = 'keyword'; 
  window.lastFetchedResults = [];
  window.sortState = { col: null, dir: 0 };

  document.addEventListener("DOMContentLoaded", () => {
    document.getElementById("ytApiKey").value = localStorage.getItem("yt_api_key") || "";
    document.getElementById("periodSelect").value = localStorage.getItem("yt_period") || "7";
    document.getElementById("maxResultsSelect").value = localStorage.getItem("yt_max_results") || "20";
    setMode('keyword');
  });

  function toggleSettings() {
    const panel = document.getElementById("settingsPanel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
  }

  function saveSettings() {
    localStorage.setItem("yt_api_key", document.getElementById("ytApiKey").value.trim());
    localStorage.setItem("yt_period", document.getElementById("periodSelect").value);
    localStorage.setItem("yt_max_results", document.getElementById("maxResultsSelect").value);
    setStatus("Settings saved.", "success");
    toggleSettings();
  }

  function getApiKey() { return localStorage.getItem("yt_api_key") || document.getElementById("ytApiKey").value.trim(); }

  function setMode(newMode) {
    mode = newMode;
    document.getElementById("modeKeywordBtn").classList.toggle("mode-active", mode === "keyword");
    document.getElementById("modeTrendingBtn").classList.toggle("mode-active", mode === "trending");
    
    const autoBtn = document.getElementById("modeAutoBtn");
    autoBtn.classList.toggle("mode-active", mode === "auto");
    autoBtn.classList.toggle("auto", mode === "auto");

    const legInput = document.getElementById("legacyInputs");
    const autoInput = document.getElementById("autoInputs");
    const btn = document.getElementById("actionBtn");

    if (mode === "keyword") {
      legInput.style.display = "block"; autoInput.style.display = "none"; btn.textContent = "Find Exploding Content";
    } else if (mode === "trending") {
      legInput.style.display = "none"; autoInput.style.display = "none"; btn.textContent = "Refresh Trending";
    } else {
      legInput.style.display = "none"; autoInput.style.display = "block"; btn.textContent = "Initialize Auto Pipeline";
    }
    
    document.getElementById('resultsTableContainer').innerHTML = '';
    document.getElementById('listHeader').style.display = 'none';
  }

  function setStatus(msg, type = '') {
    const el = document.getElementById('mainStatus'); el.textContent = msg; el.className = 'status ' + type;
  }

  async function runSearch() {
    const apiKey = getApiKey();
    if (!apiKey) { setStatus("Add your YouTube API key in Settings first.", "error"); return; }
    
    const btn = document.getElementById('actionBtn');
    btn.disabled = true;

    try {
      if (mode === 'trending') {
        await fetchTrending(apiKey);
      } else if (mode === 'keyword') {
        const keyword = document.getElementById('keywordInput').value.trim();
        if (!keyword) { setStatus("Enter a keyword first.", "error"); btn.disabled = false; return; }
        await fetchKeywordSearch(apiKey, keyword);
      } else if (mode === 'auto') {
        runAutoResearch(apiKey);
      }
    } catch (err) {
      setStatus(`Error: ${err.message}`, "error");
    }
    
    if (mode !== 'auto') btn.disabled = false;
  }

  /* --- LEGACY LOGIC --- */
  async function fetchTrending(apiKey) {
    setStatus("Fetching trending videos...", "active");
    const res = await fetch(`${API_BASE}/videos?part=snippet,statistics&chart=mostPopular&maxResults=25&key=${apiKey}`);
    const data = await res.json();
    if (data.error) throw new Error(data.error.message);
    await renderLegacyResults(apiKey, data.items || []);
  }

  async function fetchKeywordSearch(apiKey, keyword) {
    setStatus("Searching for exploding content...", "active");
    const days = parseInt(localStorage.getItem("yt_period") || "7", 10);
    const maxRes = parseInt(localStorage.getItem("yt_max_results") || "20", 10);
    const afterDate = new Date(Date.now() - days * 24 * 60 * 60 * 1000).toISOString();
    
    const searchRes = await fetch(`${API_BASE}/search?part=snippet&q=${encodeURIComponent(keyword)}&type=video&order=viewCount&publishedAfter=${afterDate}&maxResults=${maxRes}&key=${apiKey}`);
    const searchData = await searchRes.json();
    if (searchData.error) throw new Error(searchData.error.message);

    const videoIds = (searchData.items || []).map(i => i.id.videoId).filter(Boolean);
    if (videoIds.length === 0) { setStatus("No results.", "error"); return; }

    const videosRes = await fetch(`${API_BASE}/videos?part=snippet,statistics&id=${videoIds.join(',')}&key=${apiKey}`);
    const videosData = await videosRes.json();
    if (videosData.error) throw new Error(videosData.error.message);
    await renderLegacyResults(apiKey, videosData.items || []);
  }

  async function renderLegacyResults(apiKey, videoItems) {
    const channelIds = [...new Set(videoItems.map(v => v.snippet.channelId))];
    const channelsRes = await fetch(`${API_BASE}/channels?part=snippet,statistics&id=${channelIds.join(',')}&key=${apiKey}`);
    const channelsData = await channelsRes.json();
    const channelsById = {};
    (channelsData.items || []).forEach(c => { channelsById[c.id] = c; });

    const results = videoItems.map(item => {
      const cId = item.snippet.channelId;
      const cInfo = channelsById[cId];
      const ageDays = Math.floor((Date.now() - (cInfo ? new Date(cInfo.snippet.publishedAt) : new Date()).getTime()) / 86400000);
      return {
        title: item.snippet.title, channel: item.snippet.channelTitle,
        views: item.statistics ? parseInt(item.statistics.viewCount || 0, 10) : 0,
        subs: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.subscriberCount || 0, 10) : 0,
        videos: cInfo && cInfo.statistics ? parseInt(cInfo.statistics.videoCount || 0, 10) : 0,
        ageDays: ageDays, videoLink: `https://www.youtube.com/watch?v=${item.id.videoId || item.id}`, channelLink: `https://www.youtube.com/channel/${cId}`
      };
    });

    window.lastFetchedResults = results; window.sortState = { col: null, dir: 0 };
    renderLegacyTable(results);
    setStatus(`${results.length} videos found.`, "success");
  }

  function handleSort(col) {
    if (window.sortState.col === col) window.sortState.dir = (window.sortState.dir + 1) % 3;
    else { window.sortState.col = col; window.sortState.dir = 1; }

    let toRender = [...window.lastFetchedResults];
    if (window.sortState.dir !== 0) toRender.sort((a, b) => window.sortState.dir === 1 ? b[col] - a[col] : a[col] - b[col]);
    
    mode === 'auto' ? renderAutoTable(toRender) : renderLegacyTable(toRender);
  }

  function getSortIndicator(col) {
    if (window.sortState && window.sortState.col === col) return window.sortState.dir === 1 ? ' ↓' : (window.sortState.dir === 2 ? ' ↑' : '');
    return '';
  }
  function escapeHtml(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  function renderLegacyTable(results) {
    const container = document.getElementById('resultsTableContainer');
    document.getElementById('listHeader').style.display = 'flex';
    document.getElementById('listCount').textContent = `${results.length} Legacy Videos Found`;

    let html = `<div class="table-container"><table class="glass-table"><thead><tr>
      <th>Title</th><th>Channel</th>
      <th class="sortable" onclick="handleSort('views')">Views${getSortIndicator('views')}</th>
      <th class="sortable" onclick="handleSort('subs')">Subs${getSortIndicator('subs')}</th>
      <th class="sortable" onclick="handleSort('videos')">Videos${getSortIndicator('videos')}</th>
      <th class="sortable" onclick="handleSort('ageDays')">Channel Age${getSortIndicator('ageDays')}</th>
      <th>Links</th></tr></thead><tbody>`;

    results.forEach(r => {
      let ageP = Math.min((r.ageDays / 730) * 100, 100);
      html += `<tr><td class="trunc" title="${escapeHtml(r.title)}">${escapeHtml(r.title)}</td><td class="trunc">${escapeHtml(r.channel)}</td>
      <td>${r.views.toLocaleString()} 👁️</td><td>${r.subs.toLocaleString()} 👥</td><td>${r.videos.toLocaleString()}</td>
      <td><div class="progress-bar-bg"><div class="progress-bar-fill" style="width:${ageP}%"></div></div><span class="progress-val">${r.ageDays}d</span></td>
      <td><a class="table-btn" href="${r.videoLink}" target="_blank">▶️</a><a class="table-btn" href="${r.channelLink}" target="_blank">👤</a></td></tr>`;
    });
    container.innerHTML = html + `</tbody></table></div>`;
  }

  /* --- NEW AUTO PIPELINE LOGIC --- */
  function runAutoResearch(apiKey) {
    const seed = document.getElementById('seedInput').value.trim();
    const niche = document.getElementById('nicheInput').value.trim();
    const threshold = document.getElementById('thresholdInput').value;
    if (!seed || !niche) { setStatus("Seed and Niche keywords required.", "error"); document.getElementById('actionBtn').disabled = false; return; }

    const url = `/api/auto-research?api_key=${apiKey}&seed=${encodeURIComponent(seed)}&niche=${encodeURIComponent(niche)}&threshold=${threshold}`;
    const eventSource = new EventSource(url);

    eventSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      if (data.status === 'progress') setStatus(data.msg, "active");
      else if (data.status === 'done') {
        setStatus(data.msg, "success");
        window.lastFetchedResults = data.results; window.sortState = { col: null, dir: 0 };
        renderAutoTable(data.results);
        eventSource.close(); document.getElementById('actionBtn').disabled = false;
      } 
      else if (data.status === 'error') {
        setStatus("Error: " + data.msg, "error"); eventSource.close(); document.getElementById('actionBtn').disabled = false;
      }
    };
    eventSource.onerror = function(err) {
      setStatus("Connection stream lost.", "error"); eventSource.close(); document.getElementById('actionBtn').disabled = false;
    };
  }

  function renderAutoTable(results) {
    const container = document.getElementById('resultsTableContainer');
    document.getElementById('listHeader').style.display = 'flex';
    document.getElementById('listCount').textContent = `${results.length} Target Shorts Generated`;

    let html = `<div class="table-container"><table class="glass-table"><thead><tr>
      <th>Short Title</th><th>Verified Channel</th>
      <th class="sortable" onclick="handleSort('views')">Total Views${getSortIndicator('views')}</th>
      <th class="sortable" onclick="handleSort('vph')">Velocity (VPH)${getSortIndicator('vph')}</th>
      <th class="sortable" onclick="handleSort('age_hours')">Age (Hours)${getSortIndicator('age_hours')}</th>
      <th>Links</th></tr></thead><tbody>`;

    results.forEach(r => {
      html += `<tr><td class="trunc" title="${escapeHtml(r.title)}">${escapeHtml(r.title)}</td><td class="trunc">${escapeHtml(r.channel)}</td>
      <td>${r.views.toLocaleString()} 👁️</td><td><span class="badge">🔥 ${r.vph.toLocaleString()}/hr</span></td><td>${r.age_hours} hrs</td>
      <td><a class="table-btn" href="${r.videoLink}" target="_blank">▶️ Watch</a><a class="table-btn" href="${r.channelLink}" target="_blank">👤 Ch</a></td></tr>`;
    });
    container.innerHTML = html + `</tbody></table></div>`;
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

@app.route('/api/auto-research', methods=['GET'])
def auto_research_stream():
    api_key = request.args.get('api_key')
    seed = request.args.get('seed')
    niche_str = request.args.get('niche')
    threshold = int(request.args.get('threshold', 5))

    def generate():
        def emit(status, msg="", data=None):
            payload = {"status": status, "msg": msg}
            if data is not None: payload["results"] = data
            return f"data: {json.dumps(payload)}\n\n"

        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            niche_keywords = [k.strip().lower() for k in niche_str.split(',') if k.strip()]

            db_path = 'verified_channels.json'
            verified = {}
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    verified = json.load(f)

            yield emit('progress', f'Searching seed keyword: "{seed}" to find active channels...')
            
            search_res = youtube.search().list(q=seed, part="snippet", type="video", order="date", maxResults=20).execute()
            found_channels = list(set([item['snippet']['channelId'] for item in search_res.get('items', [])]))
            new_channels = [cid for cid in found_channels if cid not in verified]
            
            yield emit('progress', f'Found {len(found_channels)} channels. {len(new_channels)} are new. Qualifying them...')

            if new_channels:
                c_res = youtube.channels().list(part="contentDetails,snippet", id=",".join(new_channels)).execute()
                for c_item in c_res.get('items', []):
                    c_id = c_item['id']
                    c_title = c_item['snippet']['title']
                    try:
                        uploads_id = c_item['contentDetails']['relatedPlaylists']['uploads']
                    except KeyError:
                        continue 

                    pl_res = youtube.playlistItems().list(part="snippet", playlistId=uploads_id, maxResults=30).execute()
                    
                    match_count = 0
                    for pl_item in pl_res.get('items', []):
                        title = pl_item['snippet']['title'].lower()
                        if any(k in title for k in niche_keywords): match_count += 1

                    if match_count >= threshold:
                        verified[c_id] = {"title": c_title, "uploads_id": uploads_id}
                        yield emit('progress', f'✅ Qualified: {c_title} ({match_count} matches)')
                    else:
                        yield emit('progress', f'❌ Discarded: {c_title} ({match_count} matches)')

                with open(db_path, 'w') as f:
                    json.dump(verified, f, indent=4)

            yield emit('progress', f'Scraping latest Shorts from all {len(verified)} verified channels in database...')
            all_shorts = []

            for c_id, c_data in verified.items():
                uploads_id = c_data.get('uploads_id')
                if not uploads_id: continue

                pl_res = youtube.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=20).execute()
                v_ids = [item['contentDetails']['videoId'] for item in pl_res.get('items', [])]

                if not v_ids: continue

                v_res = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(v_ids)).execute()

                for v_item in v_res.get('items', []):
                    duration_str = v_item['contentDetails']['duration']
                    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
                    if not match: continue
                    h, m, s = int(match.group(1) or 0), int(match.group(2) or 0), int(match.group(3) or 0)
                    total_seconds = h * 3600 + m * 60 + s

                    if total_seconds <= 60:
                        pub_date = parser.isoparse(v_item['snippet']['publishedAt'])
                        age_hours = (datetime.now(timezone.utc) - pub_date).total_seconds() / 3600
                        views = int(v_item['statistics'].get('viewCount', 0))
                        
                        vph = views / max(age_hours, 1)

                        all_shorts.append({
                            "title": v_item['snippet']['title'],
                            "channel": c_data['title'],
                            "views": views, "vph": round(vph, 1), "age_hours": round(age_hours, 1),
                            "videoLink": f"https://www.youtube.com/watch?v={v_item['id']}",
                            "channelLink": f"https://www.youtube.com/channel/{c_id}"
                        })

            yield emit('progress', 'Sorting matrix by View Velocity...')
            all_shorts.sort(key=lambda x: x['vph'], reverse=True)
            yield emit('done', 'Research Complete!', all_shorts[:100])

        except Exception as e:
            yield emit('error', str(e))

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
