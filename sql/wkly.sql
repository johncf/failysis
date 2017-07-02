-- these queries were written for hive

CREATE TABLE disk_logs_wkly
( datestamp DATE,
  serial_no VARCHAR(32),
  power_hrs INT,
  blocks_read BIGINT,
  blocks_written BIGINT,
  wkid INT
);

CREATE TABLE disk_fails_wkly
( serial_no VARCHAR(32),
  wkid INT
);


INSERT INTO TABLE disk_logs_wkly
SELECT MAX(datestamp),
       serial_no,
       MAX(power_hrs),
       MAX(blocks_read),
       MAX(blocks_written),
       wkid
FROM (SELECT datestamp,
             serial_no,
             power_hrs,
             blocks_read,
             blocks_written,
             CAST(datediff(datestamp, '2007-01-01')/7 AS INT) AS wkid -- 2007-01-01 is a Monday
      FROM disk_logs
      WHERE power_hrs <> 'null' AND
            power_hrs <> '0' AND
            blocks_read <> '0' AND
            blocks_written <> '0') AS dvc
GROUP BY serial_no, wkid;


INSERT INTO TABLE disk_fails_wkly
SELECT serial_no,
       CAST(datestamp, '2007-01-01')/7 AS INT AS wkid
FROM disk_fails
GROUP BY serial_no AS uniq_disk_fails;
