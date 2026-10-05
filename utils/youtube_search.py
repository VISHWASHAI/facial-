from youtubesearchpython import VideosSearch

FALLBACK_ID = "dQw4w9WgXcQ"


def search_youtube(query):
    videos_search = VideosSearch(query, limit=1)
    result = videos_search.result()
    if result['result']:
        video_id = result['result'][0]['id']
        return f"https://www.youtube.com/embed/{video_id}?autoplay=1"
    return f"https://www.youtube.com/embed/{FALLBACK_ID}"


def search_youtube_videos(query, limit=8):
    """Return [{'id', 'title'}] for the top results of a query."""
    try:
        results = VideosSearch(query, limit=limit).result()['result']
    except Exception:
        results = []
    return [{"id": r['id'], "title": r['title']} for r in results]
