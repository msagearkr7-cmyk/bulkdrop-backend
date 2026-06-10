from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "BulkDrop IG Backend Running"

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    username = data.get('username', '').strip().lstrip('@')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    try:
        L = instaloader.Instaloader()

        # Optional: login for better reliability
        # IG_USER = os.environ.get('IG_USER')
        # IG_PASS = os.environ.get('IG_PASS')
        # if IG_USER and IG_PASS:
        #     L.login(IG_USER, IG_PASS)

        profile = instaloader.Profile.from_username(L.context, username)

        video_urls = []
        count = 0

        for post in profile.get_posts():
            if count >= 50:  # limit to 50 videos max
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
