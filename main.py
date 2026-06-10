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


@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    raw = data.get('username', '').strip()

    if not raw:
        return jsonify({'error': 'Username required'}), 400

    # Accept full URL or plain username
    if 'instagram.com' in raw:
        ig_url = raw if raw.startswith('http') else 'https://' + raw
        username = ig_url.rstrip('/').split('/')[-1]
    else:
        username = raw.lstrip('@')
        ig_url = f'https://www.instagram.com/{username}/'

    amount = int(data.get('amount', 50))
    pagination_token = data.get('pagination_token', '')

    try:
        response = requests.post(
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
            }
        )

        if response.status_code == 429:
            return jsonify({'error': 'RapidAPI rate limit hit — try again shortly'}), 429

        if not response.ok:
            return jsonify({'error': f'RapidAPI error {response.status_code}: {response.text[:200]}'}), 502

        result = response.json()

        # Normalise the response into a consistent shape
        # The API returns data in result['data'] or similar — handle both shapes
        items = []
        next_token = ''

        if isinstance(result, dict):
            # Common response shapes from this API
            raw_items = (
                result.get('data') or
                result.get('following') or
                result.get('users') or
                result.get('result') or
                []
            )
            next_token = (
                result.get('pagination_token') or
                result.get('next_max_id') or
                result.get('next_cursor') or
                ''
            )
        elif isinstance(result, list):
            raw_items = result
        else:
            raw_items = []

        for item in raw_items:
            if isinstance(item, dict):
                items.append({
                    'username': item.get('username') or item.get('user') or '',
                    'full_name': item.get('full_name') or item.get('name') or '',
                    'profile_url': f"https://www.instagram.com/{item.get('username', '')}/" if item.get('username') else '',
                    'is_private': item.get('is_private', False),
                    'is_verified': item.get('is_verified', False),
                    'followers': item.get('follower_count') or item.get('followers') or 0,
                    'profile_pic': item.get('profile_pic_url') or item.get('profile_pic') or '',
                })

        return jsonify({
            'username': username,
            'total': len(items),
            'following': items,
            'pagination_token': next_token,
            'has_more': bool(next_token),
        })

    except requests.exceptions.Timeout:
        return jsonify({'error': 'Request timed out — try again'}), 504
    except requests.exceptions.ConnectionError:
        return jsonify({'error': 'Cannot reach RapidAPI — check network'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
