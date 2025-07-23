-- CardPress Blog Database Schema for Cloudflare D1

-- Users table (admin-only, no registration)
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Posts table
CREATE TABLE IF NOT EXISTS posts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT,
    labels TEXT, -- JSON array as string
    colors TEXT,
    column_status TEXT DEFAULT 'ideas', -- ideas, drafting, editing, deployed
    image_url TEXT,
    image_path TEXT, -- R2 storage path
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Index for better query performance
CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_column_status ON posts(column_status);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at);

-- Insert default admin user (password should be hashed in production)
-- Default password: "admin123" (change this!)
INSERT OR IGNORE INTO users (id, email, password_hash, is_admin) 
VALUES (
    'admin-001', 
    'admin@example.com', 
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewJR0Q9HHZL7WZ2u', -- admin123
    1
); 