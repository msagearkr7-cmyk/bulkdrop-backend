import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="YT Explosion Finder", layout="wide")
st.title("🔥 YouTube Explosion & Velocity Finder")

# --- SIDEBAR: API KEY ---
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Enter YouTube API v3 Key", type="password")

# --- SESSION STATE ---
if 'youtube' not in st.session_state:
    st.session_state.youtube = None

# --- HELPER FUNCTIONS ---
def connect_to_youtube(key):
    if "streamlit" in key.lower() or len(key) < 10:
        st.error("⚠️ Please paste a valid API Key (starts with 'AIza'), not a command.")
        return None
    try:
        service = build('youtube', 'v3', developerKey=key)
        # Test call
        service.videoCategories().list(part='snippet', regionCode='US').execute()
        return service
    except Exception as e:
        st.error(f"❌ API Error: {e}")
        return None

def get_channel_info(yt_client, channel_ids):
    if not channel_ids: return {}
    res = yt_client.channels().list(part="snippet,statistics", id=",".join(channel_ids)).execute()
    return {item['id']: item for item in res.get('items', [])}

def process_results(yt_client, video_items):
    channel_ids = [item['snippet']['channelId'] for item in video_items]
    channels = get_channel_info(yt_client, channel_ids)
    
    data = []
    for item in video_items:
        c_id = item['snippet']['channelId']
        c_info = channels.get(c_id, {})
        
        pub_date = parser.isoparse(c_info['snippet']['publishedAt']) if c_info else datetime.now(timezone.utc)
        age_days = (datetime.now(timezone.utc) - pub_date).days
        
        data.append({
            "Title": item['snippet']['title'],
            "Channel": item['snippet']['channelTitle'],
            "Views": int(item['statistics'].get('viewCount', 0)) if 'statistics' in item else 0,
            "Subs": int(c_info['statistics'].get('subscriberCount', 0)) if c_info else 0,
            "Videos": int(c_info['statistics'].get('videoCount', 0)) if c_info else 0,
            "Ch Age (Days)": age_days,
            # These are the links we will make responsive
            "Video Link": f"https://www.youtube.com/watch?v={item['id'] if isinstance(item['id'], str) else item['id'].get('videoId')}",
            "Channel Link": f"https://www.youtube.com/channel/{c_id}"
        })
    return pd.DataFrame(data)

# --- TABLE RENDERER (The Responsive Part) ---
def display_responsive_table(df):
    """Renders the dataframe with clickable, responsive links."""
    st.dataframe(
        df,
        column_config={
            "Video Link": st.column_config.LinkColumn(
                "Watch Video", 
                help="Click to watch on YouTube",
                validate=r"^https://www.youtube.com/watch\?v=.*",
                display_text="▶️ Watch"
            ),
            "Channel Link": st.column_config.LinkColumn(
                "Visit Channel",
                help="Open Channel Page",
                display_text="👤 Open Channel"
            ),
            "Views": st.column_config.NumberColumn(format="%d 👁️"),
            "Subs": st.column_config.NumberColumn(format="%d 👥"),
            "Ch Age (Days)": st.column_config.ProgressColumn(
                "Channel Age",
                help="Days since channel creation",
                format="%d days",
                min_value=0,
                max_value=365*2 # Progress bar fills up if channel is 2 years old
            )
        },
        hide_index=True,
        use_container_width=True
    )

# --- APP LOGIC ---
if api_key_input:
    if st.session_state.youtube is None:
        st.session_state.youtube = connect_to_youtube(api_key_input)
else:
    st.info("👋 Please enter your API Key in the sidebar to begin.")
    st.stop()

if st.session_state.youtube:
    tab1, tab2 = st.tabs(["⚡ Trending Now", "🔍 Keyword Explosion"])

    with tab1:
        st.subheader("Global Trending Videos")
        if st.button("Refresh Trending"):
            with st.spinner("Fetching..."):
                res = st.session_state.youtube.videos().list(
                    part="snippet,statistics", chart="mostPopular", maxResults=25
                ).execute()
                df_trend = process_results(st.session_state.youtube, res.get('items', []))
                display_responsive_table(df_trend)

    with tab2:
        st.subheader("Find Exploding Videos by Topic")
        col1, col2, col3 = st.columns([2,1,1])
        with col1:
            search_query = st.text_input("Enter Niche Keyword", "AI Tools")
        with col2:
            period = st.selectbox("Time Period", ["Last 24 Hours", "Last 7 Days", "Last 30 Days"])
        with col3:
            max_vids = st.slider("Results", 10, 50, 20)

        if st.button("Find Exploding Content"):
            with st.spinner("Searching..."):
                days_map = {"Last 24 Hours": 1, "Last 7 Days": 7, "Last 30 Days": 30}
                after_date = (datetime.now(timezone.utc) - timedelta(days=days_map[period])).isoformat()
                
                search_res = st.session_state.youtube.search().list(
                    q=search_query, part="snippet", type="video", order="viewCount", 
                    publishedAfter=after_date, maxResults=max_vids
                ).execute()
                
                v_ids = [item['id']['videoId'] for item in search_res.get('items', [])]
                if v_ids:
                    video_stats_res = st.session_state.youtube.videos().list(
                        part="snippet,statistics", id=",".join(v_ids)
                    ).execute()
                    df_search = process_results(st.session_state.youtube, video_stats_res.get('items', []))
                    display_responsive_table(df_search)
