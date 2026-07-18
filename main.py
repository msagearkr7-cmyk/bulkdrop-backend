from flask import Flask, request, jsonify, Response, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import uuid
from googleapiclient.discovery import build
from dateutil import parser
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
CORS(app, origins="*")

# --- 0. SERVE THE UI ---
@app.route('/')
def home():
    # This serves your index.html file from the root directory
    return send_from_directory('.', 'index.html')

# --- 1. MULTI-PLATFORM DOWNLOADER ---
@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    cookies_text = data.get('cookies', '').strip()
    use_proxy = data.get('proxy', False)
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    unique_id = uuid.uuid4().hex
    cookie_filename = f"cookies_{unique_id}.txt"
    
    if cookies_text:
        with open(cookie_filename, 'w', encoding='utf-8') as f:
            f.write(cookies_text)

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
        'geo_bypass': True,
        'geo_bypass_country': 'US'
    }
    
    if os.path.exists(cookie_filename):
        ydl_opts['cookiefile'] = cookie_filename
    
    try:
        if use_proxy:
            temp_filename = f"temp_{unique_id}.mp4"
            ydl_opts['outtmpl'] = temp_filename
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_filename):
                with open(temp_filename, 'rb') as f:
                    video_data = f.read()
                
                os.remove(temp_filename)
                if os.path.exists(cookie_filename):
                    os.remove(cookie_filename)
                
                return Response(
                    video_data,
                    mimetype='video/mp4',
                    headers={'Content-Disposition': f'attachment; filename="{unique_id}.mp4"'}
                )
            else:
                return jsonify({'error': 'Failed to stream media file from proxy server'}), 500
        else:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if not direct_url and 'formats' in info:
                    direct_url = info['formats'][-1]['url']
            
            if os.path.exists(cookie_filename):
                os.remove(cookie_filename)
                
            return jsonify({'url': direct_url})
                
    except Exception as e:
        if os.path.exists(cookie_filename):
            try: os.remove(cookie_filename)
            except: pass
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try: os.remove(temp_filename)
            except: pass
        return jsonify({'error': str(e)}), 500

# --- 2. YOUTUBE NICHE FINDER ---
@app.route('/youtube-niche', methods=['POST'])
def youtube_niche():
    data = request.json or {}
    api_key = data.get('api_key', '').strip()
    query = data.get('query', 'AI Tools')
    period = int(data.get('period', 7)) 
    max_results = int(data.get('max_results', 20))

    if not api_key:
        return jsonify({'error': 'YouTube API Key required'}), 400

    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        after_date = (datetime.now(timezone.utc) - timedelta(days=period)).isoformat()
        
        search_res = youtube.search().list(
            q=query, part="snippet", type="video", order="viewCount", 
            publishedAfter=after_date, maxResults=max_results
        ).execute()
        
        v_ids = [item['id']['videoId'] for item in search_res.get('items', []) if isinstance(item['id'], dict) and 'videoId' in item['id']]
        
        if not v_ids:
            return jsonify({'results': []})
        
        video_stats_res = youtube.videos().list(part="snippet,statistics", id=",".join(v_ids)).execute()
        video_items = video_stats_res.get('items', [])
        
        channel_ids = [item['snippet']['channelId'] for item in video_items]
        channels_res = youtube.channels().list(part="snippet,statistics", id=",".join(channel_ids)).execute()
        channels = {item['id']: item for item in channels_res.get('items', [])}
        
        results = []
        for item in video_items:
            c_id = item['snippet']['channelId']
            c_info = channels.get(c_id, {})
            
            pub_date = parser.isoparse(c_info['snippet']['publishedAt']) if c_info else datetime.now(timezone.utc)
            age_days = (datetime.now(timezone.utc) - pub_date).days
            
            results.append({
                "title": item['snippet']['title'],
                "channel": item['snippet']['channelTitle'],
                "views": int(item['statistics'].get('viewCount', 0)) if 'statistics' in item else 0,
                "subs": int(c_info['statistics'].get('subscriberCount', 0)) if c_info else 0,
                "age_days": age_days,
                "video_link": f"https://www.youtube.com/watch?v={item['id']}",
                "channel_link": f"https://www.youtube.com/channel/{c_id}"
            })
            
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
