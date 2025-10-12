from youtubesearchpython import VideosSearch

def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    if result['result']:
        video_id = result['result'][0]['id']
        return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    return "https://www.youtube.com/embed/dQw4w9WgXcQ"
