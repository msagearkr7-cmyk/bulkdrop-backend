import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="YT Explosion Finder", layout="wide", page_icon="🔥")

# --- MOBILE / TOUCH RELIABILITY CSS ---
# Streamlit's default dataframe grid (glide-data-grid) and small tap targets
# are the two biggest sources of "touch not working" / "scroll stuck" bugs
# on Android + iOS. This block fixes both without changing any data logic.
st.markdown("""
<style>
    /* Let the page scroll normally with touch anywhere, including over tables */
    html, body, [data-testid="stAppViewContainer"] {
        touch-action: pan-y !important;
        -webkit-overflow-scrolling: touch !important;
        overscroll-behavior: contain;
    }

    /* Dataframe / table container: enable smooth momentum scroll in both axes
       so a table wider than the screen doesn't trap the touch gesture */
    [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
        touch-action: pan-x pan-y !important;
        -webkit-overflow-scrolling: touch !important;
    }
    [data-testid="stDataFrame"] div[role="grid"] {
        touch-action: pan-x pan-y !important;
    }

    /* Bigger tap targets (Android/iOS guideline: 44px minimum) */
    .stButton > button, .stDownloadButton > button {
        min-height: 44px;
        font-size: 16px;
        border-radius: 10px;
        width: 100%;
    }

    /* Segmented control (time period) - bigger touch area, wraps cleanly */
    div[data-testid="stSegmentedControl"] label {
        min-height: 40px;
        font-size: 15px;
    }

    /* Inputs: 16px font stops iOS Safari auto-zoom-on-focus, which is a
       common cause of "the page jumped / my tap missed" complaints */
    input, select, textarea {
        font-size: 16px !important;
    }

    /* Selectbox / dropdown touch target */
    div[data-baseweb="select"] > div {
        min-height: 44px;
    }

    /* Stack the search row cleanly on narrow screens */
    @media (max-width: 640px) {
        [data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        h1 { font-size: 1.5rem !important; }
    }

    /* Sidebar collapses fine by default; just make its inputs touch-friendly too */
    section[data-testid="stSidebar"] input {
        min-height: 44px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🔥 YouTube Explosion & Velocity Finder")

# --- SIDEBAR: API KEY ---
st.sidebar.header("Configuration")
api_key_input = st.sidebar.text_input("Enter YouTube API v3 Key", type="password")

# --- SESSION STATE ---
if 'youtube' not in st.session_state:
    st.session_state.youtube = None
if 'df_trend' not in st.session_state:
    st.session_state.df_trend = None
if 'df_search' not in st.session_state:
    st.session_state.df_search = None

# --- HELPER FUNCTIONS (unchanged logic) ---
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
    if not channel_ids:
        return {}
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
            "Video Link": f"https://www.youtube.com/watch?v={item['id'] if isinstance(item['id'], str) else item['id'].get('videoId')}",
            "Channel Link": f"https://www.youtube.com/channel/{c_id}"
        })
    return pd.DataFrame(data)

# --- TABLE RENDERER (same columns/data, sized for reliable touch scroll) ---
def display_responsive_table(df):
    """Renders the dataframe with clickable, responsive links."""
    row_h = 35
    height = min(600, row_h * (len(df) + 1) + 3) if len(df) else 200
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
                max_value=365 * 2  # Progress bar fills up if channel is 2 years old
            )
        },
        hide_index=True,
        use_container_width=True,
        height=height
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
        if st.button("Refresh Trending", key="btn_trending"):
            with st.spinner("Fetching..."):
                res = st.session_state.youtube.videos().list(
                    part="snippet,statistics", chart="mostPopular", maxResults=25
                ).execute()
                st.session_state.df_trend = process_results(st.session_state.youtube, res.get('items', []))

        if st.session_state.df_trend is not None:
            display_responsive_table(st.session_state.df_trend)

    with tab2:
        st.subheader("Find Exploding Videos by Topic")

        search_query = st.text_input(
            "Niche Keyword",
            value="",
            placeholder="e.g. minecraft speedrun, true crime, budget travel"
        )

        col1, col2 = st.columns([2, 1])
        with col1:
            period = st.segmented_control(
                "Time Period",
                options=["Last 24 Hours", "Last 7 Days", "Last 30 Days"],
                default="Last 7 Days"
            )
        with col2:
            max_vids = st.selectbox(
                "Number of Results",
                options=[10, 20, 30, 40, 50],
                index=1
            )

        find_clicked = st.button("Find Exploding Content", key="btn_search")

        if find_clicked:
            if not search_query.strip():
                st.warning("⚠️ Enter a keyword first.")
            elif not period:
                st.warning("⚠️ Pick a time period.")
            else:
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
                        st.session_state.df_search = process_results(st.session_state.youtube, video_stats_res.get('items', []))
                    else:
                        st.session_state.df_search = pd.DataFrame()
                        st.info("No results for that keyword/time period. Try widening the time period.")

        if st.session_state.df_search is not None and not st.session_state.df_search.empty:
            display_responsive_table(st.session_state.df_search)
            
