#!/usr/bin/env python3
"""Update the paper feed from INSPIRE.

For every entry in watchlist.json, ask INSPIRE for recent papers that either
cite a watched paper or are written by a watched author, and merge them into
<data-dir>/papers.json.  Papers stay in that file until their id shows up in
<data-dir>/read.json (written by the web page when you mark something read).

The run is idempotent: it re-queries a sliding window every time, so there is
no "last run" timestamp to lose and a missed day is caught up automatically.

Standard library only.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

API = "https://inspirehep.net/api/literature"
FIELDS = ",".join([
    "titles.title", "titles.source", "earliest_date", "control_number",
    "arxiv_eprints", "author_count", "authors.full_name",
    "collaborations.value", "abstracts.value", "abstracts.source",
])
PAGE_SIZE = 50
MAX_PAGES = 10
MAX_AUTHORS = 8
PAUSE = 0.5  # seconds between requests; INSPIRE allows 15 requests / 5 s


def inspire_get(params):
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": "paper-feed-updater"})
    last = None
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429:
                time.sleep(float(e.headers.get("Retry-After") or 10))
            elif e.code >= 500:
                time.sleep(5 * (attempt + 1))
            else:
                raise
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last = e
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"INSPIRE request failed after retries: {last}")


def norm_date(s):
    """INSPIRE dates can be YYYY, YYYY-MM or YYYY-MM-DD; pad to a full date."""
    s = (s or "").strip()
    if len(s) == 4:
        return s + "-01-01"
    if len(s) == 7:
        return s + "-01"
    return s[:10]


def display_name(full_name):
    last, _, first = full_name.partition(",")
    return f"{first.strip()} {last.strip()}".strip()


def to_item(meta):
    eprints = meta.get("arxiv_eprints") or []
    arxiv = eprints[0].get("value") if eprints else None
    recid = str(meta["control_number"])
    titles = meta.get("titles") or [{}]
    abstracts = meta.get("abstracts") or []
    abstract = next((a["value"] for a in abstracts if a.get("source") == "arXiv"),
                    abstracts[0]["value"] if abstracts else "")
    authors = [display_name(a["full_name"]) for a in (meta.get("authors") or [])
               if a.get("full_name")]
    return {
        "id": arxiv or f"inspire:{recid}",
        "recid": recid,
        "arxiv": arxiv,
        "title": titles[0].get("title", "(untitled)"),
        "authors": authors[:MAX_AUTHORS],
        "author_count": meta.get("author_count") or len(authors),
        "collaborations": [c["value"] for c in (meta.get("collaborations") or [])
                           if c.get("value")],
        "categories": (eprints[0].get("categories") or []) if eprints else [],
        "abstract": abstract,
        "date": norm_date(meta.get("earliest_date")),
    }


def fetch_watch(query, cutoff):
    """Return (total hits ever, items dated on/after cutoff) for one query."""
    recent, total = [], 0
    for page in range(1, MAX_PAGES + 1):
        data = inspire_get({"q": query, "sort": "mostrecent", "size": PAGE_SIZE,
                            "page": page, "fields": FIELDS})
        time.sleep(PAUSE)
        hits = data["hits"]["hits"]
        total = data["hits"]["total"]
        fresh = [to_item(h["metadata"]) for h in hits
                 if norm_date(h["metadata"].get("earliest_date")) >= cutoff]
        recent += fresh
        # Results are sorted newest first: stop once a page is not all fresh.
        if len(fresh) < len(hits) or len(hits) < PAGE_SIZE:
            break
    return total, recent


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    here = Path(__file__).resolve().parent
    ap.add_argument("--watchlist", default=here / "watchlist.json")
    ap.add_argument("--data-dir", default=here / ".data")
    ap.add_argument("--window-days", type=int, default=45,
                    help="how far back to look for new papers on each run")
    ap.add_argument("--max-age-days", type=int, default=365,
                    help="drop unread papers older than this")
    args = ap.parse_args()

    watch = load_json(args.watchlist, None)
    if watch is None:
        sys.exit(f"watchlist not found: {args.watchlist}")
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=args.window_days)).strftime("%Y-%m-%d")
    oldest = (now - timedelta(days=args.max_age_days)).strftime("%Y-%m-%d")

    store = {it["id"]: it for it in load_json(data_dir / "papers.json", {}).get("items", [])}
    read = set(load_json(data_dir / "read.json", {}).get("read", []))

    queries = (
        [("cites", w, f"refersto:recid:{w['recid']}") for w in watch.get("papers", [])] +
        [("author", w, f"exactauthor:{w['bai']}") for w in watch.get("authors", [])]
    )

    # Reasons are rebuilt for everything inside the window, so that removing a
    # watch also removes the papers that were only there because of it.
    for it in store.values():
        if it["date"] >= cutoff:
            it["why"], it["tags"] = [], []

    warnings, n_new = [], 0
    for kind, w, query in queries:
        label = w["label"]
        total, recent = fetch_watch(query, cutoff)
        print(f"{label}: {len(recent)} recent / {total} total", flush=True)
        if total == 0:
            what = "has no citations yet" if kind == "cites" else \
                "matches no papers - the INSPIRE author identifier is probably wrong or was renamed"
            if kind == "author":
                warnings.append(f"Author watch “{label}” ({w['bai']}) {what}.")
            continue
        for item in recent:
            if item["id"] in read:
                continue
            cur = store.get(item["id"])
            if cur is None:
                cur = store[item["id"]] = {**item, "added": now.isoformat(timespec="seconds"),
                                           "why": [], "tags": []}
                n_new += 1
            else:
                cur.update(item)  # refresh metadata (title fixes, added eprint...)
            reason = {"kind": kind, "label": label}
            if reason not in cur["why"]:
                cur["why"].append(reason)
            cur["tags"] = sorted(set(cur["tags"]) | set(w.get("tags", [])))

    items = [it for it in store.values()
             if it["id"] not in read and it.get("why") and it["date"] >= oldest]
    items.sort(key=lambda it: (it["added"], it["date"]), reverse=True)

    out = {"updated": now.isoformat(timespec="seconds"), "warnings": warnings, "items": items}
    (data_dir / "papers.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\n{n_new} new, {len(items)} unread in feed, {len(warnings)} warnings")
    for wmsg in warnings:
        print("WARNING:", wmsg)


if __name__ == "__main__":
    main()
