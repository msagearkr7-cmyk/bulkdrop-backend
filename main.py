from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app, origins="*")

RAPIDAPI_KEY = os.environ.get('RAPIDAPI_KEY', 'f620e6d328msha3be7257d181088p184d1bjsn81951ba001c6')
RAPIDAPI_HOST = 'instagram-scraper-stable-api.p.rapidapi.com'


@app.route('/')
def home():
    return "BulkDrop IG Backend Running"


def call_api(ig_url, amount, pagination_token):
    return requests.post(
        f'https://{RAPIDAPI_HOST}/get_ig_user_followers_v2.php',
        headers={
            'Content-Type': 'application/x-www-form-urlencoded',
            'x-rapidapi-host': RAPIDAPI_HOST,
            'x-rapidapi-key': RAPIDAPI_KEY,
        },
        data={
            'username_or_url': ig_url,
            'data': 'following',
            'amount': amount,
            'pagination_token': pagination_token,
        },
        timeout=30
    )


# ── DEBUG: see raw API response ──────────────────────────────────────────────
@app.route('/debug', methods=['POST'])
def debug():
    data = request.json or {}
    raw = data.get('username', '').strip()
    if not raw:
        return jsonify({'error': 'username required'}), 400

    username = raw.lstrip('@')
    ig_url = f'https://www.instagram.com/{username}/'

    try:
        resp = call_api(ig_url, 12, '')
        return jsonify({
            'status_code': resp.status_code,
            'raw': resp.text[:5000]          # cap at 5k chars
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── MAIN SCRAPE ───────────────────────────────────────────────────────────────
@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json or {}
    raw = data.get('username', '').strip()

    if not raw:
        return jsonify({'error': 'Username required'}), 400

    if 'instagram.com' in raw:
        ig_url = raw if raw.startswith('http') else 'https://' + raw
        username = ig_url.rstrip('/').split('/')[-1]
    else:
        username = raw.lstrip('@')
        ig_url = f'https://www.instagram.com/{username}/'

    amount = int(data.get('amount', 12))
    pagination_token = data.get('pagination_token', '') or ''

    try:
        response = call_api(ig_url, amount, pagination_token)

        if response.status_code == 429:
            return jsonify({'error': 'RapidAPI rate limit hit — try again shortly'}), 429

        if not response.ok:
            return jsonify({'error': f'RapidAPI error {response.status_code}: {response.text[:300]}'}), 502

        # Parse JSON
        try:
            result = response.json()
        except Exception:
            return jsonify({'error': f'API returned non-JSON: {response.text[:300]}'}), 502

        # ── Unwrap every known response shape ────────────────────────────────
        # Shape 1: { "data": [ ... ] }
        # Shape 2: { "following": [ ... ] }
        # Shape 3: { "users": [ ... ] }
        # Shape 4: { "result": { "following": [...], "next_max_id": "..." } }
        # Shape 5: plain list  [ ... ]

        next_token = ''
        raw_items = []

        if isinstance(result, list):
            raw_items = result

        elif isinstance(result, dict):
            # Try nested result object first
            inner = result.get('result') or result.get('data') or result
            if isinstance(inner, dict):
                raw_items = (
                    inner.get('following') or
                    inner.get('users') or
                    inner.get('edge_follow', {}).get('edges') or
                    []
                )
                next_token = (
                    inner.get('pagination_token') or
                    inner.get('next_max_id') or
                    inner.get('next_cursor') or
                    ''
                )
            elif isinstance(inner, list):
                raw_items = inner

            # Also check top-level lists
            if not raw_items:
                raw_items = (
                    result.get('following') or
                    result.get('users') or
                    result.get('data') or
                    []
                )
                next_token = next_token or (
                    result.get('pagination_token') or
                    result.get('next_max_id') or
                    result.get('next_cursor') or
                    ''
                )

        # Unwrap GraphQL edge nodes if needed
        if raw_items and isinstance(raw_items[0], dict) and 'node' in raw_items[0]:
            raw_items = [e['node'] for e in raw_items]

        # Normalise each user object
        items = []
        for item in raw_items:
            if not isinstance(item, dict):
                continue
            items.append({
                'username':    item.get('username') or item.get('user') or '',
                'full_name':   item.get('full_name') or item.get('name') or '',
                'profile_url': f"https://www.instagram.com/{item.get('username', '')}/",
                'is_private':  bool(item.get('is_private', False)),
                'is_verified': bool(item.get('is_verified', False)),
                'followers':   item.get('follower_count') or item.get('followers') or 0,
                'profile_pic': item.get('profile_pic_url') or item.get('profile_pic') or '',
            })

        # If still empty, return raw result so frontend can show it
        if not items:
            return jsonify({
                'username': username,
                'total': 0,
                'following': [],
                'pagination_token': '',
                'has_more': False,
                '_raw_keys': list(result.keys()) if isinstance(result, dict) else str(type(result)),
            })

        return jsonify({
            'username':         username,
            'total':            len(items),
            'following':        items,
            'pagination_token': next_token,
            'has_more':         bool(next_token),
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out — try again'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot reach RapidAPI — check network'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
