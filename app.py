from flask import Flask, request, Response, jsonify
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone
import json
import re
import os

app = Flask(__name__)

# Backend in-memory store (continuously synced by the frontend to survive Render wipes)
BASE_CHANNELS = {}

HTML_UI = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Research Tool Pro | Base Command</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
  :root {
    --glass-fill: rgba(255, 255, 255, 0.07);
    --glass-border: rgba(255, 255, 255, 0.14);
    --glass-border-soft: rgba(255, 255, 255, 0.07);
    --ink: #f5f5f7;
    --ink-dim: rgba(245, 245, 247, 0.55);
    --accent: #0a84ff;
    --accent-purple: #bf5af2;
    --radius-lg: 28px;
    --radius-md: 18px;
    --radius-sm: 12px;
  }

  body {
    background: #030304; color: var(--ink);
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, sans-serif;
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

  /* Login Overlay */
  #loginOverlay {
    position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(20px);
    z-index: 9999; display: flex; flex-direction: column; align-items: center; justify-content: center;
  }
  .login-box {
    background: var(--glass-fill); border: 1px solid var(--glass-border); padding: 40px;
    border-radius: var(--radius-lg); text-align: center; width: 100%; max-width: 400px;
  }
  .login-box h2 { margin-bottom: 10px; font-size: 22px; }
  .login-box p { color: var(--ink-dim); font-size: 13px; margin-bottom: 24px; }
  .login-input {
    width: 100%; padding: 14px; border-radius: var(--radius-sm); border: 1px solid var(--glass-border-soft);
    background: rgba(0,0,0,0.5); color: #fff; font-size: 16px; text-align: center; margin-bottom: 16px; outline: none; letter-spacing: 4px;
  }
  .login-input:focus { border-color: var(--accent); }

  .brand { text-align: center; margin-bottom: 28px; }
  .brand-mark { display: block; font-size: 30px; font-weight: 700; color: #fff; }
  .brand-sub { display: block; margin-top: 5px; font-size: 12px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-dim); }

  .box { width: 100%; max-width: 900px; }
  .glass-panel {
    background: var(--glass-fill); -webkit-backdrop-filter: blur(28px); backdrop-filter: blur(28px);
    border: 1px solid var(--glass-border); border-radius: var(--radius-lg); padding: 24px; box-shadow: 0 20px 50px rgba(0,0,0,0.45);
  }

  .header-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
  .header-row h3 { font-size: 16px; font-weight: 600; }
  .btn-icon { background: rgba(255,255,255,0.1); border: none; color: #fff; padding: 8px 16px; border-radius: 99px; cursor: pointer; font-size: 12px; font-weight: 600; transition: 0.2s; }
  .btn-icon:hover { background: rgba(255,255,255,0.2); }

  /* Tag Inputs */
  .tag-container {
    background: rgba(0,0,0,0.3); border: 1px solid var(--glass-border-soft); border-radius: var(--radius-md);
    padding: 10px 14px; min-height: 56px; display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-bottom: 16px;
  }
  .tag-container input {
    background: transparent; border: none; color: var(--ink); font-size: 14px; outline: none; flex: 1; min-width: 150px;
  }
  .tag {
    background: rgba(255,255,255,0.15); color: #fff; font-size: 12px; font-weight: 600; padding: 6px 12px;
    border-radius: 8px; display: flex; align-items: center; gap: 6px;
  }
  .tag span { cursor: pointer; color: rgba(255,255,255,0.5); }
  .tag span:hover { color: #ff453a; }

  /* Split Buttons */
  .action-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
  button.solid {
    padding: 16px; font-size: 14px; font-weight: 600; border-radius: 16px; border: none; cursor: pointer; transition: all 0.15s; font-family: inherit;
  }
  button.solid:hover { transform: scale(0.98); opacity: 0.9; }
  button.solid:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
  .btn-discover { background: var(--accent-purple); color: #fff; }
  .btn-analyze { background: var(--accent); color: #fff; }

  /* Channel Manager & Settings */
  .settings-panel { display: none; background: rgba(0,0,0,0.4); border-radius: var(--radius-md); padding: 20px; margin-bottom: 24px; border: 1px solid var(--glass-border-soft); }
  .channel-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; max-height: 300px; overflow-y: auto; margin-top: 16px; padding-right: 8px; }
  .channel-card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 12px; padding: 12px; display: flex; align-items: center; gap: 12px; }
  .channel-card img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; }
  .channel-card .c-info { flex: 1; overflow: hidden; }
  .channel-card .c-name { font-size: 12px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .channel-card .c-del { color: #ff453a; cursor: pointer; font-size: 16px; }

  .status { font-size: 13px; font-weight: 500; color: var(--ink-dim); min-height: 20px; margin-top: 20px; text-align: center; }
  .status.active { color: var(--accent-2); }
  
  /* Output Table */
  .table-container { width: 100%; overflow-x: auto; max-height: 600px; overflow-y: auto; border-radius: var(--radius-sm); background: rgba(255,255,255,0.03); border: 1px solid var(--glass-border-soft); margin-top: 24px; display: none; }
  .glass-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: left; white-space: nowrap; }
  .glass-table th { position: sticky; top: 0; background: rgba(30, 30, 35, 0.9); backdrop-filter: blur(12px); color: var(--ink-dim); font-weight: 600; padding: 12px 16px; z-index: 2; }
  .glass-table td { padding: 12px 16px; border-bottom: 1px solid rgba(255,255,255,0.05); vertical-align: middle; }
  .glass-table tr:hover td { background: rgba(255,255,255,0.05); }
  
  .thumb-img { width: 64px; height: 36px; border-radius: 6px; object-fit: cover; border: 1px solid rgba(255,255,255,0.1); }
  .logo-img { width: 24px; height: 24px; border-radius: 50%; vertical-align: middle; margin-right: 8px; }
  
  .badge { padding: 4px 8px; border-radius: 6px; font-weight: bold; font-size: 11px; background: rgba(191, 90, 242, 0.2); color: #bf5af2;}
  .table-btn { font-size: 11px; font-weight: 600; padding: 6px 12px; border-radius: 6px; background: rgba(255,255,255,0.1); color: #fff; text-decoration: none; transition: 0.2s; margin-right: 4px; }
  .table-btn:hover { background: rgba(255,255,255,0.2); }
  .trunc { max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
  
  ::-webkit-scrollbar { width: 6px; height: 6px; }
  ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 10px; }
</style>
</head>
<body>

<!-- Authentication Overlay -->
<div id="loginOverlay">
  <div class="login-box">
    <h2 id="loginTitle">System Locked</h2>
    <p id="loginSub">Enter your Profile PIN to access the base.</p>
    <input type="password" id="pinInput" class="login-input" placeholder="••••" onkeypress="if(event.key === 'Enter') checkLogin()">
    <button class="solid btn-analyze" style="width:100%;" onclick="checkLogin()">Unlock</button>
  </div>
</div>

<div class="brand">
  <span class="brand-mark">Base Command</span>
  <span class="brand-sub">Permanent Channel Pipeline</span>
</div>

<div class="box">
  <div class="glass-panel">
    
    <div class="header-row">
      <h3>Pipeline Configuration</h3>
      <button class="btn-icon" onclick="toggleSettings()">⚙️ Base Manager & API</button>
    </div>

    <!-- Settings & Base Manager Panel -->
    <div class="settings-panel" id="settingsPanel">
      <div style="margin-bottom:16px;">
        <label style="font-size:10px; text-transform:uppercase; color:var(--ink-dim); font-weight:600;">YouTube API Key</label>
        <input type="text" id="ytApiKey" class="tag-container" style="width:100%; margin-top:6px;" placeholder="AIzaSy..." onchange="saveConfig()">
      </div>
      <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
        <label style="font-size:10px; text-transform:uppercase; color:var(--ink-dim); font-weight:600;">Verified Base Channels</label>
        <span style="font-size:12px; color:var(--accent);" id="baseCount">0 Saved</span>
      </div>
      <div class="channel-grid" id="channelGrid">
        <!-- Channel Cards Load Here -->
      </div>
    </div>

    <!-- Tag Inputs -->
    <div style="font-size:11px; margin-bottom:6px; color:var(--ink-dim); font-weight:600;">1. DISCOVERY SEEDS (Type & Press Enter)</div>
    <div class="tag-container" id="seedContainer">
      <input type="text" id="seedInput" placeholder="e.g. street food, funny animals...">
    </div>

    <div style="font-size:11px; margin-bottom:6px; color:var(--ink-dim); font-weight:600;">2. NICHE VERIFICATION KEYWORDS (Type & Press Enter)</div>
    <div class="tag-container" id="nicheContainer">
      <input type="text" id="nicheInput" placeholder="e.g. spicy, vendor, burger...">
    </div>

    <div style="font-size:11px; margin-bottom:6px; color:var(--ink-dim); font-weight:600;">3. QUALIFICATION THRESHOLD</div>
    <input type="number" id="thresholdInput" class="tag-container" style="width:100%; color:#fff; font-size:14px;" value="5" onchange="saveConfig()">

    <!-- Action Buttons -->
    <div class="action-grid">
      <button class="solid btn-discover" id="btnDiscover" onclick="runPipeline('discover')">
        🔍 Discover & Add to Base
      </button>
      <button class="solid btn-analyze" id="btnAnalyze" onclick="runPipeline('analyze')">
        ⚡ Analyze Saved Base List
      </button>
    </div>

    <div class="status" id="mainStatus">System Ready.</div>

    <div class="table-container" id="tableContainer">
      <table class="glass-table">
        <thead id="tableHead"></thead>
        <tbody id="tableBody"></tbody>
      </table>
    </div>

  </div>
</div>

<script>
  let config = { seeds: [], niches: [], threshold: 5, apiKey: '' };
  let baseChannels = {}; // Master permanent storage

  // --- 1. LOGIN SYSTEM ---
  window.onload = () => {
    const savedPin = localStorage.getItem('profile_pin');
    if (!savedPin) {
      document.getElementById('loginTitle').innerText = 'Welcome Setup';
      document.getElementById('loginSub').innerText = 'Create a PIN to permanently lock your profile and data.';
    }
  };

  function checkLogin() {
    const input = document.getElementById('pinInput').value;
    const savedPin = localStorage.getItem('profile_pin');
    
    if (!input) return;

    if (!savedPin) {
      localStorage.setItem('profile_pin', input);
      unlockSystem();
    } else if (input === savedPin) {
      unlockSystem();
    } else {
      document.getElementById('loginSub').innerText = '❌ Incorrect PIN';
      document.getElementById('loginSub').style.color = '#ff453a';
    }
  }

  function unlockSystem() {
    document.getElementById('loginOverlay').style.display = 'none';
    loadPermanentData();
    setupTagListeners();
  }

  // --- 2. PERMANENT DATA MANAGEMENT ---
  function loadPermanentData() {
    const savedConfig = localStorage.getItem('app_config');
    if (savedConfig) {
      config = JSON.parse(savedConfig);
      document.getElementById('ytApiKey').value = config.apiKey || '';
      document.getElementById('thresholdInput').value = config.threshold || 5;
      renderTags('seedContainer', config.seeds);
      renderTags('nicheContainer', config.niches);
    }

    const savedChannels = localStorage.getItem('base_channels');
    if (savedChannels) {
      baseChannels = JSON.parse(savedChannels);
      syncBackend(); // Push local master list to backend memory instantly
    }
    renderChannelGrid();
  }

  function saveConfig() {
    config.apiKey = document.getElementById('ytApiKey').value.trim();
    config.threshold = parseInt(document.getElementById('thresholdInput').value) || 5;
    localStorage.setItem('app_config', JSON.stringify(config));
  }

  async function syncBackend() {
    // Keeps backend JSON in sync with browser master list
    await fetch('/api/sync-channels', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(baseChannels)
    });
  }

  // --- 3. TAG SYSTEM ---
  function setupTagListeners() {
    const handleEnter = (e, arrKey, containerId, inputId) => {
      if (e.key === 'Enter' && e.target.value.trim()) {
        const val = e.target.value.trim();
        if (!config[arrKey].includes(val)) {
          config[arrKey].push(val);
          saveConfig();
          renderTags(containerId, config[arrKey]);
        }
        e.target.value = '';
      }
    };
    document.getElementById('seedInput').addEventListener('keypress', (e) => handleEnter(e, 'seeds', 'seedContainer', 'seedInput'));
    document.getElementById('nicheInput').addEventListener('keypress', (e) => handleEnter(e, 'niches', 'nicheContainer', 'nicheInput'));
  }

  function renderTags(containerId, arr) {
    const container = document.getElementById(containerId);
    const input = container.querySelector('input');
    container.innerHTML = '';
    
    arr.forEach((tag, idx) => {
      const span = document.createElement('div');
      span.className = 'tag';
      span.innerHTML = `${tag} <span onclick="removeTag('${containerId}', ${idx})">&times;</span>`;
      container.appendChild(span);
    });
    container.appendChild(input);
  }

  window.removeTag = function(containerId, idx) {
    const arrKey = containerId === 'seedContainer' ? 'seeds' : 'niches';
    config[arrKey].splice(idx, 1);
    saveConfig();
    renderTags(containerId, config[arrKey]);
  }

  // --- 4. BASE MANAGER (UI) ---
  function toggleSettings() {
    const panel = document.getElementById("settingsPanel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
  }

  function renderChannelGrid() {
    const grid = document.getElementById('channelGrid');
    grid.innerHTML = '';
    const keys = Object.keys(baseChannels);
    document.getElementById('baseCount').innerText = `${keys.length} Saved`;

    keys.forEach(cId => {
      const c = baseChannels[cId];
      const div = document.createElement('div');
      div.className = 'channel-card';
      div.innerHTML = `
        <img src="${c.logo || 'https://via.placeholder.com/36'}" alt="logo">
        <div class="c-info">
          <div class="c-name">${c.title}</div>
        </div>
        <div class="c-del" onclick="deleteChannel('${cId}')">&times;</div>
      `;
      grid.appendChild(div);
    });
  }

  window.deleteChannel = function(cId) {
    delete baseChannels[cId];
    localStorage.setItem('base_channels', JSON.stringify(baseChannels));
    syncBackend();
    renderChannelGrid();
  }

  // --- 5. PIPELINE EXECUTION ---
  function setStatus(msg, type = '') {
    const el = document.getElementById('mainStatus');
    el.textContent = msg; el.className = 'status ' + type;
  }

  function runPipeline(actionType) {
    if (!config.apiKey) return setStatus("API Key required in Settings.", "error");
    
    document.getElementById('btnDiscover').disabled = true;
    document.getElementById('btnAnalyze').disabled = true;
    document.getElementById('tableContainer').style.display = 'none';

    let url = '';
    if (actionType === 'discover') {
      if (config.seeds.length === 0 || config.niches.length === 0) {
        setStatus("Seeds and Niche tags are required for Discovery.", "error");
        enableBtns(); return;
      }
      const sParams = encodeURIComponent(config.seeds.join(','));
      const nParams = encodeURIComponent(config.niches.join(','));
      url = `/api/discover?api_key=${config.apiKey}&seeds=${sParams}&niches=${nParams}&threshold=${config.threshold}`;
    } else {
      if (Object.keys(baseChannels).length === 0) {
        setStatus("Your Base List is empty. Run Discovery first.", "error");
        enableBtns(); return;
      }
      url = `/api/analyze?api_key=${config.apiKey}`;
    }

    const eventSource = new EventSource(url);

    eventSource.onmessage = function(event) {
      const data = JSON.parse(event.data);
      
      if (data.status === 'progress') {
        setStatus(data.msg, "active");
      } 
      else if (data.status === 'channel_found') {
        // Permanently add new channel to browser master list
        baseChannels[data.channel.id] = data.channel.data;
        localStorage.setItem('base_channels', JSON.stringify(baseChannels));
        syncBackend();
        renderChannelGrid();
      }
      else if (data.status === 'done') {
        setStatus(data.msg, "success");
        if (data.results) renderTable(data.results);
        eventSource.close(); enableBtns();
      } 
      else if (data.status === 'error') {
        setStatus("Error: " + data.msg, "error");
        eventSource.close(); enableBtns();
      }
    };
    eventSource.onerror = function() {
      setStatus("Stream finished or disconnected.", "success");
      eventSource.close(); enableBtns();
    };
  }

  function enableBtns() {
    document.getElementById('btnDiscover').disabled = false;
    document.getElementById('btnAnalyze').disabled = false;
  }

  function renderTable(results) {
    if (results.length === 0) return setStatus("No results matched criteria.", "error");
    document.getElementById('tableContainer').style.display = 'block';
    
    const thead = document.getElementById('tableHead');
    const tbody = document.getElementById('tableBody');

    thead.innerHTML = `<tr><th>Video</th><th>Title</th><th>Base Channel</th><th>Views</th><th>Velocity (VPH)</th><th>Links</th></tr>`;
    
    let html = '';
    results.forEach(r => {
      html += `<tr>
        <td><img class="thumb-img" src="${r.thumbnail}" alt="thumb"></td>
        <td class="trunc" title="${r.title}">${r.title}</td>
        <td><img class="logo-img" src="${r.logo}">${r.channel}</td>
        <td>${r.views.toLocaleString()} 👁️</td>
        <td><span class="badge">🔥 ${r.vph.toLocaleString()}/hr</span></td>
        <td>
          <a class="table-btn" href="${r.videoLink}" target="_blank">▶️</a>
          <a class="table-btn" href="${r.channelLink}" target="_blank">👤</a>
        </td>
      </tr>`;
    });
    tbody.innerHTML = html;
  }
</script>
</body>
</html>
"""

@app.route("/")
def index():
    return HTML_UI

@app.route("/api/sync-channels", methods=["POST"])
def sync_channels():
    # Frontend master list pushes here so the backend can use it for Analysis
    global BASE_CHANNELS
    BASE_CHANNELS = request.json or {}
    return jsonify({"success": True})

@app.route('/api/discover', methods=['GET'])
def auto_discover():
    api_key = request.args.get('api_key')
    seeds = request.args.get('seeds', '').split(',')
    niche_keywords = [k.strip().lower() for k in request.args.get('niches', '').split(',') if k.strip()]
    threshold = int(request.args.get('threshold', 5))

    def generate():
        def emit(status, msg="", data=None, channel_info=None):
            payload = {"status": status, "msg": msg}
            if data is not None: payload["results"] = data
            if channel_info is not None: payload["channel"] = channel_info
            return f"data: {json.dumps(payload)}\n\n"

        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            new_channels = set()

            # 1. Search across all seed tags
            for seed in seeds:
                if not seed.strip(): continue
                yield emit('progress', f'Searching seed tag: "{seed}"...')
                search_res = youtube.search().list(q=seed.strip(), part="snippet", type="video", order="date", maxResults=15).execute()
                for item in search_res.get('items', []):
                    c_id = item['snippet']['channelId']
                    if c_id not in BASE_CHANNELS:
                        new_channels.add(c_id)

            yield emit('progress', f'Extracted {len(new_channels)} undocumented channels. Running Niche Verification...')

            # 2. Qualify Channels
            new_channels = list(new_channels)
            if new_channels:
                for i in range(0, len(new_channels), 50):
                    batch = new_channels[i:i+50]
                    c_res = youtube.channels().list(part="contentDetails,snippet", id=",".join(batch)).execute()
                    
                    for c_item in c_res.get('items', []):
                        c_id = c_item['id']
                        c_title = c_item['snippet']['title']
                        logo = c_item['snippet']['thumbnails']['default']['url']
                        
                        try:
                            uploads_id = c_item['contentDetails']['relatedPlaylists']['uploads']
                        except KeyError:
                            continue 

                        # Check last 30 videos
                        pl_res = youtube.playlistItems().list(part="snippet", playlistId=uploads_id, maxResults=30).execute()
                        
                        match_count = 0
                        for pl_item in pl_res.get('items', []):
                            title = pl_item['snippet']['title'].lower()
                            if any(k in title for k in niche_keywords): match_count += 1

                        if match_count >= threshold:
                            channel_data = {"title": c_title, "uploads_id": uploads_id, "logo": logo}
                            BASE_CHANNELS[c_id] = channel_data
                            # Stream directly to browser storage
                            yield emit('channel_found', f'✅ Added to Base: {c_title} ({match_count} matches)', channel_info={"id": c_id, "data": channel_data})
                        else:
                            yield emit('progress', f'❌ Discarded: {c_title} ({match_count} matches)')

            yield emit('done', f'Discovery Sequence Complete. Saved {len(BASE_CHANNELS)} total channels to Base.')

        except Exception as e:
            yield emit('error', str(e))

    return Response(generate(), mimetype='text/event-stream')


@app.route('/api/analyze', methods=['GET'])
def auto_analyze():
    api_key = request.args.get('api_key')

    def generate():
        def emit(status, msg="", data=None):
            payload = {"status": status, "msg": msg}
            if data is not None: payload["results"] = data
            return f"data: {json.dumps(payload)}\n\n"

        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
            all_shorts = []
            
            total_base = len(BASE_CHANNELS)
            yield emit('progress', f'Initializing scrape sequence for {total_base} Base Channels...')

            for idx, (c_id, c_data) in enumerate(BASE_CHANNELS.items()):
                yield emit('progress', f'[{idx+1}/{total_base}] Analyzing {c_data["title"]}...')
                uploads_id = c_data.get('uploads_id')
                if not uploads_id: continue

                pl_res = youtube.playlistItems().list(part="contentDetails", playlistId=uploads_id, maxResults=15).execute()
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
                        
                        # Extract Video Thumbnail
                        try:
                            thumb = v_item['snippet']['thumbnails']['medium']['url']
                        except KeyError:
                            thumb = v_item['snippet']['thumbnails']['default']['url']

                        all_shorts.append({
                            "title": v_item['snippet']['title'],
                            "channel": c_data['title'],
                            "logo": c_data.get('logo', ''),
                            "thumbnail": thumb,
                            "views": views, "vph": round(vph, 1), "age_hours": round(age_hours, 1),
                            "videoLink": f"https://www.youtube.com/watch?v={v_item['id']}",
                            "channelLink": f"https://www.youtube.com/channel/{c_id}"
                        })

            yield emit('progress', 'Sorting matrix by View Velocity...')
            all_shorts.sort(key=lambda x: x['vph'], reverse=True)
            yield emit('done', 'Base Analysis Complete!', all_shorts[:100])

        except Exception as e:
            yield emit('error', str(e))

    return Response(generate(), mimetype='text/event-stream')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
