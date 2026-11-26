"""نشر حلقة ثلاثية الأبعاد على يوتيوب (مرة واحدة فقط لكل عنوان).

    python blender/youtube_publish.py publish/part3.json video.mp4

يحتاج: YT_CLIENT_ID و YT_CLIENT_SECRET و YT_REFRESH_TOKEN (أسرار المستودع).
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def http(url, data=None, headers=None, method=None):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        return urllib.request.urlopen(req, timeout=600)
    except urllib.error.HTTPError as e:
        sys.exit(f"خطأ من يوتيوب ({e.code}): {e.read().decode('utf-8', 'replace')[:500]}")


def token():
    env = {k: os.environ.get(k, "").strip() for k in ("YT_CLIENT_ID", "YT_CLIENT_SECRET", "YT_REFRESH_TOKEN")}
    missing = [k for k, v in env.items() if not v]
    if missing:
        sys.exit(f"لا توجد صلاحية نشر على يوتيوب؛ ينقص: {', '.join(missing)}")
    body = urllib.parse.urlencode({"client_id": env["YT_CLIENT_ID"], "client_secret": env["YT_CLIENT_SECRET"],
                                   "refresh_token": env["YT_REFRESH_TOKEN"], "grant_type": "refresh_token"})
    with http("https://oauth2.googleapis.com/token", body.encode()) as r:
        return json.load(r)["access_token"]


def published_titles(tok):
    auth = {"Authorization": f"Bearer {tok}"}
    api = "https://www.googleapis.com/youtube/v3"
    with http(f"{api}/channels?part=contentDetails&mine=true", headers=auth) as r:
        items = json.load(r).get("items", [])
    if not items:
        return set()
    pl = items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    titles, page = set(), ""
    while True:
        q = urllib.parse.urlencode({"part": "snippet", "playlistId": pl, "maxResults": 50, "pageToken": page})
        with http(f"{api}/playlistItems?{q}", headers=auth) as r:
            data = json.load(r)
        titles |= {i["snippet"]["title"] for i in data.get("items", [])}
        page = data.get("nextPageToken")
        if not page:
            return titles


def main():
    meta = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    video = Path(sys.argv[2])
    if meta.get("approved") is not True:
        sys.exit("لم تتم الموافقة على النشر (approved = true)")
    tok = token()
    if meta["title"] in published_titles(tok):
        print(f"منشورة سابقاً: {meta['title']}")
        return
    body = json.dumps({
        "snippet": {"title": meta["title"], "description": meta["description"], "tags": meta.get("tags", []),
                    "categoryId": meta.get("categoryId", "1"), "defaultLanguage": "ar", "defaultAudioLanguage": "ar"},
        # محتوى موجّه للأطفال: يلزم التصريح بذلك (قانون COPPA وسياسة يوتيوب)
        "status": {"privacyStatus": meta.get("privacy", "public"),
                   "selfDeclaredMadeForKids": meta.get("madeForKids", True)},
    }, ensure_ascii=False).encode()
    size = video.stat().st_size
    with http("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
              body, {"Authorization": f"Bearer {tok}", "Content-Type": "application/json; charset=UTF-8",
                     "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": str(size)}) as r:
        location = r.headers["Location"]
    with video.open("rb") as f, http(location, f.read(), {"Content-Type": "video/mp4"}, "PUT") as r:
        vid = json.load(r)["id"]
    print(f"✓ نُشرت: https://youtu.be/{vid}")
    gh = os.environ.get("GITHUB_STEP_SUMMARY")
    if gh:
        Path(gh).write_text(f"نُشرت: https://youtu.be/{vid}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
