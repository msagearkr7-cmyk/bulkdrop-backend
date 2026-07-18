from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/')
def home():
    return "BulkDrop Multi-Platform Engine Running"

@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    cookies_text = data.get('cookies', '').strip()
    use_proxy = data.get('proxy', False)
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    # Create a unique cookie file for this specific request to prevent race conditions
    unique_id = uuid.uuid4().hex
    cookie_filename = f"cookies_{unique_id}.txt"
    
    if cookies_text:
        with open(cookie_filename, 'w', encoding='utf-8') as f:
            f.write(cookies_text)

    # Advanced stealth configuration to mimic browser signatures
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
            # PROXY MODE (Instagram, TikTok & Facebook): Streams directly through Render
            temp_filename = f"temp_{unique_id}.mp4"
            ydl_opts['outtmpl'] = temp_filename
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_filename):
                with open(temp_filename, 'rb') as f:
                    video_data = f.read()
                
                # Cleanup files immediately
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
            # EXTRACTION MODE (YouTube): Extracts direct URL link
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if not direct_url and 'formats' in info:
                    direct_url = info['formats'][-1]['url']
            
            if os.path.exists(cookie_filename):
                os.remove(cookie_filename)
                
            return jsonify({'url': direct_url})
                
    except Exception as e:
        # Fallback cleanup on failure
        if os.path.exists(cookie_filename):
            try: os.remove(cookie_filename)
            except: pass
        if 'temp_filename' in locals() and os.path.exists(temp_filename):
            try: os.remove(temp_filename)
            except: pass
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
