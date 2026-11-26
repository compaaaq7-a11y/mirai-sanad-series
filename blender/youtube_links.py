"""ربط مقاطع السلسلة ببعضها: يضيف أسطراً إلى أوصافها (دون حذف شيء) ويبني قائمة تشغيل مرتّبة.

    python blender/youtube_links.py publish/series-links.json
لا يكرر سطراً موجوداً، ولا ينشئ قائمة تشغيل جديدة إن وُجدت بالاسم نفسه، ولا يضيف مقطعاً موجوداً فيها.
"""

import json
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_publish import http, token  # noqa: E402

API = "https://www.googleapis.com/youtube/v3"


def main():
    cfg = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    tok = token()
    auth = {"Authorization": f"Bearer {tok}"}
    jh = {**auth, "Content-Type": "application/json; charset=UTF-8"}
    for vid, lines in cfg.get("append", {}).items():
        with http(f"{API}/videos?part=snippet&id={vid}", headers=auth) as r:
            items = json.load(r).get("items", [])
        if not items:
            print(f"- {vid}: غير موجود")
            continue
        sn = items[0]["snippet"]
        desc = sn.get("description", "")
        new = [ln for ln in lines if ln not in desc]
        if not new:
            print(f"- {vid}: لا تغيير")
            continue
        sn["description"] = desc.rstrip() + "\n\n" + "\n".join(new)
        body = {"id": vid, "snippet": {k: sn[k] for k in ("title", "description", "categoryId", "tags",
                                                            "defaultLanguage", "defaultAudioLanguage") if k in sn}}
        with http(f"{API}/videos?part=snippet", json.dumps(body, ensure_ascii=False).encode(), jh, "PUT"):
            pass
        print(f"✓ {vid}: أُضيف {len(new)} سطر")
    pl = cfg.get("playlist")
    if pl:
        q = urllib.parse.urlencode({"part": "snippet", "mine": "true", "maxResults": 50})
        with http(f"{API}/playlists?{q}", headers=auth) as r:
            found = [p for p in json.load(r).get("items", []) if p["snippet"]["title"] == pl["title"]]
        if found:
            pid = found[0]["id"]
        else:
            body = {"snippet": {"title": pl["title"], "description": pl.get("description", ""), "defaultLanguage": "ar"},
                    "status": {"privacyStatus": "public"}}
            with http(f"{API}/playlists?part=snippet,status", json.dumps(body, ensure_ascii=False).encode(), jh) as r:
                pid = json.load(r)["id"]
            print(f"✓ قائمة تشغيل جديدة: https://www.youtube.com/playlist?list={pid}")
        have, page = set(), ""
        while True:
            q = urllib.parse.urlencode({"part": "contentDetails", "playlistId": pid, "maxResults": 50, "pageToken": page})
            with http(f"{API}/playlistItems?{q}", headers=auth) as r:
                data = json.load(r)
            have |= {i["contentDetails"]["videoId"] for i in data.get("items", [])}
            page = data.get("nextPageToken")
            if not page:
                break
        for vid in pl["videos"]:
            if vid in have:
                continue
            body = {"snippet": {"playlistId": pid, "resourceId": {"kind": "youtube#video", "videoId": vid}}}
            with http(f"{API}/playlistItems?part=snippet", json.dumps(body).encode(), jh):
                pass
            print(f"✓ أُضيف إلى القائمة: {vid}")
        print(f"القائمة: https://www.youtube.com/playlist?list={pid}")


if __name__ == "__main__":
    main()
