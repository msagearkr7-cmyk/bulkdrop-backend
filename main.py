from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, origins="*")

# Updated with your new API key
RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', '543d5079e1msh7782c641c938117p185970jsnec52bad3352b')
RAPIDAPI_HOST = 'instagram-scraper-stable-api.p.rapidapi.com'

HEADERS = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'x-rapidapi-host': RAPIDAPI_HOST,
    'x-rapidapi-key': RAPIDAPI_KEY,
}


@app.route('/')
def home():
    return "BulkDrop IG Backend Running"


def resolve_username(raw):
    """Return (username, ig_url) from raw input."""
    raw = raw.strip()
    if 'instagram.com' in raw:
        ig_url = raw if raw.startswith('http') else 'https://' + raw
        username = ig_url.rstrip('/').split('/')[-1]
    else:
        username = raw.lstrip('@')
        ig_url = f'https://www.instagram.com/{username}/'
    return username, ig_url


# ── PROFILE INFO ──────────────────────────────────────────────────────────────
@app.route('/profile', methods=['POST'])
def profile():
    data = request.json or {}
    raw = data.get('username', '').strip()
    if not raw:
        return jsonify({'error': 'username required'}), 400

    username, ig_url = resolve_username(raw)

    try:
        resp = requests.post(
            f'https://{RAPIDAPI_HOST}/ig_get_fb_profile_v3.php',
            headers=HEADERS,
            data={'username_or_url': username},
            timeout=30
        )
        if not resp.ok:
            return jsonify({'error': f'API error {resp.status_code}: {resp.text[:300]}'}), 502
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── REELS ─────────────────────────────────────────────────────────────────────
@app.route('/reels', methods=['POST'])
def reels():
    data = request.json or {}
    raw = data.get('username', '').strip()
    if not raw:
        return jsonify({'error': 'username required'}), 400

    username, ig_url = resolve_username(raw)
    amount = int(data.get('amount', 20))
    pagination_token = data.get('pagination_token', '') or ''

    try:
        resp = requests.post(
            f'https://{RAPIDAPI_HOST}/get_ig_user_reels.php',
            headers=HEADERS,
            data={
                'username_or_url': username,
                'amount': amount,
                'pagination_token': pagination_token,
            },
            timeout=30
        )

        if resp.status_code == 429:
            return jsonify({'error': 'Rate limit hit — try again shortly'}), 429
        if not resp.ok:
            return jsonify({'error': f'API error {resp.status_code}: {resp.text[:300]}'}), 502

        try:
            result = resp.json()
        except Exception:
            return jsonify({'error': f'Non-JSON response: {resp.text[:300]}'}), 502

        # Unwrap response — reels API returns various shapes
        next_token = ''
        raw_items = []

        if isinstance(result, list):
            raw_items = result
        elif isinstance(result, dict):
            inner = result.get('result') or result.get('data') or result
            if isinstance(inner, list):
                raw_items = inner
            elif isinstance(inner, dict):
                raw_items = inner.get('reels') or inner.get('items') or inner.get('data') or []
                next_token = (
                    inner.get('pagination_token') or
                    inner.get('next_max_id') or
                    inner.get('next_cursor') or ''
                )
            if not raw_items:
                raw_items = result.get('reels') or result.get('items') or result.get('data') or []
                next_token = next_token or (
                    result.get('pagination_token') or
                    result.get('next_max_id') or
                    result.get('next_cursor') or ''
                )

        # Normalise each reel
        items = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            
            # Unwrap standard Instagram GraphQL structures
            media = item.get('media') or item.get('node', {}).get('media') or item
            
            # Attempt to build public share URL for Cobalt
            code = media.get('code') or media.get('shortcode')
            public_url = f"https://www.instagram.com/reel/{code}/" if code else (media.get('video_url') or '')

            # Extract thumbnail
            thumb = media.get('thumbnail_url') or media.get('display_url') or media.get('image_url')
            if not thumb:
                candidates = media.get('candidates', [])
                if isinstance(candidates, list) and len(candidates) > 0:
                    thumb = candidates[0].get('url', '')

            # Extract caption safely
            caption_obj = media.get('caption')
            caption_text = ''
            if isinstance(caption_obj, dict):
                caption_text = caption_obj.get('text', '')
            elif isinstance(caption_obj, str):
                caption_text = caption_obj

            items.append({
                'id':          media.get('id') or media.get('pk') or '',
                'url':         public_url,
                'thumbnail':   thumb or '',
                'caption':     caption_text or 'No caption',
                'play_count':  media.get('play_count') or media.get('view_count') or 0,
                'like_count':  media.get('like_count') or 0,
                'taken_at':    media.get('taken_at') or media.get('timestamp') or '',
            })

        if not items:
            return jsonify({
                'username': username,
                'total': 0,
                'reels': [],
                'pagination_token': '',
                'has_more': False,
                '_raw_keys': list(result.keys()) if isinstance(result, dict) else str(type(result)),
            })

        return jsonify({
            'username':         username,
            'total':            len(items),
            'reels':            items,
            'pagination_token': next_token,
            'has_more':         bool(next_token),
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot reach RapidAPI'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── COBALT DOWNLOADER ─────────────────────────────────────────────────────────
@app.route('/download', methods=['POST'])
def download():
    data = request.json or {}
    ig_url = data.get('url')
    
    if not ig_url:
        return jsonify({'error': 'Instagram URL required'}), 400

    try:
        # Route through the official Cobalt API via backend to bypass CORS
        resp = requests.post(
            'https://api.cobalt.tools/api/json',
            headers={
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            json={
                'url': ig_url,
                'vCodec': 'h264',
                'vQuality': '1080',
                'aFormat': 'best',
                'isAudioOnly': False
            },
            timeout=30
        )
        
        if not resp.ok:
            return jsonify({'error': f'Cobalt API error: {resp.status_code}'}), 502
            
        return jsonify(resp.json())
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── POSTS (bonus) ─────────────────────────────────────────────────────────────
@app.route('/posts', methods=['POST'])
def posts():
    data = request.json or {}
    raw = data.get('username', '').strip()
    if not raw:
        return jsonify({'error': 'username required'}), 400

    username, ig_url = resolve_username(raw)
    amount = int(data.get('amount', 12))
    pagination_token = data.get('pagination_token', '') or ''

    try:
        resp = requests.post(
            f'https://{RAPIDAPI_HOST}/get_ig_user_posts.php',
            headers=HEADERS,
            data={
                'username_or_url': ig_url,
                'amount': amount,
                'pagination_token': pagination_token,
            },
            timeout=30
        )
        if not resp.ok:
            return jsonify({'error': f'API error {resp.status_code}: {resp.text[:300]}'}), 502
        return jsonify(resp.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── DEBUG ─────────────────────────────────────────────────────────────────────
@app.route('/debug', methods=['POST'])
def debug():
    data = request.json or {}
    raw = data.get('username', '').strip()
    endpoint = data.get('endpoint', 'get_ig_user_reels.php')
    if not raw:
        return jsonify({'error': 'username required'}), 400

    username, _ = resolve_username(raw)

    try:
        resp = requests.post(
            f'https://{RAPIDAPI_HOST}/{endpoint}',
            headers=HEADERS,
            data={'username_or_url': username, 'amount': 5},
            timeout=30
        )
        return jsonify({'status_code': resp.status_code, 'raw': resp.text[:5000]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
