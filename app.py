import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta
import streamlit.components.v1 as components

# --- PAGE SETUP ---
st.set_page_config(page_title="Research Tool", layout="centered", initial_sidebar_state="collapsed")

# --- APPLE MINIMAL / GLASSMORPHIC CSS ---
st.markdown("""
<style>
    /* Hide default Streamlit headers, menus, and sidebar toggle */
    [data-testid="stHeader"], [data-testid="collapsedControl"] { display: none !important; }
    
    /* Base Theme & Background */
    [data-testid="stAppViewContainer"] {
        background-color: #030304;
        color: #f5f5f7;
        font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    /* Ambient Glow Background */
    [data-testid="stAppViewContainer"]::before, [data-testid="stAppViewContainer"]::after {
        content: ''; position: fixed; border-radius: 50%; filter: blur(130px); z-index: -1; opacity: 0.35;
    }
    [data-testid="stAppViewContainer"]::before { top: -10%; left: -10%; width: 40vw; height: 40vw; background: #5e5ce6; }
    [data-testid="stAppViewContainer"]::after { bottom: -10%; right: -10%; width: 40vw; height: 40vw; background: #bf5af2; }

    /* Typography Overrides */
    h1, h2, h3, h4, h5, h6, p, span, label { color: #f5f5f7 !important; }
    
    /* Settings Expander (Glassmorphic) */
    [data-testid="stExpander"] {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(28px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        margin-bottom: 24px;
        overflow: hidden;
    }
    [data-testid="stExpander"] summary { padding: 12px 16px; font-weight: 600; }
    [data-testid="stExpander"] summary:hover { background: rgba(255, 255, 255, 0.08); }

    /* Inputs, Sliders & Selectboxes */
    .stTextInput>div>div>input, .stSelectbox>div>div>div, .stNumberInput>div>div>input {
        background-color: rgba(0, 0, 0, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    .stTextInput>div>div>input:focus, .stSelectbox>div>div>div:focus {
        border-color: #0a84ff !important;
        box-shadow: inset 0 0 0 1px #0a84ff !important;
    }
    
    /* Buttons */
    .stButton>button {
        background: #fff !important;
        color: #000 !important;
        border-radius: 14px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 10px 24px !important;
        transition: all 0.2s ease !important;
        width: 100%;
    }
    .stButton>button:hover { transform: scale(0.98); opacity: 0.9; }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 6px;
        gap: 4px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 10px 16px;
        color: rgba(255, 255, 255, 0.5);
        border: none !important;
        background: transparent !important;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255, 255, 255, 0.15) !important;
        color: #fff !important;
    }

    /* DataFrame / Table Styling */
    [data-testid="stDataFrame"] {
        background: rgba(255, 255, 255, 0.03);
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 8px;
    }
    [data-testid="stDataFrame"] div { color: #f5f5f7 !important; }
</style>
""", unsafe_allow_html=True)

# --- INJECT LOCAL STORAGE SCRIPT ---
components.html("""
<script>
    const key = localStorage.getItem('yt_api_key') || '';
    if (key) { window.parent.postMessage({type: 'streamlit:setComponentValue', value: key}, '*'); }
</script>
""", height=0)

# --- HEADER & SETTINGS ---
st.title("BulkDrop Intelligence")

if 'youtube' not in st.session_state:
    st.session_state.youtube = None

with st.expander("⚙️ API Configuration"):
    api_key_input = st.text_input("YouTube API v3 Key", type="password", placeholder="Paste API Key here...")
    if st.button("Save API Key"):
        st.components.v1.html(f"<script>localStorage.setItem('yt_api_key', '{api_key_input}');</script>", height=0)
        try:
            service = build('youtube', 'v3', developerKey=api_key_input)
            service.videoCategories().list(part='snippet', regionCode='US').execute()
            st.session_state.youtube = service
            st.success("✅ Key saved and authenticated successfully!")
        except Exception as e:
            st.error("❌ Invalid API Key.")

# Auto-authenticate if key is present but session is empty
if api_key_input and st.session_state.youtube is None:
    try:
        st.session_state.youtube = build('youtube', 'v3', developerKey=api_key_input)
    except:
        pass

# --- HELPER FUNCTIONS ---
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
            "Video Link": f"https://www.youtube.com/watch?v={item['id'] if isinstance(item['id'], str) else item['id'].get('videoId')}",
            "Channel Link": f"https://www.youtube.com/channel/{c_id}"
        })
    return pd.DataFrame(data)

def display_responsive_table(df):
    st.dataframe(
        df,
        column_config={
            "Video Link": st.column_config.LinkColumn("Watch Video", display_text="▶️ Watch"),
            "Channel Link": st.column_config.LinkColumn("Visit Channel", display_text="👤 Open Channel"),
            "Views": st.column_config.NumberColumn(format="%d 👁️"),
            "Subs": st.column_config.NumberColumn(format="%d 👥"),
            "Ch Age (Days)": st.column_config.ProgressColumn("Channel Age", format="%d days", min_value=0, max_value=365*2)
        },
        hide_index=True,
        use_container_width=True
    )

# --- APP LOGIC (TABS SWAPPED) ---
if st.session_state.youtube:
    # Research Tool is now Tab 1 (Default)
    tab1, tab2 = st.tabs(["🔍 Research Tool", "⚡ Trending Now"])

    with tab1:
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            # Default value is now completely empty
            search_query = st.text_input("Enter Niche Keyword", value="", placeholder="e.g. AI Tools, Minecraft")
        with col2:
            period = st.selectbox("Time Period", ["Last 24 Hours", "Last 7 Days", "Last 30 Days"])
        with col3:
            max_vids = st.slider("Results", 10, 50, 20)

        if st.button("Find Exploding Content"):
            if not search_query.strip():
                st.warning("⚠️ Please enter a keyword to search.")
            else:
                with st.spinner("Searching..."):
                    days_map = {"Last 24 Hours": 1, "Last 7 Days": 7, "Last 30 Days": 30}
                    after_date = (datetime.now(timezone.utc) - timedelta(days=days_map[period])).isoformat()
                    
                    search_res = st.session_state.youtube.search().list(
                        q=search_query, part="snippet", type="video", order="viewCount", 
                        publishedAfter=after_date, maxResults=max_vids
                    ).execute()
                    
                    v_ids = [item['id']['videoId'] for item in search_res.get('items', []) if 'videoId' in item['id']]
                    if v_ids:
                        video_stats_res = st.session_state.youtube.videos().list(
                            part="snippet,statistics", id=",".join(v_ids)
                        ).execute()
                        df_search = process_results(st.session_state.youtube, video_stats_res.get('items', []))
                        display_responsive_table(df_search)
                    else:
                        st.info("No results found for this period. Try widening your search.")

    with tab2:
        if st.button("Refresh Trending"):
            with st.spinner("Fetching global trends..."):
                res = st.session_state.youtube.videos().list(
                    part="snippet,statistics", chart="mostPopular", maxResults=25
                ).execute()
                df_trend = process_results(st.session_state.youtube, res.get('items', []))
                display_responsive_table(df_trend)
else:
    st.info("👋 Open the **⚙️ API Configuration** menu above and enter your YouTube API Key to begin.")
