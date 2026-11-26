"""قراءة إحصاءات كل مقاطع القناة (قراءة فقط): المشاهدات والإعجابات والتعليقات وإعداد «مخصص للأطفال».

    python blender/youtube_stats.py out.json
يحتاج: YT_CLIENT_ID و YT_CLIENT_SECRET و YT_REFRESH_TOKEN.
"""

import json
import os
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_publish import http, token  # noqa: E402

API = "https://www.googleapis.com/youtube/v3"


def main():
    tok = token()
    auth = {"Authorization": f"Bearer {tok}"}
    with http(f"{API}/channels?part=contentDetails,statistics,snippet&mine=true", headers=auth) as r:
        ch = json.load(r)["items"][0]
    uploads = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    ids, page = [], ""
    while True:
        q = urllib.parse.urlencode({"part": "contentDetails", "playlistId": uploads, "maxResults": 50, "pageToken": page})
        with http(f"{API}/playlistItems?{q}", headers=auth) as r:
            data = json.load(r)
        ids += [i["contentDetails"]["videoId"] for i in data.get("items", [])]
        page = data.get("nextPageToken")
        if not page:
            break
    rows = []
    for k in range(0, len(ids), 50):
        q = urllib.parse.urlencode({"part": "snippet,statistics,status,contentDetails", "id": ",".join(ids[k:k + 50])})
        with http(f"{API}/videos?{q}", headers=auth) as r:
            for v in json.load(r).get("items", []):
                st, s = v.get("statistics", {}), v.get("status", {})
                rows.append({
                    "id": v["id"], "title": v["snippet"]["title"], "published": v["snippet"]["publishedAt"],
                    "duration": v["contentDetails"].get("duration"),
                    "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)) if "commentCount" in st else None,
                    "madeForKids": s.get("madeForKids"), "selfDeclaredMadeForKids": s.get("selfDeclaredMadeForKids"),
                    "privacy": s.get("privacyStatus"),
                    "has_captions": v["contentDetails"].get("caption"),
                })
    rows.sort(key=lambda r: r["published"])
    out = {"channel": {"title": ch["snippet"]["title"], **{k: ch["statistics"].get(k) for k in
                                                         ("subscriberCount", "viewCount", "videoCount")}},
           "videos": rows}
    Path(sys.argv[1]).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    lines = ["| نُشر | العنوان | مشاهدات | إعجابات | للأطفال |", "|---|---|---|---|---|"]
    lines += [f"| {r['published'][:16]} | {r['title']} | {r['views']} | {r['likes']} | {r['madeForKids']} |" for r in rows]
    print("\n".join(lines))
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        Path(os.environ["GITHUB_STEP_SUMMARY"]).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
