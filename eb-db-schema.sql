-- Enable pgvector extension (Must be run as Superuser usually)
CREATE EXTENSION IF NOT EXISTS vector;


-- --------------------------------------------------------------------------------
-- Table: folder
-- Description: Generic hierarchy container for any source (Drive folders, Notion pages, etc.)
-- --------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS folder (
    id SERIAL PRIMARY KEY,
    
    -- Business Keys
    ext_source_id TEXT NOT NULL, -- The specific ID from the source (e.g., Drive Folder ID)
    source VARCHAR(50) NOT NULL,         -- 'drive', 'notion', 'sharepoint'
    
    -- Hierarchy
    parent_id INTEGER,                   -- Self-referential FK for nesting
    
    -- Core Attributes
    name VARCHAR(255) NOT NULL,
    
    -- Audit & Metadata
    metadata JSONB DEFAULT '{}',         -- Store specific drive fields like 'webViewLink', 'owners' here
    permissions JSONB DEFAULT '[]',      -- Access Control Lists (ACLs)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),
    -- Constraints
    CONSTRAINT uq_folder_source_ext_id UNIQUE (source, ext_source_id),
    CONSTRAINT fk_folder_parent FOREIGN KEY (parent_id) REFERENCES folder(id) ON DELETE SET NULL
);

COMMENT ON TABLE folder IS 'Unified folder structure for all data sources.';
COMMENT ON COLUMN folder.permissions IS 'Stores source-specific access (ACLs), e.g., list of users with read/write access.';

-- --------------------------------------------------------------------------------
-- Table: document
-- Description: Represents a single file/document Uploaded into the system.
-- --------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document (
    id SERIAL PRIMARY KEY,
    
    -- Business Keys
    ext_source_id TEXT, -- External Unique identifier from source (e.g., Google Drive ID)
    source VARCHAR(50) NOT NULL,         -- Origin source: 'drive', 'notion', 'local', etc.
    
    -- Core Attributes
    name VARCHAR(255) NOT NULL,          -- Original filename
    mime_type VARCHAR(100),              -- e.g., 'application/pdf'
    source_url VARCHAR(1024),            -- Web link or local path
    folder_id INTEGER,                  -- FK to generic folder table
    permissions JSONB DEFAULT '[]',      -- Access Control Lists (ACLs)
    
    -- Audit & Metadata (Standard Fields)
    metadata JSONB DEFAULT '{}',         -- Flexible bag for extra attributes (e.g., author, page_count)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),             -- User/System who uploaded it
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE, -- Soft delete support
    deleted_by VARCHAR(255),

    CONSTRAINT uq_document_ext_source_id UNIQUE (ext_source_id),
    CONSTRAINT fk_document_folder FOREIGN KEY (folder_id) REFERENCES folder(id) 
);

COMMENT ON COLUMN document.folder_id IS 'FK to the generic folder table, placing this document in a hierarchy.';
COMMENT ON COLUMN document.permissions IS 'Stores source-specific access (ACLs), e.g., list of users with read/write access.';
COMMENT ON TABLE document IS 'Stores metadata for uploaded files.';
COMMENT ON COLUMN document.ext_source_id IS 'External unique ID from the source system (e.g., Google Drive File ID).';
COMMENT ON COLUMN document.source IS 'The origin system of the document (drive, notion, etc.).';
COMMENT ON COLUMN document.metadata IS 'JSONB field for extra properties like tags, author, verified_status.';

-- --------------------------------------------------------------------------------
-- Table: document_chunk
-- Description: Stores text segments and their vector embeddings.
-- --------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS document_chunk (
    id SERIAL PRIMARY KEY,
    
    -- Foreign Key
    document_id INTEGER NOT NULL,
    
    -- Core Content
    chunk_index INTEGER NOT NULL,        -- Sequential order 0, 1, 2... to reconstruct context
    content TEXT NOT NULL,               -- The actual text segment
    embedding vector(768),               -- 768-dim vector (Gemini Pro / OpenAI v3 small)
    
    -- Audit & Metadata (Standard Fields)
    metadata JSONB DEFAULT '{}',         -- Chunk-level metadata (e.g., page_number)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_document_chunk_document FOREIGN KEY(document_id) REFERENCES document(id) ON DELETE CASCADE
);

COMMENT ON TABLE document_chunk IS 'Stores segmented text and vector embeddings for semantic search.';
COMMENT ON COLUMN document_chunk.chunk_index IS 'Position of the chunk in the original document.';


-- --------------------------------------------------------------------------------
-- AppUser: Stores application users
-- --------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    ext_user_id TEXT,
    email VARCHAR(255),
    display_name VARCHAR(255),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT uq_users_ext_user_id UNIQUE (ext_user_id),
    CONSTRAINT uq_users_email UNIQUE (email)
);

CREATE TABLE IF NOT EXISTS google_account (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    email VARCHAR(255),

    access_token TEXT,
    refresh_token TEXT,
    expiry_time TIMESTAMP WITHOUT TIME ZONE,
    scopes JSONB DEFAULT '[]',
    revoked_at TIMESTAMP WITHOUT TIME ZONE,

    -- Audit & Metadata (Standard Fields)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_google_account_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- --------------------------------------------------------------------------------
-- Chat Space: Stores chat spaces
-- --------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS chat_space (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,

    -- Business Keys
    ext_space_id TEXT NOT NULL,

    display_name VARCHAR(255),
    space_type VARCHAR(50),
    metadata JSONB DEFAULT '{}',

    last_sync_at TIMESTAMP WITHOUT TIME ZONE,
    -- Audit & Metadata (Standard Fields)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_chat_space_account FOREIGN KEY(account_id) REFERENCES google_account(id) ON DELETE CASCADE
);

-- Chat Message: Stores chat messages
-- --------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS chat_message (
    id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL,
    space_id INTEGER NOT NULL,

    -- Business Keys
    ext_message_id TEXT NOT NULL,
    text TEXT,
    vector vector(768),

    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,

    sender JSONB,
    raw JSONB,

    -- Audit & Metadata (Standard Fields)
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_chat_message_account FOREIGN KEY(account_id) REFERENCES google_account(id) ON DELETE CASCADE,
    CONSTRAINT fk_chat_message_space FOREIGN KEY(space_id) REFERENCES chat_space(id) ON DELETE CASCADE
);


-- --------------------------------------------------------------------------------
-- Chat Space Members: maps users to spaces
-- --------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_space_member (
    id SERIAL PRIMARY KEY,
    space_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(50),
    member_type VARCHAR(50), -- e.g., 'HUMAN', 'BOT'
    metadata JSONB DEFAULT '{}',
    
    -- Audit & Metadata (Standard Fields)
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),
    CONSTRAINT fk_member_space FOREIGN KEY(space_id) REFERENCES chat_space(id) ON DELETE CASCADE,
    CONSTRAINT fk_member_user FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_space_user UNIQUE (space_id, user_id)
);

-- --------------------------------------------------------------------------------
-- Gmail: Threads and Messages (Linked to google_account)
-- --------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS gmail_thread (
    id SERIAL PRIMARY KEY,
    
    -- Foreign Key
    account_id INTEGER NOT NULL,            -- Owner Google Account
    
    -- Business Keys
    ext_thread_id TEXT,    -- Gmail Thread ID (External)
    history_id TEXT,                -- Sync History ID
    
    -- Metadata
    snippet VARCHAR(1024),
    metadata JSONB DEFAULT '{}',            -- Flexible fields
    
    -- Audit
    last_sync_at TIMESTAMP WITHOUT TIME ZONE,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_gmail_thread_account 
        FOREIGN KEY(account_id) 
        REFERENCES google_account(id) 
        ON DELETE CASCADE,

    CONSTRAINT uq_gmail_thread_account_thread UNIQUE (account_id, ext_thread_id)
);

CREATE TABLE IF NOT EXISTS gmail_message (
    id SERIAL PRIMARY KEY,
    
    -- Foreign Keys
    account_id INTEGER NOT NULL,
    thread_id INTEGER,                      -- Internal DB ID of the thread
    
    -- Business Keys
    ext_message_id TEXT,   -- Gmail Message ID (External)
    
    -- Email Attributes
    subject VARCHAR(1024),
    sender VARCHAR(255),                    -- From
    recipients JSONB DEFAULT '[]',          -- To, Cc, Bcc list
    snippet TEXT,
    body_text TEXT,                         -- Plain text content
    body_html TEXT,                         -- HTML content (optional)
    
    internal_date TIMESTAMP WITHOUT TIME ZONE, -- Gmail 'internalDate'
    label_ids JSONB DEFAULT '[]',           -- List of label IDs (INBOX, SENT, etc.)

    -- Vector Embedding for Search
    vector vector(768),

    -- Audit
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    created_by VARCHAR(255),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (now() AT TIME ZONE 'utc'),
    updated_by VARCHAR(255),
    deleted_at TIMESTAMP WITHOUT TIME ZONE,
    deleted_by VARCHAR(255),

    CONSTRAINT fk_gmail_message_account 
        FOREIGN KEY(account_id) 
        REFERENCES google_account(id) 
        ON DELETE CASCADE,

    CONSTRAINT fk_gmail_message_thread 
        FOREIGN KEY(thread_id) 
        REFERENCES gmail_thread(id) 
        ON DELETE SET NULL,

    CONSTRAINT uq_gmail_message_account_msg UNIQUE (account_id, ext_message_id)
);

-- Migration Script: Add profile_picture column to users table
-- Date: 2026-01-27
-- Description: Adds profile_picture column to store user's Google profile picture URL

-- Add profile_picture column
ALTER TABLE public.users 
ADD COLUMN IF NOT EXISTS profile_picture VARCHAR(1024);

-- Add comment to the column
COMMENT ON COLUMN public.users.profile_picture IS 'URL to user profile picture from Google or other providers';

-- Verify the change
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'profile_picture';
