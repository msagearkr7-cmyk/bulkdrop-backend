from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app, origins="*")

def handle_incoming_cookies(cookies_text):
    """Writes incoming cookies text to a local file for yt-dlp to use."""
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

    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
        }
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        if use_proxy:
            # TIKTOK MODE: Force yt-dlp to physically download the file to Render's disk
            temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
            ydl_opts['outtmpl'] = temp_filename
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Read the downloaded video directly into memory
            if os.path.exists(temp_filename):
                with open(temp_filename, 'rb') as f:
                    video_data = f.read()
                
                # Delete the file from the Render server to prevent storage filling up
                os.remove(temp_filename)
                
                # Stream the real video file securely to the phone
                return Response(
                    video_data,
                    mimetype='video/mp4',
                    headers={'Content-Disposition': 'attachment; filename="tiktok_video.mp4"'}
                )
            else:
                return jsonify({'error': 'Failed to save TikTok file to server'}), 500
                
        else:
            # IG & YOUTUBE MODE: Just extract the direct CDN URL like normal
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                direct_url = info.get('url')
                if not direct_url and info.get('requested_downloads'):
                    direct_url = info['requested_downloads'][0].get('url')
                    
                return jsonify({'url': direct_url})
                
    except Exception as e:
        # Emergency clean-up if the download crashes halfway through
        if use_proxy and 'temp_filename' in locals() and os.path.exists(temp_filename):
            os.remove(temp_filename)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
