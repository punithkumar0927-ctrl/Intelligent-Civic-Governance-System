-- Apply once to an existing PostgreSQL database before deploying this version.
-- New databases receive these values from SQLAlchemy metadata automatically.
ALTER TYPE issuestatus ADD VALUE IF NOT EXISTS 'resolution_submitted';
ALTER TYPE issuestatus ADD VALUE IF NOT EXISTS 'verified_resolved';
