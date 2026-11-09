# Live pipeline snapshot - 2026-11-09 08:05:28 UTC

### Ingested events

| rows | first_event | last_event | events_per_s | wikis |
|---|---|---|---|---|
| 13164 | 2026-11-09 07:59:49+00:00 | 2026-11-09 08:05:26+00:00 | 39.1 | 118 |

### Hypertable chunks

| chunk_name | range_start | range_end | is_compressed |
|---|---|---|---|
| _hyper_4_211_chunk | 2026-11-09 07:00:00+00:00 | 2026-11-09 08:00:00+00:00 | False |
| _hyper_4_212_chunk | 2026-11-09 08:00:00+00:00 | 2026-11-09 09:00:00+00:00 | False |

### Continuous aggregate: last 10 minutes

| minute | human | bot | bytes_added |
|---|---|---|---|
| 2026-11-09 08:05:00+00:00 | 690 | 435 | 397548 |
| 2026-11-09 08:04:00+00:00 | 1732 | 1145 | 1067915 |
| 2026-11-09 08:03:00+00:00 | 1128 | 872 | 925600 |
| 2026-11-09 08:02:00+00:00 | 1217 | 875 | 918914 |
| 2026-11-09 08:01:00+00:00 | 1201 | 1099 | 1084286 |
| 2026-11-09 08:00:00+00:00 | 1325 | 1262 | 1160164 |
| 2026-11-09 07:59:00+00:00 | 87 | 96 | 75333 |

### Top wikis over the run

| wiki | edits |
|---|---|
| commonswiki | 6236 |
| wikidatawiki | 2040 |
| enwiki | 857 |
| kaawiki | 706 |
| enwiktionary | 325 |
| arwiki | 316 |
| dewiki | 211 |
| frwiki | 199 |
| mgwiktionary | 191 |
| zhwiki | 187 |

### Dashboard query latency (median of 5, client round-trip)

| query | raw hypertable | continuous aggregate |
|---|---|---|
| per-minute edits by wiki & bot | 138.8 ms | 137.0 ms |

### Background policies

| job_id | application_name | schedule_interval |
|---|---|---|
| 1001 | Columnstore Policy [1001] | 1 day, 0:00:00 |
| 1002 | Refresh Continuous Aggregate Policy [1002] | 0:01:00 |
| 1003 | Retention Policy [1003] | 1 day, 0:00:00 |
