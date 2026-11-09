# ghw-tiger-streaming — real-time Wikipedia edit analytics on Tiger Data

MLH Global Hack Week: Builders Week · Tiger Data Challenge 4 *"Build a Real-Time Streaming Analytics App"*.

**Live feed:** [Wikimedia EventStreams](https://stream.wikimedia.org/v2/stream/recentchange) — every edit on every Wikipedia / Wikidata /
Commons wiki, worldwide, ~30-50 events per second (a real user-activity stream, no API key).

```
EventStreams (SSE) ──► ingest.py (micro-batched COPY every 2 s) ──► hypertable ghw25.wiki_edits (1-hour chunks)
                                                                      │
                                    continuous aggregate ghw25.edits_per_minute (real-time, refreshed every minute)
                                                                      │
                                                       Streamlit dashboard (app.py, auto-refresh 5 s)
```

* `schema.sql` — hypertable created with `WITH (tsdb.hypertable ...)`, continuous aggregate (edits / bytes per minute per wiki, bot vs
  human) with `materialized_only = false` so the newest seconds are included, refresh policy, columnstore policy after 2 h and a 3-day
  retention policy to keep the free tier small.
* `ingest.py` — resilient SSE consumer (auto-reconnect), batches rows and writes them with `COPY`.
* `app.py` — Streamlit dashboard: edits/s, bot share, active wikis, data freshness, per-minute chart from the continuous aggregate,
  top wikis, latest events, query latencies.
* `report.py` — writes a snapshot of the pipeline (row counts, ingest rate, chunks, cagg vs raw latency, background jobs) to
  [`results/RESULTS.md`](results/RESULTS.md).

Screenshot of the dashboard during a live run: [`results/dashboard.png`](results/dashboard.png).

## Run it
```bash
cp .env.example .env && export $(grep -v '^#' .env | xargs)
pip install -r requirements.txt
python ingest.py &                 # stream forever (or --seconds 600)
streamlit run app.py               # http://localhost:8501
python report.py                   # snapshot -> results/RESULTS.md
```
`ci/run-live.yml` streams for ~5 minutes in GitHub Actions, screenshots the dashboard with headless Chromium and commits the results
(secret: `DATABASE_URL`). Copy it to `.github/workflows/` to enable it.

## Stack
Tiger Cloud (TimescaleDB) · hypertables · continuous aggregates · columnstore + retention policies · Wikimedia EventStreams (SSE) ·
Python · psycopg 3 · Streamlit · Altair
