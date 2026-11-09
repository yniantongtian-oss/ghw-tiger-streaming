"""Streamlit live dashboard over the Tiger Cloud hypertable + continuous aggregate.
   streamlit run app.py"""
import os, time
import altair as alt, pandas as pd, psycopg, streamlit as st

st.set_page_config(page_title="Live Wikipedia edits on Tiger Data", page_icon="🐯", layout="wide")
REFRESH = int(os.environ.get("REFRESH_SECONDS", "5"))

@st.cache_resource
def conn():
    c = psycopg.connect(os.environ["DATABASE_URL"], autocommit=True, application_name="ghw25-dashboard")
    return c

def q(sql, params=None):
    t = time.perf_counter()
    with conn().cursor() as cur:
        cur.execute(sql, params)
        df = pd.DataFrame(cur.fetchall(), columns=[d.name for d in cur.description])
    return df, (time.perf_counter() - t) * 1000

st.title("🐯 Live Wikipedia edit stream on Tiger Data")
st.caption("Wikimedia EventStreams → micro-batched COPY → TimescaleDB hypertable → continuous aggregate (real-time) → this dashboard. "
           f"Auto-refresh every {REFRESH}s.")

kpi, ms1 = q("""SELECT count(*) FILTER (WHERE time > now() - interval '1 minute') AS last_min,
                       count(*) FILTER (WHERE time > now() - interval '5 minutes') AS last5,
                       round(100.0 * avg(is_bot::int) FILTER (WHERE time > now() - interval '5 minutes'), 1) AS bot_pct,
                       count(DISTINCT wiki) FILTER (WHERE time > now() - interval '5 minutes') AS wikis,
                       count(*) AS total, max(time) AS newest
                FROM ghw25.wiki_edits WHERE time > now() - interval '1 day'""")
k = kpi.iloc[0]
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Edits / s (last min)", f"{(k.last_min or 0)/60:.1f}")
c2.metric("Edits (last 5 min)", f"{int(k.last5 or 0):,}")
c3.metric("Bot share", f"{k.bot_pct or 0}%")
c4.metric("Active wikis", int(k.wikis or 0))
lag = (pd.Timestamp.now(tz="UTC") - pd.Timestamp(k.newest)).total_seconds() if k.newest is not None else float("nan")
c5.metric("Freshness (newest row)", f"{lag:.0f}s ago")

per_min, ms2 = q("""SELECT minute, CASE WHEN is_bot THEN 'bot' ELSE 'human' END AS who, sum(edits)::int AS edits
                     FROM ghw25.edits_per_minute WHERE minute > now() - interval '30 minutes' GROUP BY 1,2 ORDER BY 1""")
left, right = st.columns([2, 1])
with left:
    st.subheader("Edits per minute (continuous aggregate)")
    if not per_min.empty:
        st.altair_chart(alt.Chart(per_min).mark_bar().encode(
            x=alt.X("minute:T", title=None), y=alt.Y("edits:Q", stack=True), color=alt.Color("who:N", scale=alt.Scale(range=["#f5a623", "#4a90e2"]))
        ).properties(height=300), width='stretch')
top, ms3 = q("""SELECT wiki, sum(edits)::int AS edits, sum(bytes_added)::bigint AS bytes_added
                FROM ghw25.edits_per_minute WHERE minute > now() - interval '10 minutes' GROUP BY wiki ORDER BY edits DESC LIMIT 10""")
with right:
    st.subheader("Top wikis, last 10 min")
    if not top.empty:
        st.altair_chart(alt.Chart(top).mark_bar(color="#f5a623").encode(x="edits:Q", y=alt.Y("wiki:N", sort="-x", title=None)).properties(height=300),
                        width='stretch')

st.subheader("Latest events")
latest, ms4 = q("""SELECT to_char(time AT TIME ZONE 'UTC', 'HH24:MI:SS') AS utc, wiki, change_type, is_bot, byte_delta, left(title, 80) AS title
                   FROM ghw25.wiki_edits ORDER BY time DESC LIMIT 12""")
st.dataframe(latest, hide_index=True, width='stretch')
st.caption(f"Query latency (ms): KPIs {ms1:.0f} · per-minute cagg {ms2:.0f} · top wikis {ms3:.0f} · latest {ms4:.0f}  —  total rows in last day: {int(k.total):,}")

time.sleep(REFRESH)
st.rerun()
