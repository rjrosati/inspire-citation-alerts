# inspire-citation-alerts

A personal paper feed: new papers that cite a paper on your watch list or are
written by an author on it, plus optional LLM-triaged picks from the arXiv
listings. It behaves like an RSS reader — papers pile up until you mark them
read.

Feed page: https://rjrosati.github.io/inspire-citation-alerts/

## How it fits together

| Piece | What it does |
| --- | --- |
| `watchlist.json` | Watched papers (INSPIRE record ids) and authors (INSPIRE author identifiers), each with a label and tags. |
| `update.py` | Queries INSPIRE for every watch and merges new hits into `papers.json`. Run daily by `.github/workflows/update.yml`, and again whenever `watchlist.json` changes. |
| `triage.py` + `triage_prompt.md` | Run by hand. Pulls recent arXiv submissions that the feed did not catch, has Sonnet score them against the interests in `triage_prompt.md`, and publishes the good ones to `picks.json`. |
| `docs/index.html` | The feed page (GitHub Pages). Filter by tag, watch or kind; mark read; edit the watch list. |
| `data` branch | `papers.json` (written by the workflow), `picks.json` (written by `triage.py`), `read.json` (written by the page). Kept off `main` so the daily commits stay out of the code history. |

Citations and disambiguated authors come from INSPIRE because the arXiv API
has neither. The arXiv API is used only for the triage listing.

## Using the page

Open "Watch list & settings" and paste a GitHub
[fine-grained token](https://github.com/settings/personal-access-tokens/new)
restricted to this repository with **Contents: Read and write**. With it, read
marks sync across devices and you can add, relabel, retag or remove watches
from the page. "Watch citations" on any paper adds it to the watch list.
Without a token the page is read-only and read marks stay in that browser.

Keys: `j`/`k` move, `m` mark read, `o` open, `a` toggle abstract.

## Running things by hand

```sh
python3 update.py                # refresh .data/papers.json locally
python3 triage.py --dry-run      # score the last week of arXiv, print picks
python3 triage.py                # same, and publish picks to the feed
```

`triage.py` needs the `claude` CLI logged in on the machine. It writes every
score from its last run to `.triage_last_run.json`; use that to tune
`triage_prompt.md` when it is too generous or too strict. Categories, model
and score threshold are command-line options (`--help`).

If the page shows a warning that an author watch matches no papers, INSPIRE
has renamed that author's identifier: remove the author and add them again
from the page.
