"""Live ingest: Wikimedia EventStreams (every edit on every Wikipedia/Wikimedia
wiki, ~20-50 events/s) -> Tiger Cloud hypertable, micro-batched with COPY.

  python ingest.py --seconds 600     # stream for 10 minutes
  python ingest.py                   # stream forever
"""
import argparse, json, os, time
from datetime import datetime
import psycopg, requests

STREAM = "https://stream.wikimedia.org/v2/stream/recentchange"
UA = "ghw-tiger-streaming/1.0 (https://github.com/yniantongtian-oss/ghw-tiger-streaming)"

def events():
    while True:
        try:
            with requests.get(STREAM, stream=True, timeout=(10, 60),
                              headers={"Accept": "text/event-stream", "User-Agent": UA}) as r:
                r.raise_for_status()
                for line in r.iter_lines(decode_unicode=True):
                    if line and line.startswith("data: "):
                        try:
                            yield json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
        except requests.RequestException as e:
            print("stream reconnect:", e, flush=True); time.sleep(2)

def row(e):
    if e.get("type") not in ("edit", "new", "log", "categorize"):
        return None
    ln = e.get("length") or {}
    delta = (ln.get("new") or 0) - (ln.get("old") or 0) if ln else 0
    return (datetime.fromtimestamp(e["timestamp"]).astimezone(), e.get("wiki"), (e.get("title") or "")[:300],
            e.get("type"), bool(e.get("bot")), e.get("namespace"), delta, (e.get("user") or "")[:120])

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seconds", type=float, default=0); ap.add_argument("--flush", type=float, default=2.0)
    a = ap.parse_args()
    with psycopg.connect(os.environ["DATABASE_URL"], autocommit=True) as conn:
        ddl = open(os.path.join(os.path.dirname(__file__), "schema.sql")).read()
        for stmt in [x.strip() for x in ddl.split(";\n")]:
            if stmt and not all(l.startswith("--") or not l.strip() for l in stmt.splitlines()):
                conn.execute(stmt)
        start = last = time.time(); buf = []; total = 0
        for e in events():
            r = row(e)
            if r: buf.append(r)
            now = time.time()
            if now - last >= a.flush and buf:
                t0 = time.perf_counter()
                with conn.cursor().copy("COPY ghw25.wiki_edits (time, wiki, title, change_type, is_bot, namespace, byte_delta, user_name) FROM STDIN") as cp:
                    for x in buf: cp.write_row(x)
                total += len(buf)
                print(f"{datetime.now():%H:%M:%S} +{len(buf):4d} rows  total={total:7d}  copy={1000*(time.perf_counter()-t0):5.0f}ms  "
                      f"rate={total/(now-start):5.1f}/s", flush=True)
                buf.clear(); last = now
            if a.seconds and now - start > a.seconds:
                break
        print(f"done: {total} events in {time.time()-start:.0f}s")

if __name__ == "__main__":
    main()
