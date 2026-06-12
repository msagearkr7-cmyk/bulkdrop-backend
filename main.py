from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import yt_dlp
import os
import uuid

app = Flask(__name__)
CORS(app, origins="*")

def handle_incoming_cookies(cookies_text):
    """Writes incoming platform cookies to a local file for yt-dlp to utilize."""
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

    # Dynamically write the specific platform cookies passed from the frontend
    handle_incoming_cookies(cookies_text)

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
    
    # Apply cookie file if authentication text was provided
    if os.path.exists('cookies.txt') and cookies_text:
        ydl_opts['cookiefile'] = 'cookies.txt'
    
    try:
        if use_proxy:
            # PROXY MODE (TikTok & Facebook): Downloads file to Render disk to bypass blocks
            temp_filename = f"temp_{uuid.uuid4().hex}.mp4"
            ydl_opts['outtmpl'] = temp_filename
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            if os.path.exists(temp_filename):
                with open(temp_filename, 'rb') as f:
                    video_data = f.read()
                
                # Instantly remove from server disk storage to save space
                os.remove(temp_filename)
                
                # Stream binary payload directly to client browser as a Blob download
                return Response(
                    video_data,
                    mimetype='video/mp4',
                    headers={'Content-Disposition': 'attachment; filename="clear_download.mp4"'}
                )
            else:
                return jsonify({'error': 'Failed to stream media file from proxy server'}), 500
        else:
            # EXTRACTION MODE (Instagram): Extracts direct high-speed CDN URL link
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                direct_url = info.get('url')
                if not direct_url and 'formats' in info:
                    direct_url = info['formats'][-1]['url']
                return jsonify({'url': direct_url})
                
    except Exception as e:
        # Fallback clean-up to prevent disk storage build-up if an execution crashes
        if use_proxy and 'temp_filename' in locals() and os.path.exists(temp_filename):
            try:
                os.remove(temp_filename)
            except:
                pass
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)

