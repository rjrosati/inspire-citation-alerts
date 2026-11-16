#!/usr/bin/env python3
"""Triage recent arXiv submissions with a cheap LLM and add its picks to the feed.

Fetches everything submitted to the configured arXiv categories since the last
triage (default: the last 7 days), drops what the author/citation feed already
caught or what you have already read, and asks `claude -p` (Sonnet by default)
to score each remaining paper using the instructions in triage_prompt.md.
Papers scoring at or above --min-score are written to picks.json on the `data`
branch, where the web page shows them next to the INSPIRE hits.

Run this on a machine where the `claude` CLI is logged in:

    python3 triage.py              # triage since last run, publish picks
    python3 triage.py --days 3     # only the last 3 days
    python3 triage.py --dry-run    # score, print, but don't write or push

Standard library only (plus git and the claude CLI).
"""
import argparse
import json
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / ".data"
ARXIV_API = "https://export.arxiv.org/api/query"
DEFAULT_CATEGORIES = ["hep-th", "gr-qc", "astro-ph.CO", "astro-ph.IM"]
ATOM = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
PAGE = 200
MAX_AUTHORS = 8
OVERLAP_DAYS = 5
COST = [0.0]  # running total of what the claude CLI reports, in USD

SCHEMA = {
    "type": "object",
    "properties": {"results": {"type": "array", "items": {
        "type": "object",
        "properties": {
            "id": {"type": "string"},
            "score": {"type": "integer", "enum": [0, 1, 2, 3]},
            "tags": {"type": "array", "items": {"type": "string"}},
            "reason": {"type": "string"},
        },
        "required": ["id", "score", "tags", "reason"],
    }}},
    "required": ["results"],
}


def run(*cmd, cwd=None, check=True):
    return subprocess.run(cmd, cwd=cwd, check=check, text=True,
                          capture_output=True).stdout.strip()


def ensure_data_checkout():
    """Make sure .data/ is an up-to-date git worktree of the `data` branch."""
    if not (DATA / ".git").exists():
        run("git", "fetch", "origin", "data", cwd=HERE)
        run("git", "worktree", "add", "-B", "data", str(DATA), "origin/data", cwd=HERE)
    run("git", "pull", "--rebase", "--autostash", "origin", "data", cwd=DATA)


def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def fetch_arxiv(categories, start, end):
    """All papers first submitted in [start, end] to any of the categories."""
    fmt = "%Y%m%d%H%M"
    query = "({}) AND submittedDate:[{} TO {}]".format(
        " OR ".join(f"cat:{c}" for c in categories), start.strftime(fmt), end.strftime(fmt))
    papers, offset = [], 0
    while True:
        url = ARXIV_API + "?" + urllib.parse.urlencode({
            "search_query": query, "sortBy": "submittedDate", "sortOrder": "descending",
            "start": offset, "max_results": PAGE})
        entries, total = None, 0
        for attempt in range(6):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "paper-feed-triage"})
                with urllib.request.urlopen(req, timeout=90) as r:
                    root = ET.fromstring(r.read())
                total = int(root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults") or 0)
                entries = root.findall("a:entry", ATOM)
                # arXiv sometimes returns an empty page by mistake; retry those.
                if entries or offset >= total:
                    break
            except (urllib.error.URLError, TimeoutError, ET.ParseError) as e:
                print(f"  arXiv request failed ({e}), retrying", file=sys.stderr)
            time.sleep(5 * (attempt + 1))
        if entries is None or (not entries and offset < total):
            sys.exit("arXiv API kept failing; try again later.")
        for e in entries:
            m = re.search(r"abs/(.+?)(v\d+)?$", e.findtext("a:id", "", ATOM))
            if not m:
                continue
            authors = [a.findtext("a:name", "", ATOM) for a in e.findall("a:author", ATOM)]
            papers.append({
                "id": m.group(1),
                "arxiv": m.group(1),
                "recid": None,
                "title": " ".join(e.findtext("a:title", "", ATOM).split()),
                "authors": authors[:MAX_AUTHORS],
                "author_count": len(authors),
                "collaborations": [],
                "categories": [c.get("term") for c in e.findall("a:category", ATOM)],
                "abstract": " ".join(e.findtext("a:summary", "", ATOM).split()),
                "date": e.findtext("a:published", "", ATOM)[:10],
            })
        offset += PAGE
        if offset >= total:
            return papers
        time.sleep(3)  # arXiv asks for 3 s between API calls


def classify_batch(batch, prompt_template, tags, model):
    listing = "\n\n".join(json.dumps({
        "id": p["id"], "title": p["title"],
        "authors": ", ".join(p["authors"][:5]) + (" et al." if p["author_count"] > 5 else ""),
        "categories": p["categories"], "abstract": p["abstract"],
    }, ensure_ascii=False) for p in batch)
    prompt = (prompt_template
              .replace("{{TAGS}}", "\n".join(f"- {t}" for t in tags))
              .replace("{{PAPERS}}", listing))
    want = {p["id"] for p in batch}
    for attempt in range(3):
        # Run from an empty directory with no tools: this is pure classification.
        with tempfile.TemporaryDirectory() as tmp:
            proc = subprocess.run(
                ["claude", "-p", "--model", model, "--tools", "", "--strict-mcp-config",
                 "--output-format", "json", "--json-schema", json.dumps(SCHEMA)],
                input=prompt, text=True, capture_output=True, cwd=tmp)
        try:
            reply = json.loads(proc.stdout)
            COST[0] += reply.get("total_cost_usd") or 0
            results = reply["structured_output"]["results"]
            got = {r["id"]: r for r in results if r["id"] in want}
            if set(got) == want:
                return got
            print(f"  batch returned {len(got)}/{len(want)} ids, retrying", file=sys.stderr)
        except (json.JSONDecodeError, KeyError, TypeError):
            print(f"  bad model output, retrying: {(proc.stdout or proc.stderr)[:200]}",
                  file=sys.stderr)
        time.sleep(3 * (attempt + 1))
    print("  giving up on a batch; its papers stay untriaged this run", file=sys.stderr)
    return {}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--days", type=int, help="look back this many days (default: since "
                    "the last triage, or 7 days on the first run)")
    ap.add_argument("--categories", nargs="+", default=DEFAULT_CATEGORIES)
    ap.add_argument("--model", default="sonnet")
    ap.add_argument("--min-score", type=int, default=2, choices=[1, 2, 3])
    ap.add_argument("--batch-size", type=int, default=20)
    ap.add_argument("--jobs", type=int, default=4, help="parallel claude calls")
    ap.add_argument("--limit", type=int, help="only triage the first N papers (testing)")
    ap.add_argument("--dry-run", action="store_true", help="don't write or push anything")
    args = ap.parse_args()

    ensure_data_checkout()
    feed_ids = {it["id"] for it in load_json(DATA / "papers.json", {}).get("items", [])}
    read = set(load_json(DATA / "read.json", {}).get("read", []))
    picks = load_json(DATA / "picks.json", {"items": []})
    # id -> submission date of every paper already judged, so overlapping or
    # interrupted runs never pay to score the same paper twice.
    state = load_json(DATA / "triage_state.json", {"scored": {}})
    scored = state["scored"]
    watch = load_json(HERE / "watchlist.json", {})
    tags = sorted({t for sec in ("papers", "authors") for w in watch.get(sec, [])
                   for t in w.get("tags", [])})
    template = (HERE / "triage_prompt.md").read_text(encoding="utf-8")

    now = datetime.now(timezone.utc)
    stamp = now.isoformat(timespec="seconds")
    if args.days:
        start = now - timedelta(days=args.days)
    elif picks.get("triaged_through"):
        # Overlap the previous run: arXiv only lists a paper once it is announced,
        # which can be days after its submission date (weekends, holidays).
        start = max(datetime.fromisoformat(picks["triaged_through"]) - timedelta(days=OVERLAP_DAYS),
                    now - timedelta(days=30))
    else:
        start = now - timedelta(days=7)

    oldest = (now - timedelta(days=400)).strftime("%Y-%m-%d")
    items = [it for it in picks["items"]
             if it["id"] not in read and it["id"] not in feed_ids and it["date"] >= oldest]

    def save(complete):
        out = {"triaged_through": stamp if complete else picks.get("triaged_through"),
               "items": sorted(items, key=lambda it: (it["added"][:10], it["date"]), reverse=True)}
        (DATA / "picks.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        (DATA / "triage_state.json").write_text(json.dumps(
            {"scored": {i: d for i, d in scored.items() if d >= oldest}}) + "\n", encoding="utf-8")

    # Work through the period one week at a time, newest first, saving after
    # each week so a long backfill can be interrupted and resumed.
    all_scores, n_picks, n_failed, n_left = {}, 0, 0, args.limit
    hi = now
    while hi > start and (n_left is None or n_left > 0):
        lo = max(start, hi - timedelta(days=7))
        print(f"\narXiv {' '.join(args.categories)}  {lo:%Y-%m-%d} .. {hi:%Y-%m-%d}", flush=True)
        papers = fetch_arxiv(args.categories, lo, hi)
        known = feed_ids | read | {it["id"] for it in items} | set(scored)
        todo = [p for p in papers if p["id"] not in known]
        if n_left is not None:
            todo = todo[:n_left]
            n_left -= len(todo)
        print(f"  {len(papers)} submissions, {len(todo)} to score", flush=True)
        batches = [todo[i:i + args.batch_size] for i in range(0, len(todo), args.batch_size)]
        scores = {}
        with ThreadPoolExecutor(args.jobs) as pool:
            for got in pool.map(lambda b: classify_batch(b, template, tags, args.model), batches):
                scores.update(got)
        by_id = {p["id"]: p for p in todo}
        for pid, r in scores.items():
            all_scores[pid] = {"title": by_id[pid]["title"], **r}
            scored[pid] = by_id[pid]["date"]
            if r["score"] >= args.min_score:
                n_picks += 1
                items.append({**by_id[pid], "added": stamp,
                              "tags": sorted(t for t in set(r["tags"]) if t in tags),
                              "why": [{"kind": "agent", "label": r["reason"].strip(),
                                       "score": r["score"]}]})
                print(f"  [{r['score']}] {by_id[pid]['title']}\n      "
                      f"https://arxiv.org/abs/{pid}\n      {r['reason'].strip()}", flush=True)
        n_failed += len(todo) - len(scores)
        if not args.dry_run:
            save(complete=False)
        hi = lo

    hist = [sum(1 for r in all_scores.values() if r["score"] == s) for s in range(4)]
    print(f"\nScores: 0:{hist[0]}  1:{hist[1]}  2:{hist[2]}  3:{hist[3]}   ({n_failed} failed)"
          f"   API-equivalent cost ${COST[0]:.2f}")

    # Full scores of this run, for tuning triage_prompt.md.
    (HERE / ".triage_last_run.json").write_text(json.dumps(
        sorted(all_scores.values(), key=lambda r: -r["score"]), ensure_ascii=False, indent=1),
        encoding="utf-8")

    if args.dry_run:
        print("Dry run: nothing written.")
        return

    # Only advance the high-water mark if every batch succeeded and nothing was skipped.
    save(complete=n_failed == 0 and args.limit is None)
    run("git", "add", "picks.json", "triage_state.json", cwd=DATA)
    if run("git", "diff", "--cached", "--name-only", cwd=DATA):
        run("git", "commit", "-m", f"Triage: {n_picks} picks", cwd=DATA)
        run("git", "pull", "--rebase", "--autostash", "origin", "data", cwd=DATA)
        run("git", "push", "origin", "data", cwd=DATA)
        print(f"Published {n_picks} new picks ({len(items)} agent picks unread in total).")
    else:
        print("Nothing to publish.")


if __name__ == "__main__":
    main()
