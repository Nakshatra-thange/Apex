-- Enable the pgcrypto extension to generate UUIDs
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =================================================================
-- Table: users
-- Purpose: Stores core user information, authentication, and status.
-- =================================================================
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user', -- e.g., 'user', 'admin'
    subscription_tier VARCHAR(50) NOT NULL DEFAULT 'free', -- e.g., 'free', 'premium', 'enterprise'
    status VARCHAR(50) NOT NULL DEFAULT 'pending_verification', -- e.g., 'pending_verification', 'active', 'suspended'
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Index for faster email lookups
CREATE INDEX idx_users_email ON users(email);


-- =================================================================
-- Table: projects
-- Purpose: Organizes code snippets into logical groups for users.
-- =================================================================
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    settings JSONB, -- For future-proofing, e.g., custom review rules
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Index for faster project lookups by owner
CREATE INDEX idx_projects_owner_id ON projects(owner_id);


-- =================================================================
-- Table: code_snippets
-- Purpose: Stores the actual code content submitted for review.
-- =================================================================
CREATE TABLE code_snippets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    filename VARCHAR(255),
    content TEXT NOT NULL,
    language VARCHAR(50),
    hash VARCHAR(64) NOT NULL, -- SHA-256 hash of the content for caching
    file_size_bytes INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Index for caching checks and faster lookups by project
CREATE INDEX idx_code_snippets_project_id ON code_snippets(project_id);
CREATE INDEX idx_code_snippets_hash ON code_snippets(hash);


-- =================================================================
-- Table: reviews
-- Purpose: Tracks the status and results of each code review job.
-- =================================================================
CREATE TABLE reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code_snippet_id UUID NOT NULL REFERENCES code_snippets(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'queued', -- e.g., 'queued', 'parsing', 'analyzing_security', 'completed', 'failed'
    priority INTEGER NOT NULL DEFAULT 10, -- Lower number = higher priority
    progress_stage VARCHAR(50), -- Mirrors the status for multi-stage feedback
    results JSONB, -- Stores the final structured review from the AI
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);
-- Index for faster review lookups by snippet
CREATE INDEX idx_reviews_code_snippet_id ON reviews(code_snippet_id);


-- =================================================================
-- Table: refresh_tokens
-- Purpose: Securely stores refresh tokens for persistent sessions.
-- =================================================================
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) UNIQUE NOT NULL, -- Hashed version of the token for security
    device_info VARCHAR(255), -- User-Agent string or similar identifier
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Index for quick token validation and user session lookups
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);


-- =================================================================
-- Table: rate_limits
-- Purpose: Persists usage data for tracking quotas over long windows.
-- Note: Real-time rate limiting should be handled in Redis for performance.
-- =================================================================
CREATE TABLE rate_limits (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    endpoint VARCHAR(255) NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    window_start TIMESTAMPTZ NOT NULL,
    tier_limit INTEGER NOT NULL
);
-- Composite index for efficient quota checks for a user on a specific endpoint
CREATE INDEX idx_rate_limits_user_endpoint_window ON rate_limits(user_id, endpoint, window_start);


-- =================================================================
-- Table: audit_logs
-- Purpose: Records significant events for security and monitoring.
-- =================================================================
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE SET NULL, -- Keep log even if user is deleted
    action VARCHAR(100) NOT NULL, -- e.g., 'USER_LOGIN', 'PROJECT_CREATE', 'REVIEW_FAILED'
    resource_type VARCHAR(50), -- e.g., 'project', 'user', 'review'
    resource_id UUID,
    ip_address INET,
    details JSONB, -- Additional context about the event
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
-- Indexes for querying logs by user or action
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
