CREATE OR REPLACE VIEW at.v_candles_1m AS
     SELECT oid
          , ts_dt::timestamptz AS ts
          , open::numeric AS open
          , max::numeric AS high
          , min::numeric AS low
          , close::numeric AS close
          , volume::numeric AS volume
          , amount::numeric AS amount
          , grain
       FROM trans.br_quotes
      WHERE 1=1
        AND grain = '1m'
        AND ts_dt IS NOT NULL
;

CREATE OR REPLACE VIEW at.v_base_20 AS
WITH base_with_lag AS (
  SELECT
    oid, ts, open, high, low, close, volume,
    LAG(close) OVER (PARTITION BY oid ORDER BY ts) AS prev_close,
    LAG(close, 1) OVER (PARTITION BY oid ORDER BY ts) AS prev_close_1
  FROM at.v_candles_1m
)
SELECT
  oid,
  ts,
  open, high, low, close, volume,
  -- 1. ATR (średnia zmienność)
  AVG(GREATEST(high - low,
               ABS(high - prev_close),
               ABS(low  - prev_close))) OVER w AS atr_20,

  -- 2. SMA & EMA (dla trendu)
  AVG(close) OVER w AS sma_20,
  (0.1 * close + 0.9 * prev_close_1) AS ema_20_approx,  -- uproszczona EMA

  -- 3. OBV (On-Balance Volume)
  SUM(
    CASE WHEN close > prev_close THEN volume
         WHEN close < prev_close THEN -volume
         ELSE 0 END
  ) OVER w AS obv,

  -- 4. Up/Down volume ratio
  SUM(volume) FILTER (WHERE close > open)  OVER w AS up_vol,
  SUM(volume) FILTER (WHERE close <= open) OVER w AS down_vol,

  -- 5. Spread i statystyki
  (high - low) AS spread,
  AVG(high - low) OVER w AS spread_avg,
  STDDEV_SAMP(high - low) OVER w AS spread_sd,

  -- 6. Średni wolumen
  AVG(volume) OVER w AS vol_avg

FROM base_with_lag
WINDOW w AS (PARTITION BY oid ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW);



CREATE OR REPLACE VIEW at.v_hidden_20 AS
WITH base AS (
  SELECT * ,
         -- okna / prymitywy
         up_vol / NULLIF(up_vol + down_vol, 0) AS c2_uvd,
         (obv - LAG(obv,10) OVER w)            AS obv_slope,
         STDDEV_SAMP(obv) OVER w               AS obv_sd,
         MAX(high) OVER w                      AS box_hi,
         MIN(low)  OVER w                      AS box_lo
  FROM at.v_base_20
  WINDOW w AS (PARTITION BY oid ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
),
lagged AS (
  SELECT *,
         LAG(box_lo) OVER (PARTITION BY oid ORDER BY ts) AS prev_box_lo
  FROM base
),
spring_raw AS (
  SELECT *,
         CASE WHEN low < prev_box_lo AND close > prev_box_lo
              THEN 0.2 ELSE 0 END AS spring_signal
  FROM lagged
),
-- 5 składowych (C1..C5) jako czytelne kolumny
components AS (
  SELECT
    *,
    -- C1: kontrakcja zmienności (logistic, z zabezpieczeniami)
    CASE 
      WHEN atr_20 IS NULL OR sma_20 IS NULL OR sma_20 = 0 THEN 0.5
      ELSE 1.0 / (1.0 + EXP(((atr_20 / NULLIF(sma_20,0))
        - AVG(atr_20 / NULLIF(sma_20,0)) OVER w)
        / GREATEST(STDDEV_SAMP(atr_20 / NULLIF(sma_20,0)) OVER w, 1e-9)))
    END AS c1_vol_comp,

    -- C3: OBV slope + flat price (mieszanka 0.7/0.3)
    CASE
      WHEN obv_sd IS NULL OR obv_sd = 0 OR sma_20 IS NULL OR sma_20 = 0 THEN 0.5
      WHEN obv_slope IS NULL THEN 0.5
      ELSE (1.0 / (1.0 + EXP(-COALESCE(obv_slope,0) / GREATEST(COALESCE(obv_sd,1e-9), 1e-9)))) * 0.7
           + (1.0 - COALESCE(box_hi - box_lo, 0) / GREATEST(COALESCE(sma_20,1e-9), 1e-9)) * 0.3
    END AS c3_money_flow,

    -- C4: no-supply (rolling avg z okna)
    AVG(
      CASE WHEN close < open
         AND (high - low) < (spread_avg - 0.5*COALESCE(spread_sd,0))
         AND volume < COALESCE(vol_avg,0) * 0.8 THEN 1 ELSE 0 END
    ) OVER w AS c4_no_supply,

    -- C5: spring (max w M=5 ostatnich)
    MAX(spring_signal) OVER (PARTITION BY oid ORDER BY ts ROWS BETWEEN 4 PRECEDING AND CURRENT ROW) AS c5_spring
  FROM spring_raw
  WINDOW w AS (PARTITION BY oid ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW)
),
scored AS (
  SELECT
    *,
    100 * (
      0.25 * c1_vol_comp
      + 0.25 * COALESCE(c2_uvd, 0.5)
      + 0.30 * c3_money_flow
      + 0.15 * c4_no_supply
      + 0.05 * c5_spring
    ) AS hidden_accum_score
  FROM components
)
SELECT
  -- OHLCV + box
  oid, ts, open, high, low, close, volume,
  box_hi, box_lo, ((box_hi + box_lo)/2.0) AS box_mid,

  -- składowe 0..1 (łatwe debugowanie)
  c1_vol_comp,
  COALESCE(c2_uvd, 0.5) AS c2_uvd,
  c3_money_flow,
  c4_no_supply,
  c5_spring,

  -- score 0..100
  hidden_accum_score,

  -- setup (jak u Ciebie: próg 70 + pozycja w boxie + brak wybicia)
  CASE
    WHEN hidden_accum_score >= 70
     AND close > ((MAX(high) OVER w + MIN(low) OVER w)/2.0)
     AND high  <  MAX(high) OVER w
    THEN TRUE ELSE FALSE
  END AS hidden_accum_setup
FROM scored
WINDOW w AS (PARTITION BY oid ORDER BY ts ROWS BETWEEN 19 PRECEDING AND CURRENT ROW);



CREATE TABLE IF NOT EXISTS at.indicator_snapshot (
  id bigserial PRIMARY KEY,
  oid int4 NOT NULL,
  ts timestamptz NOT NULL,
  timeframe text NOT NULL DEFAULT '1m',
  calc_at timestamptz NOT NULL DEFAULT now(),
  params jsonb NOT NULL,
  values jsonb NOT NULL,
  UNIQUE(oid, timeframe, ts)
);


-- INSERT INTO at.indicator_snapshot (oid, timeframe, ts, params, values)
-- SELECT
--   oid,
--   '1m' AS timeframe,
--   ts,
--   '{"N":20,"weights":[0.25,0.25,0.30,0.15,0.05]}'::jsonb AS params,
--   jsonb_build_object(
--     'hidden_accum_score', hidden_accum_score,
--     'hidden_accum_setup', hidden_accum_setup
--   ) AS values
-- FROM at.v_hidden_20
-- WHERE ts > COALESCE(
--   (SELECT MAX(ts) FROM at.indicator_snapshot s WHERE s.oid = v_hidden_20.oid AND s.timeframe = '1m'),
--   '1900-01-01'::timestamptz
-- )
-- ON CONFLICT (oid, timeframe, ts)
-- DO UPDATE SET
--   values = EXCLUDED.values,
--   calc_at = now();




CREATE OR REPLACE PROCEDURE "at".update_hidden_accum_snapshots()
	LANGUAGE plpgsql
AS $procedure$
DECLARE
  v_start timestamptz := now();
  v_count int;
BEGIN
  INSERT INTO at.indicator_snapshot (oid, timeframe, ts, calc_at, params, values)
  SELECT oid, timeframe, ts, calc_at, params, values
  FROM (
    WITH last_snap AS (
      SELECT oid, MAX(ts) AS last_ts
      FROM at.indicator_snapshot
      WHERE timeframe = '1m'
      GROUP BY oid
    )
    SELECT
      v.oid, '1m'::text AS timeframe, v.ts,
      now() AS calc_at,
      jsonb_build_object('N', 20, 'weights', jsonb_build_array(0.25,0.25,0.30,0.15,0.05)) AS params,
      jsonb_build_object(
        'hidden_accum_score', v.hidden_accum_score,
        'hidden_accum_setup', v.hidden_accum_setup
      ) AS values
    FROM at.v_hidden_20 v
    LEFT JOIN last_snap l ON l.oid = v.oid
    WHERE (l.last_ts IS NULL OR v.ts > l.last_ts)
  ) sub
  ON CONFLICT (oid, timeframe, ts)
  DO UPDATE SET values = EXCLUDED.values, calc_at = now();

  GET DIAGNOSTICS v_count = ROW_COUNT;

  INSERT INTO at.run_log (started_at, finished_at, rows_inserted, status, message)
  VALUES (v_start, now(), v_count, 'success', 'Inkrementalny update snapshotów wykonany.');

END $procedure$;




CREATE OR REPLACE VIEW at.v_candidates_to_breakout AS
WITH params AS (
  SELECT
    20::int     AS n,                   -- okno bazowe zgodne z v_hidden_20
    14::int     AS lookback_sessions,   -- ile ostatnich DNI SESYJNYCH analizujemy
    7::int      AS setup_sessions,      -- ile sesji wstecz liczymy „setupy”
    3::int      AS streak_sessions,     -- streak w ostatnich 3 SESJACH
    0.65::numeric AS avg_thresh,        -- próg średniego score (14 sesji)
    0.70::numeric AS high_thresh,       -- „wysoki” dzienny score
    0.02::numeric AS box_proximity      -- dystans do box_hi (<= 2%)
),
cal AS (
  SELECT session_date cal_date, True is_session
  FROM trans.session_calendar        
),
/* OSTATNIE *SESYJNE* DNI (lista) */
last_sessions AS (
  SELECT cal_date
  FROM cal
  WHERE is_session = true
    AND cal_date <= (now() AT TIME ZONE 'Europe/Warsaw')::date
  ORDER BY cal_date DESC
  LIMIT (SELECT lookback_sessions FROM params)
),
/* dla wygody: trzy ostatnie sesje i siedem ostatnich sesji */
last3_sessions AS (
  SELECT cal_date
  FROM last_sessions
  ORDER BY cal_date DESC
  LIMIT (SELECT streak_sessions FROM params)
),
last7_sessions AS (
  SELECT cal_date
  FROM last_sessions
  ORDER BY cal_date DESC
  LIMIT (SELECT setup_sessions FROM params)
),
/* 1) DZIENNE agregaty score/setup – TYLKO DLA DNI SESYJNYCH Z LOOKBACKU */
recent AS (
  SELECT
    s.oid,
    ((s.ts AT TIME ZONE 'Europe/Warsaw')::date) AS day,
    AVG( (s.values->>'hidden_accum_score')::numeric )      AS avg_score_day,
    BOOL_OR( (s.values->>'hidden_accum_setup')::bool )     AS any_setup_day
  FROM at.indicator_snapshot s
  JOIN params p ON TRUE
  JOIN last_sessions ls
    ON ls.cal_date = ((s.ts AT TIME ZONE 'Europe/Warsaw')::date)
  WHERE s.timeframe = '1m'
  GROUP BY s.oid, ((s.ts AT TIME ZONE 'Europe/Warsaw')::date)
),
/* 2) Dzienne wolumeny do filtrów/feature’ów – też tylko dni sesyjne */
recent_vol AS (
  SELECT
    c.oid,
    ((c.ts AT TIME ZONE 'Europe/Warsaw')::date) AS day,
    SUM(c.volume)::numeric AS day_volume
  FROM at.v_candles_1m c
  JOIN last_sessions ls
    ON ls.cal_date = ((c.ts AT TIME ZONE 'Europe/Warsaw')::date)
  GROUP BY c.oid, ((c.ts AT TIME ZONE 'Europe/Warsaw')::date)
),
/* 3) Agregacja po ostatnich 14 sesjach */
agg AS (
  SELECT
    r.oid,
    AVG(r.avg_score_day) AS avg_score_lookback,
    SUM(CASE WHEN r.avg_score_day >= (SELECT high_thresh FROM params) THEN 1 ELSE 0 END) AS high_score_days_lookback,
    SUM(CASE WHEN r.any_setup_day THEN 1 ELSE 0 END)
      FILTER (WHERE r.day IN (SELECT cal_date FROM last7_sessions))                       AS setups_last7,
    AVG(rv.day_volume) AS mean_volume_lookback
  FROM recent r
  LEFT JOIN recent_vol rv
    ON rv.oid = r.oid AND rv.day = r.day
  GROUP BY r.oid
),
/* 4) Streak: z ilu OSTATNICH 3 SESJI score był „wysoki” */
streak3 AS (
  SELECT
    r.oid,
    SUM(CASE
          WHEN r.day IN (SELECT cal_date FROM last3_sessions)
           AND r.avg_score_day >= (SELECT high_thresh FROM params)
        THEN 1 ELSE 0 END) AS high_score_last3
  FROM recent r
  GROUP BY r.oid
),
/* 5) Ostatni snapshot per oid (może wypaść w dzień niesesyjny, więc obcinamy do ostatniej sesji) */
latest_snap AS (
  SELECT s.oid, MAX(s.ts) AS last_ts
  FROM at.indicator_snapshot s
  WHERE s.timeframe = '1m'
  GROUP BY s.oid
),
latest_sess_ts AS (
  /* Dopasuj ostatni snapshot do ostatniego dnia sesyjnego, żeby price/box były z sesji */
  SELECT
    l.oid,
    MAX(s.ts) AS sess_ts
  FROM latest_snap l
  JOIN at.indicator_snapshot s
    ON s.oid=l.oid AND s.timeframe='1m'
  JOIN last_sessions ls
    ON ls.cal_date = ((s.ts AT TIME ZONE 'Europe/Warsaw')::date)
  GROUP BY l.oid
),
/* 6) Cena i box z ostatniej SESJI (v_hidden_20 zawiera box_hi/box_lo) */
price_box AS (
  SELECT
    h.oid,
    h.ts,
    h.close,
    h.box_hi,
    h.box_lo
  FROM latest_sess_ts t
  JOIN at.v_hidden_20 h
    ON h.oid = t.oid AND h.ts = t.sess_ts
),
/* 7) Złożenie metryk kandydata */
scored AS (
  SELECT
    a.oid,
    a.avg_score_lookback,
    a.high_score_days_lookback,
    s3.high_score_last3,
    a.setups_last7,
    a.mean_volume_lookback,
    pb.ts   AS last_ts,
    pb.close AS last_close,
    pb.box_hi,
    pb.box_lo,
    (pb.box_hi - pb.close) / NULLIF(pb.box_hi, 0)            AS dist_to_boxhi,       -- odległość względna do wybicia
    CASE WHEN pb.close > (pb.box_hi + pb.box_lo)/2 THEN 1 ELSE 0 END AS in_upper_half -- pozycja w boxie
  FROM agg a
  JOIN streak3 s3 ON s3.oid=a.oid
  JOIN price_box pb ON pb.oid=a.oid
)
/* 8) FINAŁ: filtry i ranking */
SELECT
  s.oid,
  s.last_ts,
  s.last_close,
  s.box_hi,
  ROUND(100 * (1 - s.last_close / s.box_hi), 2) AS pct_below_box_hi,
  s.avg_score_lookback       AS avg_score_14_sessions,
  s.high_score_days_lookback AS high_score_days_14_sessions,
  s.high_score_last3         AS high_score_last3_sessions,
  s.setups_last7             AS setups_last_7_sessions,
  s.mean_volume_lookback,
  /* ranking 0..1: akumulacja (0.6), streak (0.2), bliskość wybicia (0.2) */
  ( s.avg_score_lookback * 0.6
    + (s.high_score_last3 / (SELECT streak_sessions FROM params)) * 0.2
    + LEAST(1, GREATEST(0,
        1 - (s.dist_to_boxhi / (SELECT box_proximity FROM params))
      )) * 0.2
  ) AS rank_score
FROM scored s, params p
WHERE s.avg_score_lookback >= p.avg_thresh        -- utrzymująca się akumulacja (po sesjach)
  AND s.high_score_last3 >= (p.streak_sessions - 1)  -- min. 2 z 3 ostatnich sesji są „wysokie”
  AND s.in_upper_half = 1                          -- cena w górnej połowie boxu
  AND s.last_close < s.box_hi                      -- jeszcze bez wybicia
  AND s.dist_to_boxhi <= p.box_proximity           -- tuż pod wybiciem
ORDER BY rank_score DESC, avg_score_lookback DESC, pct_below_box_hi ASC;



