-- Cat House Database Initialization Script
-- This script creates separate schemas for each service

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas for each service
CREATE SCHEMA IF NOT EXISTS auth;
CREATE SCHEMA IF NOT EXISTS catalog;
CREATE SCHEMA IF NOT EXISTS installation;
CREATE SCHEMA IF NOT EXISTS proxy;

-- Grant permissions
GRANT ALL PRIVILEGES ON SCHEMA auth TO catuser;
GRANT ALL PRIVILEGES ON SCHEMA catalog TO catuser;
GRANT ALL PRIVILEGES ON SCHEMA installation TO catuser;
GRANT ALL PRIVILEGES ON SCHEMA proxy TO catuser;

-- Set default search path
ALTER DATABASE cathouse SET search_path TO auth, catalog, installation, proxy, public;
