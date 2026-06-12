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
        # If no cookies passed but an old file exists, clear it to prevent auth confusion
        try:
            os.remove('cookies.txt')
        except:
            pass

@app.route('/')
def home():
    return "yt-dlp BulkDrop Backend (Dynamic Cookies) Running"

@app.route('/reels', methods=['POST'])
def reels():
    data = request.json or {}
    raw = data.get('username', '').strip()
    cookies_text = data.get('cookies', '').strip()
    
    if not raw:
        return jsonify({'error': 'username required'}), 400

    # Handle dynamic cookie text assignment
    handle_incoming_cookies(cookies_text)

    username = raw.replace('@', '').strip()
    if 'instagram.com' in username:
        username = username.rstrip('/').split('/')[-1]

    ig_url = f'https://www.instagram.com/{username}/reels/'
    amount = int(data.get('amount', 12))

    ydl_opts = {
        'extract_flat': True, 
        'playlist_items': f'1-{amount}',
        'quiet': True,
        'no_warnings': True,
        'ignoreerrors': True,
    }

    if os.path.exists('cookies.txt'):
        ydl_opts['cookiefile'] = 'cookies.txt'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(ig_url, download=False)
            
            if not info or 'entries' not in info:
                return jsonify({'error': 'Instagram blocked the request. Please update your cookies in the application settings.'}), 403

            items = []
            for entry in info['entries']:
                if not entry: continue
                
                thumb = ''
                if entry.get('thumbnails'):
                    thumb = entry['thumbnails'][-1].get('url', '')
                
                items.append({
                    'id': entry.get('id', ''),
                    'url': entry.get('url', ''),
                    'thumbnail': thumb,
                    'caption': entry.get('title', 'No caption'),
                    'play_count': entry.get('view_count', 0),
                })

            return jsonify({
                'username': username,
                'total': len(items),
                'reels': items,
                'has_more': False
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    url = data.get('url')
    cookies_text = data.get('cookies', '').strip()
    
    if not url:
        return jsonify({'error': 'URL required'}), 400

    handle_incoming_cookies(cookies_text)

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
    
