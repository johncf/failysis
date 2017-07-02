-- these queries were written for postgres

CREATE TABLE disk_logs_wkly_delta
( serial_no TEXT NOT NULL,
  cur_power_hrs BIGINT,
  cur_blocks_read BIGINT,
  cur_blocks_written BIGINT,
  prev_power_hrs BIGINT,
  prev_blocks_read BIGINT,
  prev_blocks_written BIGINT,
  effective_load_gbph DOUBLE PRECISION,
  wkid INTEGER NOT NULL,
  --CONSTRAINT dl_serwk_pk PRIMARY KEY (serial_no, wkid)
);

CREATE TABLE disk_fails_wkly
( serial_no TEXT NOT NULL,
  wkid INTEGER NOT NULL,
  --CONSTRAINT df_serwk_pk PRIMARY KEY (serial_no, wkid)
)

-- const_blocks_per_gb = disk_details.phy_size_blocks / disk_details.phy_size_mb * 1024

INSERT INTO TABLE disk_logs_wkly_delta
SELECT dlw.serial_no,
       dlw.power_hrs, dlw.blocks_read, dlw.blocks_written,
       dlwp.power_hrs, dlwp.blocks_read, dlwp.blocks_written,
       (dlw.blocks_read + dlw.blocks_written - dlwp.blocks_read - dlwp.blocks_written)/(dlw.power_hrs - dlwp.power_hrs)/const_blocks_per_gb,
       dlw.wkid
FROM disk_logs_wkly AS dlw INNER JOIN disk_logs_wkly AS dlwp
     ON (dlw.serial_no = dlwp.serial_no AND dlw.wkid = dlwp.wkid + 1)
WHERE dlw.power_hrs > dlwp.power_hrs AND dlw.power_hrs < dlwp.power_hrs + 24*7*2 AND -- sane power_hrs
      dlw.blocks_read > dlwp.blocks_read AND dlw.blocks_written > dlwp.blocks_written; -- sane blocks read/written

-- insert missing broken entries from disk_logs
INSERT INTO disk_logs_wkly_delta(serial_no, wkid,
                                 cur_power_hrs, cur_blocks_read, cur_blocks_written,
                                 prev_power_hrs, prev_blocks_read, prev_blocks_written,
                                 effective_load_gbph)
SELECT dlwd.serial_no, dm.wkid,
       dlwd.cur_power_hrs, dlwd.cur_blocks_read, dlwd.cur_blocks_written,
       dlwd.cur_power_hrs, dlwd.cur_blocks_read, dlwd.cur_blocks_written,
       dlwd.effective_load_gbph -- borrow the previous value
FROM disk_logs_wkly_delta AS dlwd INNER JOIN
     (SELECT df.serial_no AS serial_no, df.wkid AS wkid
      FROM disk_fails_wkly AS df LEFT OUTER JOIN disk_logs_wkly_delta AS dl
      ON dl.serial_no = df.serial_no AND dl.wkid = df.wkid
      WHERE dl.serial_no IS NULL) AS dm
     ON dlwd.serial_no = dm.serial_no AND dla.wkid = dm.wkid - 1;



-- cumulative failures over power_hrs
WITH ct AS (SELECT cur_power_hrs, COUNT(dl.serial_no) AS disk_count
            FROM disk_logs_wkly_delta AS dl INNER JOIN disk_fails_wkly AS df
            ON dl.serial_no = df.serial_no AND dl.wkid = df.wkid
            WHERE dl.effective_load_gbph BETWEEN 0 AND 1.6
            GROUP BY cur_power_hrs)
SELECT cur_power_hrs, SUM(disk_count) OVER (ORDER BY cur_power_hrs)
FROM ct

-- observed population over power_hrs
WITH dll AS (SELECT prev_power_hrs, cur_power_hrs
             FROM disk_logs_wkly_delta
             WHERE effective_load_gbph BETWEEN 0 AND 1.6),
     bps AS (SELECT 1 AS bump,
                    prev_power_hrs AS power_hrs
             FROM dll
             UNION ALL
             SELECT -1 AS bump,
                    cur_power_hrs AS power_hrs
             FROM dll),
     dls AS (SELECT power_hrs,
                    SUM(bump) AS deltas
             FROM bps
             GROUP BY power_hrs)
SELECT power_hrs,
       SUM(deltas) OVER (ORDER BY power_hrs) AS observed_pop
FROM dls;



-- average load
WITH wl AS  (SELECT serial_no,
                    cur_power_hrs AS power_hrs,
                    prev_power_hrs AS power_hrs_first,
                    (cur_blocks_read + cur_blocks_written) AS blocks_transferred,
                    (prev_blocks_read + prev_blocks_written) AS blocks_transferred_first
             FROM disk_logs_wkly_delta
             WHERE cur_power_hrs > prev_power_hrs),
     dll AS (SELECT power_hrs - power_hrs_first AS poh_span,
                    (blocks_transferred - blocks_transferred_first)/(power_hrs - power_hrs_first)/const_blocks_per_gb AS load
             FROM wl)
SELECT SUM(poh_span * load)/SUM(poh_span) AS avg_load
FROM dll WHERE load BETWEEN 0 AND 1.6



-- === net over entire observation === ---
-- cumulative failures over power_hrs
WITH wl AS (SELECT serial_no,
                   MAX(cur_power_hrs) AS power_hrs,
                   MIN(prev_power_hrs) AS power_hrs_first,
                   MAX(cur_blocks_read + cur_blocks_written) AS blocks_transferred,
                   MIN(prev_blocks_read + prev_blocks_written) AS blocks_transferred_first
            FROM disk_logs_wkly_delta
            GROUP BY serial_no),
     ct AS (SELECT power_hrs, COUNT(wl.serial_no) AS disk_count
            FROM wl INNER JOIN disk_fails_wkly AS df
            ON wl.serial_no = df.serial_no
            WHERE (blocks_transferred - blocks_transferred_first)/(power_hrs - power_hrs_first)/const_blocks_per_gb BETWEEN 0 AND 1.6
            GROUP BY power_hrs)
SELECT power_hrs, SUM(disk_count) OVER (ORDER BY power_hrs)
FROM ct

-- observed population over power_hrs
WITH wl AS  (SELECT serial_no,
                    MAX(cur_power_hrs) AS power_hrs,
                    MIN(prev_power_hrs) AS power_hrs_first,
                    MAX(cur_blocks_read + cur_blocks_written) AS blocks_transferred,
                    MIN(prev_blocks_read + prev_blocks_written) AS blocks_transferred_first
             FROM disk_logs_wkly_delta
             GROUP BY serial_no),
     dll AS (SELECT power_hrs_first AS min_poh, power_hrs AS max_poh
             FROM wl
             WHERE (blocks_transferred - blocks_transferred_first)/(power_hrs - power_hrs_first)/const_blocks_per_gb BETWEEN 0 AND 1.6),
     bps AS (SELECT 1 AS bump,
                    min_poh AS power_hrs
             FROM dll
             UNION ALL
             SELECT -1 AS bump,
                    max_poh AS power_hrs
             FROM dll),
     dls AS (SELECT power_hrs,
                    SUM(bump) AS deltas
             FROM bps
             GROUP BY power_hrs)
SELECT power_hrs,
       SUM(deltas) OVER (ORDER BY power_hrs) AS observed_pop
FROM dls;

-- average load
WITH wl AS  (SELECT serial_no,
                    MAX(cur_power_hrs) AS power_hrs,
                    MIN(prev_power_hrs) AS power_hrs_first,
                    MAX(cur_blocks_read + cur_blocks_written) AS blocks_transferred,
                    MIN(prev_blocks_read + prev_blocks_written) AS blocks_transferred_first
             FROM disk_logs_wkly_delta
             GROUP BY serial_no),
     dll AS (SELECT power_hrs - power_hrs_first AS poh_span,
                    (blocks_transferred - blocks_transferred_first)/(power_hrs - power_hrs_first)/const_blocks_per_gb AS load
             FROM wl)
SELECT SUM(poh_span * load)/SUM(poh_span) AS avg_load
FROM dll WHERE load BETWEEN 0 AND 1.6



-- === nice queries === ---
-- statistic check: how many failures with avg load > 16 GB/hr
SELECT COUNT(*)
FROM disk_logs_wkly_delta AS dlw INNER JOIN disk_fails_wkly AS dfw
     ON (dlw.serial_no = dfw.serial_no AND dlw.wkid = dfw.wkid)
WHERE effective_load_gbph > 16


-- per week counts
with dfc as ( -- number of failures per week
         select df.wkid, count(*) df_cnt
         from disk_fails_wkly df
         group by df.wkid),
     dflc as ( -- number of failures with matching delta logs per week
         select df.wkid, count(*) dfl_cnt
         from disk_fails_wkly df inner join disk_logs_wkly_delta dl on df.serial_no = dl.serial_no and df.wkid = dl.wkid
         group by df.wkid),
     dlc as ( -- number of logs per week
         select dl.wkid, count(*) dl_cnt
         from disk_logs_wkly_delta dl
         group by dl.wkid)
select dfc.wkid, df_cnt, dfl_cnt, dl_cnt
from dfc inner join dflc on dfc.wkid = dflc.wkid
         inner join dlc on dfc.wkid = dlc.wkid
order by dfc.wkid

-- sanitize: delete the first failure among duplicates
delete from disk_fails_wkly df
using (select serial_no, min(wkid) as min_wkid
       from disk_fails_wkly group by serial_no having count(*) > 1) dups
where df.serial_no = dups.serial_no and df.wkid = dups.min_wkid

-- update mismatched wkids by moving wkids backward or forward
update disk_fails_wkly df
set wkid = missing.max_wkid
from (select df.serial_no, df.wkid as failed_wkid, max(dl.wkid) max_wkid
      from disk_fails_wkly df inner join disk_logs_wkly_delta dl on df.serial_no = dl.serial_no
      group by df.serial_no, df.wkid
      having df.wkid > max(dl.wkid) and df.wkid - max(dl.wkid) <= 4) missing -- backward
   -- having df.wkid < max(dl.wkid) and max(dl.wkid) - df.wkid <= 2) missing -- forward
where missing.serial_no = df.serial_no
