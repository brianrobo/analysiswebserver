--
-- Migration: Add Team Sharing Support for Analysis Results
-- Created: 2026-02-08
-- Description: Adds analysis_sharing table for team collaboration
--

-- Create analysis_sharing table
CREATE TABLE IF NOT EXISTS analysis_sharing (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    team_id INTEGER NOT NULL REFERENCES teams(id) ON DELETE CASCADE,
    shared_by_user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    -- Permission flags
    can_view BOOLEAN NOT NULL DEFAULT TRUE,
    can_download BOOLEAN NOT NULL DEFAULT TRUE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMP NULL,

    -- Prevent duplicate sharing
    UNIQUE(job_id, team_id)
);

-- Create indexes for faster queries
CREATE INDEX idx_analysis_sharing_job_id ON analysis_sharing(job_id);
CREATE INDEX idx_analysis_sharing_team_id ON analysis_sharing(team_id);
CREATE INDEX idx_analysis_sharing_shared_by_user_id ON analysis_sharing(shared_by_user_id);
CREATE INDEX idx_analysis_sharing_expires_at ON analysis_sharing(expires_at) WHERE expires_at IS NOT NULL;

-- Add comments for documentation
COMMENT ON TABLE analysis_sharing IS 'Team sharing records for analysis results';
COMMENT ON COLUMN analysis_sharing.job_id IS 'Analysis job being shared';
COMMENT ON COLUMN analysis_sharing.team_id IS 'Team with whom the analysis is shared';
COMMENT ON COLUMN analysis_sharing.shared_by_user_id IS 'User who shared the analysis';
COMMENT ON COLUMN analysis_sharing.can_view IS 'Permission to view analysis results';
COMMENT ON COLUMN analysis_sharing.can_download IS 'Permission to download results (JSON/CSV/ZIP)';
COMMENT ON COLUMN analysis_sharing.expires_at IS 'Optional expiration timestamp (NULL = no expiration)';

-- Migration complete
-- To run: psql -U postgres -d analysisdb -f migrations/001_add_sharing.sql
