from flask import Flask, render_template_string, request
import yt_dlp
import concurrent.futures

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Song Finder</title>
</head>
<body>
    <h2>Song Finder</h2>
    <form method="post">
        <label>Enter song titles (one per line):</label><br>
        <textarea name="input_text" rows="4" cols="50">{{ input_text or '' }}</textarea><br>
        <input type="submit" value="Find Songs">
    </form>
    {% if results %}
        <h3>Results (songs longer than 3 minutes):</h3>
        <ul>
        {% for search_title, yt_title, link, duration in results %}
            <li>
                <b>Searched:</b> "{{ search_title }}"<br>
                {% if link %}
                    <b>Found:</b> "{{ yt_title }}"<br>
                    <a href="{{ link }}" target="_blank">{{ link }}</a> ({{ duration }})
                {% else %}
                    No suitable song found
                {% endif %}
            </li>
            <br>
        {% endfor %}
        </ul>
    {% endif %}
</body>
</html>
"""

def format_duration(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02}:{s:02}"
    else:
        return f"{m}:{s:02}"

def get_youtube_song_link(query):
    ydl_opts = {
        'quiet': True,
        'skip_download': True,
        'extract_flat': False,
        'default_search': 'ytsearch5',
        'forcejson': True,
        'socket_timeout': 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            entries = info['entries'] if 'entries' in info else [info]
            for entry in entries:
                if entry and entry.get('duration') and entry['duration'] >= 180:
                    return (
                        entry.get('title', 'Unknown Title'),
                        f"https://www.youtube.com/watch?v={entry['id']}",
                        format_duration(entry['duration'])
                    )
    except Exception as e:
        print(f"Error searching for {query}: {e}")
    return (None, None, None)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    input_text = ''
    if request.method == 'POST':
        input_text = request.form['input_text']
        potential_titles = [line.strip() for line in input_text.split('\n') if line.strip()]
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            future_to_title = {executor.submit(get_youtube_song_link, title): title for title in potential_titles}
            temp_results = {}
            for future in concurrent.futures.as_completed(future_to_title):
                search_title = future_to_title[future]
                try:
                    yt_title, link, duration = future.result(timeout=15)
                except Exception as exc:
                    print(f"{search_title} generated an exception: {exc}")
                    yt_title, link, duration = None, None, None
                temp_results[search_title] = (search_title, yt_title, link, duration)
            results = [temp_results[title] for title in potential_titles]
    return render_template_string(HTML_TEMPLATE, results=results, input_text=input_text)


# ...existing code...
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
# ...existing code...
