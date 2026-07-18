import streamlit as st
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta

# --- BULKDROP STYLE OVERLAY ---
st.set_page_config(page_title="Niche Finder", layout="centered")
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background-color: #000; }
    .glass-panel {
        background: rgba(30, 30, 35, 0.4);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 20px;
        margin-bottom: 16px;
        color: #f5f5f7;
    }
    .vid-title { font-size: 15px; font-weight: 700; margin-bottom: 8px; line-height: 1.3; color: #fff; }
    .vid-meta { font-size: 12px; color: rgba(255,255,255,0.6); margin-bottom: 12px; display: flex; gap: 10px; }
    .btn-row { display: flex; gap: 8px; }
    .btn-action { 
        background: rgba(255,255,255,0.1); color: #fff; padding: 8px 12px; 
        border-radius: 10px; text-decoration: none; font-size: 12px; font-weight: 600; flex: 1; text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("Niche Intelligence")

# --- ORIGINAL LOGIC ---
api_key = st.sidebar.text_input("YouTube API Key", type="password")

if 'youtube' not in st.session_state: st.session_state.youtube = None

if api_key:
    st.session_state.youtube = build('youtube', 'v3', developerKey=api_key)

if st.session_state.youtube:
    tab1, tab2 = st.tabs(["⚡ Trending", "🔍 Keyword Search"])

    def show_results(video_items):
        for item in video_items:
            title = item['snippet']['title']
            channel = item['snippet']['channelTitle']
            views = int(item['statistics'].get('viewCount', 0))
            v_id = item['id'] if isinstance(item['id'], str) else item['id'].get('videoId')
            
            # --- CARD UI ---
            st.markdown(f"""
            <div class="glass-panel">
                <div class="vid-title">{title}</div>
                <div class="vid-meta">👤 {channel} &nbsp; • &nbsp; 👁️ {views:,}</div>
                <div class="btn-row">
                    <a class="btn-action" href="https://www.youtube.com/watch?v={v_id}" target="_blank">▶ Watch</a>
                    <a class="btn-action" href="https://www.youtube.com/channel/{item['snippet']['channelId']}" target="_blank">👤 Channel</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with tab1:
        if st.button("Refresh Trending"):
            res = st.session_state.youtube.videos().list(part="snippet,statistics", chart="mostPopular", maxResults=10).execute()
            show_results(res.get('items', []))

    with tab2:
        query = st.text_input("Search Niche", "AI Tools")
        if st.button("Find Content"):
            res = st.session_state.youtube.search().list(q=query, part="snippet", type="video", order="viewCount", maxResults=10).execute()
            v_ids = [i['id']['videoId'] for i in res['items']]
            details = st.session_state.youtube.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()
            show_results(details.get('items', []))
            
