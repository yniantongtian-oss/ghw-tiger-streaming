"""Snapshot of the live pipeline written to results/RESULTS.md (row counts, ingest rate, cagg vs raw timing)."""
import os, time, statistics
from pathlib import Path
import psycopg
OUT = Path(__file__).parent / "results"; OUT.mkdir(exist_ok=True)
L = []
def log(s=""): print(s); L.append(s)
def tab(cur, sql, title):
    cur.execute(sql); cols = [d.name for d in cur.description]
    log(f"\n### {title}\n"); log("| " + " | ".join(cols) + " |"); log("|" + "---|" * len(cols))
    for r in cur.fetchall(): log("| " + " | ".join(str(v) for v in r) + " |")
def timed(cur, sql, n=5):
    ts = []
    for _ in range(n):
        t = time.perf_counter(); cur.execute(sql); cur.fetchall(); ts.append((time.perf_counter()-t)*1000)
    return round(statistics.median(ts), 1)
with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as c, c.cursor() as cur:
    cur.execute("CALL refresh_continuous_aggregate('ghw25.edits_per_minute', NULL, now() - interval '1 minute')")
    log(f"# Live pipeline snapshot - {time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    tab(cur, """SELECT count(*) AS rows, min(time) AS first_event, max(time) AS last_event,
                round(count(*) / greatest(extract(epoch FROM max(time)-min(time)),1)::numeric, 1) AS events_per_s,
                count(DISTINCT wiki) AS wikis FROM ghw25.wiki_edits""", "Ingested events")
    tab(cur, """SELECT chunk_name, range_start, range_end, is_compressed FROM timescaledb_information.chunks
                WHERE hypertable_schema='ghw25' ORDER BY range_start""", "Hypertable chunks")
    tab(cur, """SELECT minute, sum(edits) FILTER (WHERE NOT is_bot) AS human, sum(edits) FILTER (WHERE is_bot) AS bot,
                sum(bytes_added) AS bytes_added FROM ghw25.edits_per_minute GROUP BY 1 ORDER BY 1 DESC LIMIT 10""", "Continuous aggregate: last 10 minutes")
    tab(cur, """SELECT wiki, sum(edits) AS edits FROM ghw25.edits_per_minute GROUP BY 1 ORDER BY 2 DESC LIMIT 10""", "Top wikis over the run")
    raw = timed(cur, "SELECT time_bucket('1 minute', time), wiki, is_bot, count(*) FROM ghw25.wiki_edits GROUP BY 1,2,3")
    agg = timed(cur, "SELECT minute, wiki, is_bot, edits FROM ghw25.edits_per_minute")
    log(f"\n### Dashboard query latency (median of 5, client round-trip)\n\n| query | raw hypertable | continuous aggregate |\n|---|---|---|\n| per-minute edits by wiki & bot | {raw} ms | {agg} ms |")
    tab(cur, "SELECT job_id, application_name, schedule_interval FROM timescaledb_information.jobs WHERE hypertable_schema='ghw25' OR application_name ILIKE '%%Refresh%%' ORDER BY 1", "Background policies")
(OUT / "RESULTS.md").write_text("\n".join(L) + "\n")
