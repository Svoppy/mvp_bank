-- MVP Bank: Database and limited-privilege user setup
-- Run once as postgres superuser:
--   psql -U postgres -f setup_db.sql

-- Create the application database
CREATE DATABASE mvp_bank;

-- Create a limited-privilege user (NOT superuser)
CREATE USER mvp_bank_user WITH PASSWORD 'MvpBank_SecurePass1!';

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
