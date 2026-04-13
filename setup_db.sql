-- MVP Bank: Database and limited-privilege user setup
-- Run once as postgres superuser:
--   psql -U postgres -v app_password='StrongRandomPasswordHere' -f setup_db.sql

-- Create the application database
CREATE DATABASE mvp_bank;

-- Create a limited-privilege user (NOT superuser)
-- Do not hardcode production credentials in source control.
\if :{?app_password}
\else
    \set app_password 'CHANGE_ME_STRONG_PASSWORD'
\endif
CREATE USER mvp_bank_user WITH PASSWORD :'app_password';

-- Grant only what the app needs
GRANT CONNECT ON DATABASE mvp_bank TO mvp_bank_user;
\c mvp_bank
GRANT USAGE ON SCHEMA public TO mvp_bank_user;
GRANT CREATE ON SCHEMA public TO mvp_bank_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mvp_bank_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO mvp_bank_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT USAGE ON SEQUENCES TO mvp_bank_user;
