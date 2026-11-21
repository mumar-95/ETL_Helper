PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS scenarios (
    id TEXT PRIMARY KEY,
    technology TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    years_min INTEGER NOT NULL DEFAULT 0,
    years_max INTEGER NOT NULL DEFAULT 20,
    title TEXT NOT NULL,
    stem TEXT NOT NULL,
    iics_service_scope TEXT,
    label TEXT NOT NULL DEFAULT 'ai_generated',
    status TEXT NOT NULL DEFAULT 'draft',
    tags TEXT NOT NULL DEFAULT '[]',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    content_hash TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_scenarios_tech ON scenarios(technology);
CREATE INDEX IF NOT EXISTS idx_scenarios_category ON scenarios(category);
CREATE INDEX IF NOT EXISTS idx_scenarios_difficulty ON scenarios(difficulty);
CREATE INDEX IF NOT EXISTS idx_scenarios_status ON scenarios(status);
CREATE INDEX IF NOT EXISTS idx_scenarios_label ON scenarios(label);

CREATE TABLE IF NOT EXISTS explanations (
    scenario_id TEXT PRIMARY KEY REFERENCES scenarios(id) ON DELETE CASCADE,
    section_a TEXT NOT NULL,
    section_b TEXT NOT NULL,
    section_c TEXT NOT NULL,
    section_d TEXT NOT NULL,
    section_e TEXT NOT NULL,
    section_f TEXT NOT NULL,
    section_g TEXT NOT NULL,
    section_h TEXT NOT NULL,
    section_i TEXT NOT NULL,
    section_j TEXT NOT NULL,
    section_k TEXT NOT NULL,
    section_l TEXT NOT NULL,
    section_m TEXT NOT NULL,
    sample_input_json TEXT,
    expected_output_json TEXT,
    mapping_flow_ascii TEXT,
    mapping_flow_mermaid TEXT,
    sql_logic TEXT,
    interview_answer TEXT,
    has_sample_data INTEGER NOT NULL DEFAULT 0,
    has_alternatives INTEGER NOT NULL DEFAULT 0,
    has_followups INTEGER NOT NULL DEFAULT 0,
    word_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS followup_questions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    ordinal INTEGER NOT NULL,
    question TEXT NOT NULL,
    difficulty_step TEXT NOT NULL DEFAULT 'intermediate',
    UNIQUE(scenario_id, ordinal)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    scenario_id TEXT NOT NULL REFERENCES scenarios(id) ON DELETE CASCADE,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_chat_session ON chat_messages(session_id, scenario_id);

CREATE TABLE IF NOT EXISTS generation_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scenario_id TEXT,
    technology TEXT NOT NULL,
    category TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    title TEXT NOT NULL,
    stem TEXT NOT NULL,
    payload_json TEXT,
    dedup_score REAL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    reviewed_at TEXT
);
