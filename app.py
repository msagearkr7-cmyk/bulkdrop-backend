import streamlit as st
import pandas as pd
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta

# --- PAGE SETUP ---
st.set_page_config(page_title="Niche Finder Intelligence", layout="wide", page_icon="🔥")

# --- APPLE-GLASS DESIGN SYSTEM ---------------------------------------------
# Matches the BulkDrop Pro reference 1:1: dark canvas, drifting blurred color
# fields, one seamless frosted glass panel holding everything (no sidebar,
# no nested boxes), pill buttons, and a small gear popover for auth setup.
st.markdown("""
<style>
  :root {
    --glass-fill: rgba(255, 255, 255, 0.07);
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

  /* Hide the sidebar entirely — auth now lives in the gear popover */
  section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

  html, body, [data-testid="stAppViewContainer"] {
    background: #030304 !important;
    color: var(--ink) !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    touch-action: pan-y !important;
    -webkit-overflow-scrolling: touch !important;
    overscroll-behavior: contain;
  }

  [data-testid="stAppViewContainer"] { position: relative; overflow-x: hidden; }
  [data-testid="stAppViewContainer"]::before,
  [data-testid="stAppViewContainer"]::after {
    content: '';
    position: fixed;
    border-radius: 50%;
    filter: blur(130px);
    z-index: 0;
    opacity: 0.45;
    pointer-events: none;
    animation: drift 18s infinite alternate ease-in-out;
  }
  [data-testid="stAppViewContainer"]::before { top: -12%; left: -14%; width: 46vw; height: 46vw; background: #5e5ce6; }
  [data-testid="stAppViewContainer"]::after { bottom: -14%; right: -12%; width: 42vw; height: 42vw; background: #bf5af2; animation-delay: -6s; }
  @keyframes drift { 0% { transform: translate(0,0) scale(1); } 100% { transform: translate(4%,4%) scale(1.12); } }
  @media (prefers-reduced-motion: reduce) {
    [data-testid="stAppViewContainer"]::before, [data-testid="stAppViewContainer"]::after { animation: none; }
  }

  .block-container { position: relative; z-index: 1; padding-top: 2.5rem; max-width: 700px; }

  /* ---- Brand header ---- */
  .brand-wrap { text-align: center; margin-bottom: 20px; }
  .brand-mark { display: block; font-size: 30px; font-weight: 700; letter-spacing: -0.02em; color: #fff; }
  .brand-sub { display: block; margin-top: 5px; font-size: 12px; font-weight: 500; letter-spacing: 0.14em; text-transform: uppercase; color: var(--ink-faint); }

  /* ---- Quick row (gear / auth button) ---- */
  .quick-row-spacer { display: flex; justify-content: flex-end; margin-bottom: -6px; }

  /* Popover trigger -> small pill-glass button, same as reference .icon-glass/.pill-glass */
  [data-testid="stPopover"] > div > button {
    background: var(--glass-fill) !important;
    -webkit-backdrop-filter: blur(28px) saturate(160%);
    backdrop-filter: blur(28px) saturate(160%);
    border: 1px solid var(--glass-border) !important;
    color: var(--ink-dim) !important;
    border-radius: 999px !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    padding: 8px 16px !important;
    min-height: 36px !important;
    width: auto !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.14) inset, 0 8px 20px rgba(0,0,0,0.35);
  }
  [data-testid="stPopover"] > div > button:hover { color: #fff !important; }
  [data-testid="stPopoverBody"] {
    background: #0a0a0d !important;
    border: 1px solid var(--glass-border-soft) !important;
    border-radius: var(--radius-md) !important;
    -webkit-backdrop-filter: blur(28px);
    backdrop-filter: blur(28px);
  }

  /* ---- The ONE glass panel that holds everything below the header ---- */
  div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] > div[data-testid="stTabs"]) {
    background: var(--glass-fill) !important;
    -webkit-backdrop-filter: blur(28px) saturate(160%);
    backdrop-filter: blur(28px) saturate(160%);
    border: 1px solid var(--glass-border) !important;
    border-radius: var(--radius-lg) !important;
    box-shadow: 0 1px 0 rgba(255,255,255,0.14) inset, 0 20px 50px rgba(0,0,0,0.45);
    padding: 8px;
  }

  /* ---- Tabs styled as pill toggles ---- */
  [data-testid="stTabs"] [role="tablist"] {
    gap: 10px;
    border-bottom: none !important;
    background: rgba(0,0,0,0.28);
    border: 1px solid var(--glass-border-soft);
    border-radius: 999px;
    padding: 6px;
  }
  [data-testid="stTabs"] [role="tab"] {
    border-radius: 999px !important;
    color: var(--ink-dim) !important;
    font-weight: 600;
    font-size: 13px;
    padding: 10px 18px !important;
  }
  [data-testid="stTabs"] [aria-selected="true"] { background: var(--accent) !important; color: #fff !important; }
  [data-testid="stTabs"] [data-baseweb="tab-highlight"] { display: none; }

  /* ---- Inputs ---- */
  input, select, textarea {
    font-size: 16px !important;
    background: rgba(0,0,0,0.28) !important;
    color: var(--ink) !important;
    border: 1px solid var(--glass-border-soft) !important;
    border-radius: var(--radius-sm) !important;
  }
  input:focus, textarea:focus {
    border-color: rgba(255,255,255,0.3) !important;
    box-shadow: 0 0 0 4px rgba(10,132,255,0.12) !important;
  }
  ::placeholder { color: var(--ink-faint) !important; }
  label, .stMarkdown p, [data-testid="stWidgetLabel"] p, [data-testid="stCaptionContainer"] { color: var(--ink-dim) !important; }
  div[data-baseweb="select"] > div { min-height: 44px; background: rgba(0,0,0,0.28) !important; border-radius: var(--radius-sm) !important; }

  /* ---- Segmented control ---- */
  div[data-testid="stSegmentedControl"] { background: rgba(0,0,0,0.32); border-radius: 999px; padding: 5px; border: 1px solid var(--glass-border-soft); }
  div[data-testid="stSegmentedControl"] label { min-height: 40px; font-size: 13px; font-weight: 600; border-radius: 999px !important; color: var(--ink-dim) !important; }

  /* ---- Buttons ---- */
  .stButton > button, .stDownloadButton > button {
    min-height: 48px; font-size: 14px; font-weight: 600; border-radius: 16px; width: 100%;
    background: var(--accent) !important; color: #fff !important; border: none !important; transition: all 0.15s;
  }
  .stButton > button:hover { background: #0074e0 !important; }
  .stButton > button:active { transform: scale(0.97); }

  /* ---- Dataframe / table, living inside the same panel ---- */
  [data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {
    touch-action: pan-x pan-y !important;
    -webkit-overflow-scrolling: touch !important;
    border-radius: var(--radius-md) !important;
    overflow: hidden;
    border: 1px solid var(--glass-border-soft) !important;
    background: rgba(0,0,0,0.22) !important;
  }
  [data-testid="stDataFrame"] div[role="grid"] { touch-action: pan-x pan-y !important; }

  /* ---- Status badges ---- */
  .status-badge { display: inline-block; font-size: 11px; font-weight: 600; padding: 5px 12px; border-radius: 999px; letter-spacing: 0.02em; margin-bottom: 10px; }
  .badge-live { color: var(--accent-2); background: rgba(100, 210, 255, 0.15); }
  .badge-idle { color: var(--ink-dim); background: rgba(255,255,255,0.08); }

  @media (max-width: 480px) {
    .brand-mark { font-size: 26px; }
    .block-container { padding-left: 1rem; padding-right: 1rem; }
  }
</style>
""", unsafe_allow_html=True)

# --- BRAND HEADER ---
st.markdown("""
<div class="brand-wrap">
  <span class="brand-mark">Niche Finder Intelligence</span>
  <span class="brand-sub">YouTube Explosion &amp; Velocity Engine</span>
</div>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""
if 'youtube' not in st.session_state:
    st.session_state.youtube = None
if 'df_trend' not in st.session_state:
    st.session_state.df_trend = None
if 'df_search' not in st.session_state:
    st.session_state.df_search = None

# --- SMALL "AUTHENTICATION SETUP" GEAR BUTTON (replaces sidebar) ---
st.markdown('<div class="quick-row-spacer">', unsafe_allow_html=True)
with st.popover("⚙️ Authentication Setup"):
    st.caption("YOUTUBE API v3 KEY")
    key_input = st.text_input(
        "API key",
        value=st.session_state.api_key,
        type="password",
        placeholder="AIzaSy...",
        label_visibility="collapsed",
    )
    if st.button("Save Settings", key="save_key_btn"):
        st.session_state.api_key = key_input.strip()
        st.session_state.youtube = None  # force reconnect with the new key
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- HELPER FUNCTIONS (unchanged logic) ---
def connect_to_youtube(key):
    if "streamlit" in key.lower() or len(key) < 10:
        st.error("⚠️ Please paste a valid API Key (starts with 'AIza'), not a command.")
        return None
    try:
        service = build('youtube', 'v3', developerKey=key)
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
                max_value=365 * 2
            )
        },
        hide_index=True,
        use_container_width=True,
        height=height
    )

# --- CONNECT ---
if st.session_state.api_key:
    if st.session_state.youtube is None:
        st.session_state.youtube = connect_to_youtube(st.session_state.api_key)
else:
    st.markdown('<span class="status-badge badge-idle">Awaiting key — tap "Authentication Setup" above</span>', unsafe_allow_html=True)
    st.stop()

# --- MAIN GLASS PANEL: tabs + tables all live together, no separate boxes ---
if st.session_state.youtube:
    st.markdown('<span class="status-badge badge-live">● Connected</span>', unsafe_allow_html=True)

    with st.container(border=True):
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
              
