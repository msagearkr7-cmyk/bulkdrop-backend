from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app, origins="*")

def handle_incoming_cookies(cookies_text):
    if cookies_text and cookies_text.strip():
        with open('cookies.txt', 'w', encoding='utf-8') as f:
            f.write(cookies_text.strip())
    elif os.path.exists('cookies.txt'):
        try:
            os.remove('cookies.txt')
        except:
            pass

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

    handle_incoming_cookies(cookies_text)

    # UPDATED STEALTH CONFIG
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        # Mimic a real browser fingerprint
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
        'referer': 'https://www.google.com/',
    }
    
    # Only use cookiefile if you actually provided cookies
    if os.path.exists('cookies.txt') and cookies_text:
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        if use_proxy:
            # TIKTOK/RESTRICTED MODE: Physical download to server
            temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
            ydl_opts['outtmpl'] = temp_filename
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_filename):
                with open(temp_filename, 'rb') as f:
                    video_data = f.read()
                os.remove(temp_filename)
                return Response(
                    video_data,
                    mimetype='video/mp4',
                    headers={'Content-Disposition': 'attachment; filename="video.mp4"'}
                )
        else:
            # INSTAGRAM/YOUTUBE MODE: Extraction
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if not direct_url and info.get('requested_downloads'):
                    direct_url = info['requested_downloads'][0].get('url')
                return jsonify({'url': direct_url})
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
