-- these queries were written for hive

CREATE TABLE disk_logs
( datestamp DATE,
  serial_no VARCHAR(32),
  power_hrs INT,
  blocks_read BIGINT,
  blocks_written BIGINT
);

CREATE TABLE disk_details
( serial_no VARCHAR(32),
  phy_size_blocks BIGINT,
  phy_size_mb INT
);

CREATE TABLE disk_fails
( serial_no VARCHAR(32),
  datestamp DATE
);

CREATE VIEW disk_summary AS
SELECT dd.serial_no,
       ls.first_seen, ls.last_seen,
       ls.min_power_hrs, ls.max_power_hrs,
       ls.min_blocks_read / phy_size_blocks / phy_size_mb AS min_mbs_read,
       ls.max_blocks_read / phy_size_blocks / phy_size_mb AS max_mbs_read,
       ls.min_blocks_written / phy_size_blocks / phy_size_mb AS min_mbs_written,
       ls.max_blocks_written / phy_size_blocks / phy_size_mb AS max_mbs_written
FROM disk_details AS dd LEFT SEMI JOIN (SELECT serial_no,
                                               MIN(dl.datestamp) AS first_seen,
                                               MAX(dl.datestamp) AS last_seen,
                                               MIN(dl.power_hrs) AS min_power_hrs,
                                               MAX(dl.power_hrs) AS max_power_hrs,
                                               MIN(dl.blocks_read) AS min_blocks_read,
                                               MAX(dl.blocks_read) AS max_blocks_read,
                                               MIN(dl.blocks_written) AS min_blocks_written,
                                               MAX(dl.blocks_read) AS max_blocks_written
                                        FROM disk_logs
                                        GROUP BY serial_no) AS ls
     ON dd.serial_no = df.serial_no


-- cumulative failures over power_hrs
SELECT max_power_hrs, SUM(disk_count) OVER (ORDER BY max_power_hrs)
FROM (SELECT max_power_hrs, COUNT(ds.serial_no) AS disk_count
      FROM disk_summary AS ds LEFT SEMI JOIN disk_fails AS df
           ON ds.serial_no = df.serial_no
      GROUP BY max_power_hrs) AS cu


-- observed population over power_hrs
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


-- top 100 disks based on avg load over observed life
SELECT serial_no,
       del_power_hrs,
       del_mbs_read / del_power_hrs / 3600 AS avg_rrate_mbps,
       del_blocks_written / del_power_hrs / 3600 AS avg_wrate_mbps
FROM (SELECT serial_no,
             max_power_hrs - min_power_hrs AS del_power_hrs,
             max_mbs_read - min_mbs_read AS del_mbs_read,
             max_mbs_written - min_mbs_written AS del_blocks_written
      FROM disk_summary) AS ddd
WHERE del_power_hrs <> 0
ORDER BY (avg_rrate_mbps + avg_wrate_mbps) DESC
LIMIT 100

-- number of disks which faced more than 10 GB/hr load avg over observed life
SELECT COUNT(serial_no) FROM disk_summary
WHERE (max_mbs_read + max_mbs_written - min_mbs_read - min_mbs_written)/max_power_hrs/1024 > 10


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
SELECT df.serial_no AS serial_no,
       df.datestamp AS date_failed,
       sum(cast(df.datestamp >= dl.datestamp AS INT)) AS log_count
FROM disk_fails AS df LEFT JOIN disk_logs AS dl
     ON dl.serial_no = df.serial_no
GROUP BY df.serial_no, df.datestamp
HAVING log_count = 0
