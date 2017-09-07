CREATE TABLE disk_logs
( datestamp DATE,
  serial_no VARCHAR(32),
  power_hrs INT,
  blocks_read BIGINT,
  blocks_written BIGINT
);

CREATE TABLE disk_fails
( serial_no VARCHAR(32),
  datestamp DATE
);

-- import data from csv files
COPY disk_logs FROM '/path/to/disk_logs.csv' WITH (FORMAT csv);
COPY disk_fails FROM '/path/to/disk_fails.csv' WITH (FORMAT csv);

CREATE VIEW disk_summary AS
SELECT serial_no,
       MIN(dl.datestamp) AS first_seen,
       MAX(dl.datestamp) AS last_seen,
       MIN(dl.power_hrs) AS min_power_hrs,
       MAX(dl.power_hrs) AS max_power_hrs
FROM disk_logs AS dl
GROUP BY serial_no

-- cumulative failures over power_hrs -- C(t)
SELECT power_hrs, SUM(disk_count) OVER (ORDER BY power_hrs)
FROM (SELECT power_hrs, COUNT(dl.serial_no) AS disk_count
      FROM disk_logs AS dl INNER JOIN disk_fails AS df
           ON dl.serial_no = df.serial_no AND
              dl.datestamp = df.datestamp -- under the assumption that a corresponding activity log exists for every failure log
      GROUP BY power_hrs) AS cu

-- observed population over power_hrs -- N(t)
WITH cgs AS (SELECT power_hrs,
                    SUM(contrib_step) AS contrib_group
             FROM (SELECT 1 AS contrib_step,
                          min_power_hrs AS power_hrs
                   FROM disk_summary
                   UNION ALL
                   SELECT -1 AS contrib_step,
                          max_power_hrs AS power_hrs
                   FROM disk_summary) AS pop_contrib_steps
             GROUP BY power_hrs) -- ORDER BY power_hrs ??
SELECT power_hrs,
       SUM(contrib_group) OVER (ORDER BY power_hrs) AS observed_pop
FROM cgs

-- sanity check: max_power_hrs vs last seen power_hrs
SELECT ds.serial_no, ds.last_seen, dl.power_hrs AS last_power_hrs, ds.max_power_hrs -- COUNT(DISTINCT ds.serial_no)
FROM disk_summary AS ds JOIN disk_logs AS dl
     ON ds.serial_no = dl.serial_no AND ds.last_seen = dl.datestamp
WHERE ds.max_power_hrs <> dl.power_hrs

-- sanity check: disks that spans more than const_n weeks of observations
SELECT serial_no,
       MIN(power_hrs)/24 AS min_pod,
       MAX(power_hrs)/24 AS max_pod
FROM disk_logs
GROUP BY serial_no
HAVING MAX(power_hrs) - MIN(power_hrs) > 24*(7*const_n + 1)
-- DELETE FROM disk_logs AS dl USING (/* above query*/) dx WHERE dl.serial_no = dx.serial_no

-- sanity check: number of failures for the same disk
SELECT df.serial_no AS serial_no,
       collect_set(df.datestamp) AS dates_failed -- array_agg in postgres
FROM disk_fails AS df
GROUP BY df.serial_no
HAVING size(dates_failed) > 1

-- sanity check: number of failures for the same disk that are too far apart
SELECT df.serial_no AS serial_no,
       max(df.datestamp) AS max_date_failed,
       min(df.datestamp) AS min_date_failed
FROM disk_fails AS df
GROUP BY df.serial_no
HAVING datediff(max_date_failed, min_date_failed) > 7

-- sanity check: number of logs after a failure
SELECT df.serial_no,
       SUM(1) AS ct
FROM disk_fails AS df INNER JOIN disk_logs AS dl
     ON dl.serial_no = df.serial_no
WHERE dl.datestamp > df.datestamp
GROUP BY df.serial_no

-- sanity check: failure logs that don't have corresponding activity logs
SELECT serial_no
FROM disk_fails WHERE serial_no NOT IN
  ( SELECT df.serial_no
    FROM disk_fails AS df INNER JOIN disk_logs AS dl
         ON dl.serial_no = df.serial_no AND dl.datestamp = df.datestamp)
