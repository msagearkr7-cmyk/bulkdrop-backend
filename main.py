from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import os

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
    return "BulkDrop Direct URL Resolver Running"

@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    cookies_text = data.get('cookies', '').strip()
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    handle_incoming_cookies(cookies_text)

    # yt-dlp config to extract the highest quality MP4 directly
    ydl_opts = {
        'format': 'best',
        'quiet': True,
        'no_warnings': True,
    }
    
    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
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
    
