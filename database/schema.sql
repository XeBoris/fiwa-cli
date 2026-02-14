-- Projects table
CREATE TABLE IF NOT EXISTS pstand_projects
(
    project_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL,
    currency_main VARCHAR(3),
    currency_list TEXT,  -- Store as JSON string
    project_hash VARCHAR(64) NOT NULL UNIQUE
);

-- Users table
CREATE TABLE IF NOT EXISTS pstand_users
(
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    birthday DATE,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    activated BOOLEAN DEFAULT 1,
    is_superuser BOOLEAN DEFAULT 0,
    scope VARCHAR(255) DEFAULT 'user:write',
    max_projects INTEGER DEFAULT 3,
    unique_identifier VARCHAR(36) NOT NULL,
    UNIQUE (email)
);

-- User-Project mapping table
CREATE TABLE IF NOT EXISTS pstand_user_project_map
(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES pstand_users (user_id),
    project_id INTEGER REFERENCES pstand_projects (project_id),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    project_perm_model VARCHAR(6) DEFAULT '000000',
    project_primary BOOLEAN DEFAULT 0,
    excluded_tags TEXT  -- Store as JSON string
);

-- Items table
CREATE TABLE IF NOT EXISTS pstand_items
(
    item_id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_uuid VARCHAR(36) NOT NULL,
    name VARCHAR(64) NOT NULL,
    note VARCHAR(255) DEFAULT '',
    price DECIMAL NOT NULL,
    price_final DECIMAL NOT NULL,
    currency VARCHAR(3) NOT NULL,
    currency_final VARCHAR(3) NOT NULL,
    bought_date TIMESTAMP NOT NULL,
    bought_by_id INTEGER NOT NULL REFERENCES pstand_users (user_id),
    bought_for_id INTEGER NOT NULL REFERENCES pstand_users (user_id),
    added_by_id INTEGER NOT NULL REFERENCES pstand_users (user_id),
    project_id INTEGER NOT NULL REFERENCES pstand_projects (project_id),
    exchange_rate DECIMAL NOT NULL DEFAULT 1.0,
    exchange_rate_date DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tags TEXT NOT NULL,  -- Store as JSON string
    UNIQUE (item_uuid, item_id)
);

-- Labels table
CREATE TABLE IF NOT EXISTS pstand_labels
(
    label_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(36) NOT NULL,
    description VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    project_id INTEGER NOT NULL REFERENCES pstand_projects (project_id),
    composite TEXT NOT NULL,  -- Store as JSON string
    label_status INTEGER DEFAULT 2,
    label_type INTEGER DEFAULT 1,
    UNIQUE (name, project_id)
);

-- Session table
CREATE TABLE IF NOT EXISTS pstand_session_table
(
    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES pstand_users (user_id),
    session_start TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    session_uuid VARCHAR(255) NOT NULL,
    session_type VARCHAR(255) NOT NULL,
    session_storage TEXT,  -- Store as JSON string
    UNIQUE (user_id, session_id)
);

-- Register table
CREATE TABLE IF NOT EXISTS pstand_register
(
    register_id INTEGER PRIMARY KEY AUTOINCREMENT,
    register_token VARCHAR(36) NOT NULL,
    register_status INTEGER NOT NULL,
    register_created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    register_expires TIMESTAMP NOT NULL,
    UNIQUE (register_token)
);

-- Aggregates table
CREATE TABLE IF NOT EXISTS pstand_aggregates
(
    aggregate_id INTEGER PRIMARY KEY AUTOINCREMENT,
    aggregate_uuid VARCHAR(36) NOT NULL,
    user_id INTEGER NOT NULL REFERENCES pstand_users (user_id),
    project_id INTEGER NOT NULL REFERENCES pstand_projects (project_id),
    begin DATE NOT NULL,
    interval_seconds INTEGER NOT NULL,
    aggregate_type INTEGER NOT NULL,
    aggregate_name VARCHAR(24) NOT NULL,
    aggregate_description VARCHAR(255) NOT NULL,
    aggregate_info TEXT  -- Store as JSON string
);
