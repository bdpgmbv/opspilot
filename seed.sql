CREATE SCHEMA IF NOT EXISTS demo;

CREATE TABLE IF NOT EXISTS demo.signups (
    id          BIGSERIAL PRIMARY KEY,
    signup_date DATE NOT NULL,
    plan        TEXT NOT NULL,
    country     TEXT NOT NULL,
    source      TEXT NOT NULL
);

TRUNCATE demo.signups;

INSERT INTO demo.signups (signup_date, plan, country, source)
SELECT d::date,
       (ARRAY['free','pro','team'])[1 + floor(random() * 3)],
       (ARRAY['US','IN','DE','BR'])[1 + floor(random() * 4)],
       (ARRAY['organic','ads','referral'])[1 + floor(random() * 3)]
FROM generate_series(current_date - 29, current_date, interval '1 day') AS d,
     generate_series(1, 40) AS n;

-- Yesterday the ads channel broke. This is the thing to discover.
DELETE FROM demo.signups
WHERE signup_date = current_date - 1 AND source = 'ads';

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'opspilot_ro') THEN
    CREATE ROLE opspilot_ro LOGIN PASSWORD 'readonly';
  END IF;
END
$$;

GRANT CONNECT ON DATABASE opspilot TO opspilot_ro;
GRANT USAGE  ON SCHEMA demo TO opspilot_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA demo TO opspilot_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA demo GRANT SELECT ON TABLES TO opspilot_ro;