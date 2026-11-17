-- 1. Replace THE_ANALYTICS_BUCKET with the CloudFormation AnalyticsBucketName output.
-- 2. Execute in the AWS Athena console; select an encrypted S3 query-results location.
CREATE DATABASE IF NOT EXISTS atlas_analytics;

CREATE EXTERNAL TABLE IF NOT EXISTS atlas_analytics.http_activity (
  event_ts_utc STRING,
  method STRING,
  route STRING,
  status STRING,
  latency_ms STRING,
  request_id STRING,
  event_type STRING
)
ROW FORMAT SERDE 'org.apache.hadoop.hive.serde2.OpenCSVSerde'
WITH SERDEPROPERTIES (
  'separatorChar' = ',',
  'quoteChar' = '"',
  'escapeChar' = '\\'
)
STORED AS TEXTFILE
LOCATION 's3://THE_ANALYTICS_BUCKET/activity/';

-- Requests, errors and approximate average latency per hour.
SELECT date_trunc('hour', from_iso8601_timestamp(event_ts_utc)) AS hour_utc,
       count(*) AS request_count,
       count_if(try_cast(status AS integer) >= 500) AS server_errors,
       round(avg(try_cast(latency_ms AS double)), 1) AS mean_latency_ms
FROM atlas_analytics.http_activity
WHERE event_type = 'http_request'
GROUP BY 1 ORDER BY 1 DESC LIMIT 48;
