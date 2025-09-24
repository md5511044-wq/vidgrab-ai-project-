from flask import Flask, request, jsonify
from flask_cors import CORS
import yt_dlp
import logging
import os # Naya import

# Logging setup
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
CORS(app)

# YEH NAYA CODE HAI - Render ke health check ke liye
@app.route('/')
def health_check():
    return jsonify({'status': 'ok', 'message': 'Backend is running!'})

@app.route('/api/video-info', methods=['POST'])
def get_video_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    logging.info(f"Received URL: {url}")

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            sanitized_info = ydl.sanitize_info(info)

            title = sanitized_info.get('title', 'No Title')
            thumbnail = sanitized_info.get('thumbnail', '')
            
            formats_list = []
            
            if 'formats' in sanitized_info:
                for f in sanitized_info['formats']:
                    if f.get('url') and (f.get('vcodec') != 'none' and f.get('acodec') != 'none' or f.get('vcodec') == 'none'):
                        quality = f.get('format_note') or f.get('resolution')
                        if f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                            quality = 'Audio Only'

                        if not quality or not isinstance(quality, str):
                            height = f.get('height')
                            if height:
                                quality = f"{height}p"
                            else:
                                continue 
                        
                        if not any(d['quality'] == quality for d in formats_list):
                             formats_list.append({
                                'quality': quality,
                                'url': f.get('url'),
                                'ext': f.get('ext')
                            })

            if not formats_list and sanitized_info.get('url'):
                 formats_list.append({
                    'quality': f"{sanitized_info.get('height')}p" if sanitized_info.get('height') else 'Standard',
                    'url': sanitized_info.get('url'),
                    'ext': sanitized_info.get('ext')
                 })

            if not formats_list:
                 return jsonify({'error': 'No downloadable formats found'}), 500

            response_data = {
                'title': title,
                'thumbnail': thumbnail,
                'formats': formats_list
            }
            
            logging.info(f"Successfully processed URL: {url}")
            return jsonify(response_data)

    except yt_dlp.utils.DownloadError as e:
        logging.error(f"DownloadError for URL {url}: {e}")
        return jsonify({'error': 'Could not process video. Check the URL or try again.'}), 500
    except Exception as e:
        logging.error(f"Generic error for URL {url}: {e}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

# Yeh hissa Render par nahi chalta, sirf local machine ke liye hai
if __name__ == '__main__':
    # Render port dega, local par 5000 istemaal hoga
    port = int(os.environ.get('PORT', 5000)) 
    app.run(host='0.0.0.0', port=port)
