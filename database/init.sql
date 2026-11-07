-- database/init.sql
-- NEXUS AI PostgreSQL schema with PostGIS extension
-- Run: psql -U postgres -d nexus_ai -f database/init.sql

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(64) UNIQUE NOT NULL,
    email       VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name   VARCHAR(255),
    phone       VARCHAR(20),
    role        VARCHAR(20) NOT NULL DEFAULT 'citizen',
    city        VARCHAR(100),
    ward        VARCHAR(100),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Issues
CREATE TABLE IF NOT EXISTS issues (
    id              SERIAL PRIMARY KEY,
    title           VARCHAR(300) NOT NULL,
    description     TEXT,
    category        VARCHAR(50) NOT NULL,
    severity        VARCHAR(20) NOT NULL DEFAULT 'medium',
    status          VARCHAR(30) NOT NULL DEFAULT 'open',
    latitude        DECIMAL(10,7),
    longitude       DECIMAL(10,7),
    location        GEOGRAPHY(Point, 4326),
    ward            VARCHAR(100),
    city            VARCHAR(100),
    pincode         VARCHAR(10),
    reporter_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    duplicate_of    INTEGER REFERENCES issues(id) ON DELETE SET NULL,
    duplicate_count INTEGER NOT NULL DEFAULT 0,
    ai_detected_label VARCHAR(100),
    ai_confidence   DECIMAL(5,4),
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at     TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_issues_location ON issues USING GIST(location);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
CREATE INDEX IF NOT EXISTS idx_issues_severity ON issues(severity);
CREATE INDEX IF NOT EXISTS idx_issues_category ON issues(category);
CREATE INDEX IF NOT EXISTS idx_issues_city ON issues(city);
CREATE INDEX IF NOT EXISTS idx_issues_ward ON issues(ward);
CREATE INDEX IF NOT EXISTS idx_issues_created ON issues(created_at DESC);

-- Locations (1:1 with issues; OSM enriched)
CREATE TABLE IF NOT EXISTS locations (
    id              SERIAL PRIMARY KEY,
    issue_id        INTEGER UNIQUE REFERENCES issues(id) ON DELETE CASCADE,
    latitude        DECIMAL(10,7) NOT NULL,
    longitude       DECIMAL(10,7) NOT NULL,
    geom            GEOGRAPHY(Point, 4326),
    ward            VARCHAR(100),
    zone            VARCHAR(100),
    city            VARCHAR(100),
    state           VARCHAR(100),
    pincode         VARCHAR(10),
    osm_road_name   VARCHAR(300),
    osm_place_name  VARCHAR(300),
    landmark_type   VARCHAR(100),
    landmark_name   VARCHAR(300),
    risk_score      DECIMAL(5,4) DEFAULT 0.0,
    is_high_risk_zone BOOLEAN DEFAULT FALSE,
    geocoded        BOOLEAN DEFAULT FALSE,
    geocode_source  VARCHAR(50) DEFAULT 'nominatim',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_locations_geom ON locations USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_locations_ward ON locations(ward);

-- Evidence (before/after images, documents)
CREATE TABLE IF NOT EXISTS evidences (
    id              SERIAL PRIMARY KEY,
    issue_id        INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    evidence_type   VARCHAR(30) NOT NULL DEFAULT 'IMAGE_OTHER',
    file_path       VARCHAR(500) NOT NULL,
    thumbnail_path  VARCHAR(500),
    caption         VARCHAR(300),
    uploader_id     INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_evidence_issue ON evidences(issue_id);
CREATE INDEX IF NOT EXISTS idx_evidence_type ON evidences(evidence_type);

-- Resolutions (repair verification records)
CREATE TABLE IF NOT EXISTS resolutions (
    id                  SERIAL PRIMARY KEY,
    issue_id            INTEGER UNIQUE REFERENCES issues(id) ON DELETE CASCADE,
    before_evidence_id  INTEGER REFERENCES evidences(id) ON DELETE SET NULL,
    after_evidence_id   INTEGER REFERENCES evidences(id) ON DELETE SET NULL,
    ssim_score          DECIMAL(5,4),
    edge_reduction      DECIMAL(5,4),
    brightness_delta    INTEGER,
    resolved_probability DECIMAL(5,4),
    verification_status VARCHAR(40) NOT NULL DEFAULT 'pending',
    human_verified      BOOLEAN DEFAULT FALSE,
    verified_by         INTEGER REFERENCES users(id) ON DELETE SET NULL,
    officer_note        TEXT,
    verified_at         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_resolution_status ON resolutions(verification_status);
CREATE INDEX IF NOT EXISTS idx_resolution_issue ON resolutions(issue_id);

-- Duplicate links
CREATE TABLE IF NOT EXISTS duplicate_links (
    id              SERIAL PRIMARY KEY,
    primary_issue_id INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    duplicate_issue_id INTEGER REFERENCES issues(id) ON DELETE CASCADE,
    similarity_score DECIMAL(5,4) NOT NULL,
    detected_by     VARCHAR(30) DEFAULT 'ai',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dup_primary ON duplicate_links(primary_issue_id);
CREATE INDEX IF NOT EXISTS idx_dup_secondary ON duplicate_links(duplicate_issue_id);

-- Hotspot analysis cache
CREATE TABLE IF NOT EXISTS hotspot_cache (
    id              SERIAL PRIMARY KEY,
    centroid_lat    DECIMAL(10,7),
    centroid_lon    DECIMAL(10,7),
    radius_km       DECIMAL(6,3),
    issue_count     INTEGER,
    avg_severity    DECIMAL(5,4),
    top_category    VARCHAR(50),
    ward            VARCHAR(100),
    risk_score      DECIMAL(5,4),
    computed_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Triggers: update `location` geography column when lat/lon changes
CREATE OR REPLACE FUNCTION fn_issue_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.location := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326)::GEOGRAPHY;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_issue_geom ON issues;
CREATE TRIGGER trg_issue_geom
BEFORE INSERT OR UPDATE OF latitude, longitude ON issues
FOR EACH ROW EXECUTE FUNCTION fn_issue_geom();
