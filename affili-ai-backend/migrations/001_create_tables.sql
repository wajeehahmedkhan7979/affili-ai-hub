-- Initial schema for AFFILI-AI backend
-- PostgreSQL/Supabase compatible

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. Tenants table
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    legal_hold BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users table (scoped to tenant)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'VIEWER',
    hashed_password VARCHAR(255),
    refresh_token_version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uix_tenant_email UNIQUE (tenant_id, email)
);

-- 3. Programs table
CREATE TABLE IF NOT EXISTS programs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_url VARCHAR(500),
    signup_url VARCHAR(500),
    affiliate_url VARCHAR(500),
    source VARCHAR(50) DEFAULT 'manual',
    confidence_score FLOAT,
    commission_rate FLOAT DEFAULT 0.0,
    terms TEXT,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_programs_tenant_active ON programs(tenant_id, is_active);
CREATE INDEX idx_programs_name ON programs(name);

-- 4. Applications table
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    program_id UUID NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
    user_email VARCHAR(255) NOT NULL,
    user_data TEXT,
    status VARCHAR(50) DEFAULT 'PENDING',
    agent_status VARCHAR(50) DEFAULT 'IDLE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_applications_tenant_status ON applications(tenant_id, status);

-- 5. Tasks table (agent queue)
CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    task_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'PENDING',
    payload JSONB,
    result JSONB,
    agent_id VARCHAR(255),
    agent_pool VARCHAR(100) DEFAULT 'default',
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    logs TEXT,
    screenshot_url VARCHAR(500),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    claimed_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    last_heartbeat TIMESTAMP
);

CREATE INDEX idx_tasks_tenant_status ON tasks(tenant_id, status);
CREATE INDEX idx_tasks_pool_status ON tasks(agent_pool, status);

-- 6. Response Pool table (Q&A)
CREATE TABLE IF NOT EXISTS response_pool (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    category VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_response_pool_tenant ON response_pool(tenant_id);

-- 7. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    actor_type VARCHAR(50) NOT NULL,
    actor_id VARCHAR(255),
    actor_email VARCHAR(255),
    resource_type VARCHAR(100),
    resource_id VARCHAR(255),
    details JSONB,
    ip_address VARCHAR(50),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 8. Agents table (reputation)
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(255) PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    pool VARCHAR(100) DEFAULT 'default',
    total_tasks INTEGER DEFAULT 0,
    successful_tasks INTEGER DEFAULT 0,
    failed_tasks INTEGER DEFAULT 0,
    captcha_count INTEGER DEFAULT 0,
    timeout_count INTEGER DEFAULT 0,
    health_score FLOAT DEFAULT 100.0,
    last_seen TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bootstrap Data
INSERT INTO tenants (id, name) 
VALUES ('00000000-0000-0000-0000-000000000000', 'Default Tenant')
ON CONFLICT (id) DO NOTHING;

INSERT INTO users (id, tenant_id, email, role, is_active)
VALUES ('ffffffff-ffff-ffff-ffff-ffffffffffff', '00000000-0000-0000-0000-000000000000', 'admin@affili-ai.internal', 'OWNER', true)
ON CONFLICT (id) DO NOTHING;
