from flask import Flask, request, jsonify, session
from flask_cors import CORS
import instaloader
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'bulkdrop-secret-2024')
CORS(app, supports_credentials=True, origins="*")

@app.route('/')
def home():
    return "BulkDrop IG Backend Running"

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()

    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400

    try:
        L = instaloader.Instaloader()
        L.login(username, password)
        # Store credentials in session
        session['ig_user'] = username
        session['ig_pass'] = password
        return jsonify({'success': True, 'username': username})
    except instaloader.exceptions.BadCredentialsException:
        return jsonify({'error': 'Wrong username or password'}), 401
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        return jsonify({'error': '2FA is enabled on this account — disable it first'}), 403
    except instaloader.exceptions.ConnectionException as e:
        return jsonify({'error': f'Connection error: {str(e)}'}), 503
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    username = data.get('username', '').strip().lstrip('@')
    ig_user = data.get('ig_user', '').strip()
    ig_pass = data.get('ig_pass', '').strip()

    if not username:
        return jsonify({'error': 'Username required'}), 400

    try:
        L = instaloader.Instaloader()

        # Login with credentials passed from frontend
        if ig_user and ig_pass:
            try:
                L.login(ig_user, ig_pass)
            except Exception:
                pass  # Continue even if re-login fails (already verified at /login)

        profile = instaloader.Profile.from_username(L.context, username)

        video_urls = []
        count = 0

        for post in profile.get_posts():
            if count >= 50:
                break
            if post.is_video:
                video_urls.append({
                    'url': post.video_url,
                    'shortcode': post.shortcode,
                    'timestamp': str(post.date_utc)
                })
                count += 1

        return jsonify({
            'username': username,
            'total': len(video_urls),
            'videos': video_urls
        })

    except instaloader.exceptions.ProfileNotExistsException:
        return jsonify({'error': f'Profile @{username} not found'}), 404
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return jsonify({'error': f'@{username} is a private account'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
    
