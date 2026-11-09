-- Real-time Wikipedia edit stream on Tiger Cloud
CREATE SCHEMA IF NOT EXISTS ghw25;

CREATE TABLE IF NOT EXISTS ghw25.wiki_edits (
  time        timestamptz NOT NULL,
  wiki        text        NOT NULL,
  title       text,
  change_type text,
  is_bot      boolean,
  namespace   int,
  byte_delta  int,
  user_name   text
) WITH (
  tsdb.hypertable,
  tsdb.partition_column = 'time',
  tsdb.chunk_interval   = '1 hour',
  tsdb.segmentby        = 'wiki',
  tsdb.orderby          = 'time DESC'
);
CREATE INDEX IF NOT EXISTS wiki_edits_wiki_time ON ghw25.wiki_edits (wiki, time DESC);

-- Continuous aggregate: edits per minute per wiki, bot vs human (real-time: includes not-yet-materialized rows)
CREATE MATERIALIZED VIEW IF NOT EXISTS ghw25.edits_per_minute
WITH (timescaledb.continuous, timescaledb.materialized_only = false) AS
SELECT time_bucket('1 minute', time) AS minute, wiki, is_bot,
       count(*)                          AS edits,
       sum(greatest(byte_delta, 0))      AS bytes_added,
       sum(least(byte_delta, 0))         AS bytes_removed
FROM ghw25.wiki_edits
GROUP BY 1, 2, 3
WITH NO DATA;

SELECT add_continuous_aggregate_policy('ghw25.edits_per_minute',
  start_offset => INTERVAL '2 hours', end_offset => INTERVAL '1 minute',
  schedule_interval => INTERVAL '1 minute', if_not_exists => true);

-- Keep the free trial cheap: drop raw data after 3 days, compress after 2 hours
SELECT add_retention_policy('ghw25.wiki_edits', INTERVAL '3 days', if_not_exists => true);
CALL add_columnstore_policy('ghw25.wiki_edits', after => INTERVAL '2 hours', if_not_exists => true);
