CREATE_EMAILS_TABLE = """
CREATE TABLE IF NOT EXISTS emails (
    id TEXT PRIMARY KEY,
    subject TEXT,
    sender TEXT,
    date DATETIME,
    snippet TEXT,
    body TEXT,
    processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_TWEETS_TABLE = """
CREATE TABLE IF NOT EXISTS tweets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    concept_id TEXT,
    tweet_text TEXT,
    source_type TEXT CHECK(source_type IN ('concept', 'external')) NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    publish_date DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (concept_id) REFERENCES concepts (id)
);
"""

CREATE_CONCEPTS_TABLE = """
CREATE TABLE IF NOT EXISTS concepts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    concept_text TEXT NOT NULL,
    keywords TEXT,
    links TEXT,
    times_referenced INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chroma_id TEXT UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_EMAIL_CONCEPTS_TABLE = """
CREATE TABLE IF NOT EXISTS email_concepts (
    email_id TEXT,
    concept_id INTEGER,
    relevance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (email_id, concept_id),
    FOREIGN KEY (email_id) REFERENCES emails (id),
    FOREIGN KEY (concept_id) REFERENCES concepts (id)
);
"""

CREATE_TWEETS_CONCEPTS_TABLE = """
CREATE TABLE IF NOT EXISTS tweets_concepts (
    tweet_id INTEGER,
    concept_id INTEGER,
    PRIMARY KEY (tweet_id, concept_id),
    FOREIGN KEY (tweet_id) REFERENCES tweets (id),
    FOREIGN KEY (concept_id) REFERENCES concepts (id)
);
"""

INSERT_EMAIL = """
INSERT INTO emails (id, subject, sender, date, snippet, body)
VALUES (?, ?, ?, ?, ?, ?);
"""

SELECT_UNPROCESSED_EMAILS = """
SELECT * FROM emails WHERE processed = FALSE;
"""

MARK_EMAIL_AS_PROCESSED = """
UPDATE emails SET processed = TRUE WHERE id = ?;
"""

LOOK_FOR_EMAIL_BY_ID = """
SELECT id FROM emails WHERE id = ?;
"""

INSERT_CONCEPT = """
INSERT INTO concepts (title, concept_text, keywords, links, chroma_id)
VALUES (?, ?, ?, ?, ?);
"""

INSERT_EMAIL_CONCEPT = """
INSERT INTO email_concepts (email_id, concept_id, relevance)
VALUES (?, ?, ?);
"""

UPDATE_CONCEPT_REFERENCE_COUNT = """
UPDATE concepts 
SET times_referenced = times_referenced + 1,
    updated_at = CURRENT_TIMESTAMP
WHERE id = ?;
"""

INSERT_TWEET = """
INSERT INTO tweets (concept_id, tweet_text, source_type, published, publish_date)
VALUES (?, ?, ?, TRUE, CURRENT_TIMESTAMP);
"""

LINK_TWEET_TO_CONCEPT = """
INSERT INTO tweets_concepts (tweet_id, concept_id)
VALUES (?, ?);
"""

GET_RECENT_CONCEPTS = """
SELECT id, title, concept_text, keywords
FROM concepts 
WHERE date(updated_at) >= date('now', '-1 day')
ORDER BY times_referenced DESC;
"""

GET_UNUSED_CONCEPTS_FOR_TWEETS = """
SELECT DISTINCT c.id, c.title, c.concept_text, c.keywords, c.links, c.chroma_id
FROM concepts c
LEFT JOIN tweets_concepts tc ON c.id = tc.concept_id
WHERE tc.concept_id IS NULL
AND date(c.updated_at) >= date('now', '-{days_before} day')
ORDER BY c.times_referenced DESC;
"""

UPDATE_CONCEPT_LINKS = """
UPDATE concepts SET links = ? WHERE id = ?;
"""