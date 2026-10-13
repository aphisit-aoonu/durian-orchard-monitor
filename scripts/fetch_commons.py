"""Download CC-licensed durian tree photos from Wikimedia Commons, with licence and author for credits.

Usage: python -m scripts.fetch_commons   -> commons/img_NN.jpg + commons/selected.json
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "durian-monitor/0.1 (personal research project; github.com/aphisit-aoonu)"}
CATEGORIES = ["Category:Durio zibethinus", "Category:Durian", "Category:Durian trees", "Category:Durio zibethinus (fruits)"]
# photos that show fruit on the tree, picked by eye from the categories above
WANTED = ["Durian Jarian", "Durian Kamarung", "Durian Lai Mas", "Durian Tree.jpg", "Durian in tree.jpg",
          "Durian plantation out of season 1", "Durian plantation out of season 2", "File:Durian tree.jpg",
          "Durian tree in malaysia", "Durians on a tree", "Durio L13 fruit Haw Kee", "Durio L13 tree Haw Kee",
          "Durio zibeth 071230-2985", "Ripe Durian Tree in Samosir Island 0", "Tender fruit's Durian tree"]
OUT = Path("commons")


def get(url: str) -> bytes:
    for attempt in range(5):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429:
                raise
            time.sleep(15 * (attempt + 1))  # Commons rate-limits bursts
    raise RuntimeError(f"gave up on {url}")


def api(**params) -> dict:
    return json.loads(get(API + "?" + urllib.parse.urlencode({**params, "format": "json", "maxlag": 5})))


def main() -> None:
    OUT.mkdir(exist_ok=True)
    titles = set()
    for cat in CATEGORIES:
        res = api(action="query", list="categorymembers", cmtitle=cat, cmtype="file", cmlimit=500)
        titles |= {m["title"] for m in res["query"]["categorymembers"]}
        time.sleep(2)
    picked = sorted(t for t in titles if any(w in t for w in WANTED))
    meta = []
    for i in range(0, len(picked), 15):
        res = api(action="query", titles="|".join(picked[i:i + 15]), prop="imageinfo",
                  iiprop="url|extmetadata", iiurlwidth=1280)
        for page in res["query"]["pages"].values():
            info = page["imageinfo"][0]
            em = info.get("extmetadata", {})
            text = lambda k: re.sub("<[^>]+>", "", em.get(k, {}).get("value", "")).strip()
            meta.append({"title": page["title"], "thumb": info["thumburl"], "page": info["descriptionurl"],
                         "license": text("LicenseShortName"), "artist": text("Artist"),
                         "desc": text("ImageDescription")[:160]})
        time.sleep(3)
    meta.sort(key=lambda m: m["title"])
    for k, m in enumerate(meta):
        m["file"] = str(OUT / f"img_{k:02d}.jpg")
        Path(m["file"]).write_bytes(get(m["thumb"]))
        time.sleep(1.5)
    (OUT / "selected.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(meta)} photos in {OUT}/")


if __name__ == "__main__":
    main()
