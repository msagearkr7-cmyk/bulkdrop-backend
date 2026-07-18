import streamlit as st
from googleapiclient.discovery import build

# --- BULKDROP GLASSMORPHIC UI ---
st.set_page_config(page_title="Niche Intelligence", layout="centered")
st.markdown("""
<style>
    /* Full Page Dark Background */
    [data-testid="stAppViewContainer"] { background-color: #000; }
    
    /* Replicating the BulkDrop Glass Panel */
    .glass-panel {
        background: rgba(30, 30, 35, 0.4);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 24px 48px rgba(0, 0, 0, 0.4);
        margin-bottom: 16px;
        color: #f5f5f7;
    }
    
    h1 { color: #fff; font-size: 24px; text-align: center; margin-bottom: 24px; }
    .vid-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; line-height: 1.4; }
    .vid-meta { font-size: 12px; color: rgba(255,255,255,0.5); margin-bottom: 16px; }
    
    /* Styled Button to match BulkDrop */
    .dl-btn {
        display: block; width: 100%; text-align: center; background: #0a84ff;
        color: white; padding: 12px; border-radius: 14px; text-decoration: none;
        font-weight: 600; font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

st.title("BulkDrop Niche Finder")

# --- UI INPUTS ---
api_key = st.text_input("YouTube API Key", type="password")
query = st.text_input("Search Niche", "AI Tools")

if st.button("Find Exploding Content"):
    if not api_key:
        st.error("Enter API Key")
    else:
        yt = build('youtube', 'v3', developerKey=api_key)
        res = yt.search().list(q=query, part="snippet", type="video", order="viewCount", maxResults=5).execute()
        v_ids = [i['id']['videoId'] for i in res['items']]
        details = yt.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()

        for item in details['items']:
            title = item['snippet']['title']
            channel = item['snippet']['channelTitle']
            views = int(item['statistics'].get('viewCount', 0))
            
            # --- APPLYING BULKDROP GLASS STYLE ---
            st.markdown(f"""
            <div class="glass-panel">
                <div class="vid-title">{title}</div>
                <div class="vid-meta">👤 {channel} &nbsp; • &nbsp; 👁️ {views:,} views</div>
                <a class="dl-btn" href="https://www.youtube.com/watch?v={item['id']}" target="_blank">Watch Video</a>
            </div>
            """, unsafe_allow_html=True)
