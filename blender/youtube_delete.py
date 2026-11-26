"""حذف مقاطع محددة من القناة بطلب صريح من صاحبها (حذف نهائي).

    python blender/youtube_delete.py publish/delete.json
لكل مقطع: المعرّف والعنوان المتوقع؛ لا يُحذف إن لم يطابق العنوان تماماً.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from youtube_publish import http, token  # noqa: E402

API = "https://www.googleapis.com/youtube/v3"


def main():
    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))["delete"]
    auth = {"Authorization": f"Bearer {token()}"}
    for it in items:
        with http(f"{API}/videos?part=snippet&id={it['id']}", headers=auth) as r:
            found = json.load(r).get("items", [])
        if not found:
            print(f"- {it['id']}: غير موجود (ربما حُذف سابقاً)")
            continue
        title = found[0]["snippet"]["title"]
        if title != it["title"]:
            print(f"! {it['id']}: العنوان لا يطابق («{title}»)، لم يُحذف")
            continue
        with http(f"{API}/videos?id={it['id']}", headers=auth, method="DELETE"):
            pass
        print(f"✓ حُذف: {it['id']} «{title}»")


if __name__ == "__main__":
    main()
