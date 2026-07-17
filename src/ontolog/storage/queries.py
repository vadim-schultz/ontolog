"""SQL statements for SQLite template storage."""

CREATE_SCHEMA = """
PRAGMA user_version = 1;

CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    template TEXT NOT NULL UNIQUE,
    occurrence_count INTEGER NOT NULL,
    first_seen TEXT,
    last_seen TEXT,
    examples TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS template_occurrences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    template_id TEXT NOT NULL REFERENCES templates(id),
    timestamp TEXT,
    message TEXT NOT NULL,
    parameters TEXT NOT NULL,
    process TEXT
);

CREATE INDEX IF NOT EXISTS idx_occurrences_template_id
    ON template_occurrences(template_id);
"""

FIND_TEMPLATE_BY_ID_OR_TEXT = "SELECT * FROM templates WHERE id = ? OR template = ?"

INSERT_TEMPLATE = """
INSERT INTO templates (id, template, occurrence_count, first_seen, last_seen, examples)
VALUES (?, ?, ?, ?, ?, ?)
"""

UPDATE_TEMPLATE = """
UPDATE templates
SET occurrence_count = ?, first_seen = ?, last_seen = ?, examples = ?
WHERE id = ?
"""

INSERT_OCCURRENCE = """
INSERT INTO template_occurrences (template_id, timestamp, message, parameters, process)
VALUES (?, ?, ?, ?, ?)
"""

LIST_TEMPLATES = "SELECT * FROM templates ORDER BY occurrence_count DESC, template ASC"

LIST_OCCURRENCES = """
SELECT template_id, timestamp, message, parameters, process
FROM template_occurrences
ORDER BY timestamp ASC, id ASC
"""

LIST_OCCURRENCES_BY_TEMPLATE = """
SELECT template_id, timestamp, message, parameters, process
FROM template_occurrences
WHERE template_id = ?
ORDER BY timestamp ASC, id ASC
"""

RESOLVE_TEMPLATE_ID = "SELECT id FROM templates WHERE template = ?"

MIGRATE_ADD_PROCESS_COLUMN = """
ALTER TABLE template_occurrences ADD COLUMN process TEXT
"""
