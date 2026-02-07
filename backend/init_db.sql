-- Create the application database
CREATE DATABASE analysisdb
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Connect to the new database
\c analysisdb

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE analysisdb TO postgres;

-- Extension for UUID generation (optional, if needed later)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
