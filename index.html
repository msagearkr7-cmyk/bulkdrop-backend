from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import requests

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
    use_proxy = data.get('proxy', False)  # The frontend will set this to True for TikTok
    
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
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 1. Extract the raw info dictionary
            info = ydl.extract_info(url, download=False)
            
            direct_url = info.get('url')
            if not direct_url and info.get('requested_downloads'):
                direct_url = info['requested_downloads'][0].get('url')

            if use_proxy:
                # 2. PROXY MODE: Grab the exact headers yt-dlp used to trick TikTok
                headers = info.get('http_headers', {})
                
                # 3. Stream the video directly from TikTok to Render
                req = requests.get(direct_url, headers=headers, stream=True, timeout=15)
                
                # 4. Pipe the raw video stream straight back to the user's phone
                return Response(
                    req.iter_content(chunk_size=1024 * 1024),
                    content_type=req.headers.get('Content-Type', 'video/mp4'),
                    headers={'Content-Disposition': 'attachment; filename="bulkdrop_video.mp4"'}
                )
            else:
                # NORMAL MODE: Just return the URL (for IG/YouTube)
                return jsonify({'url': direct_url})
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
