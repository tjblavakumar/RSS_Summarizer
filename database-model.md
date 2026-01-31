# Database Model - Entity Relationship Diagram

## Tables

### Feed
**Purpose:** Stores RSS feed sources

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Feed display name |
| url | VARCHAR(500) | NOT NULL, UNIQUE | RSS feed URL |
| active | BOOLEAN | DEFAULT TRUE | Enable/disable feed |
| access_key | VARCHAR(500) | NULL | API key for protected feeds |

---

### Category
**Purpose:** Organizes articles into categories

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Category name |
| description | TEXT | NULL | Category description |
| color | VARCHAR(7) | DEFAULT '#007bff' | Hex color code |
| active | BOOLEAN | DEFAULT TRUE | Enable/disable category |

---

### Topic
**Purpose:** Defines keywords for article matching

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| name | VARCHAR(100) | NOT NULL, UNIQUE | Topic name |
| keywords | TEXT | NOT NULL | Comma-separated keywords |
| category_id | INTEGER | FOREIGN KEY → categories.id | Parent category |
| active | BOOLEAN | DEFAULT TRUE | Enable/disable topic |

---

### Article
**Purpose:** Stores processed news articles

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | INTEGER | PRIMARY KEY | Unique identifier |
| title | VARCHAR(500) | NOT NULL | Article title |
| url | VARCHAR(1000) | NOT NULL, UNIQUE | Article URL |
| content | TEXT | NULL | Full article content |
| summary | TEXT | NULL | AI-generated summary |
| author | VARCHAR(200) | NULL | Article author |
| relevancy_score | INTEGER | NULL | AI relevancy score (0-100) |
| topic_scores | JSON | NULL | Scores per topic |
| feed_id | INTEGER | FOREIGN KEY → feeds.id | Source feed |
| topic_id | INTEGER | FOREIGN KEY → topics.id | Matched topic |
| published_date | DATETIME | NULL | Original publish date |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | Record creation time |
| category_name | VARCHAR(100) | NULL | Matched category |
| category_color | VARCHAR(7) | NULL | Category color |
| user_feedback | INTEGER | DEFAULT 0 | User rating (1=like, -1=dislike) |
| rss_metadata | JSON | NULL | Original RSS metadata |

---

### SystemConfig
**Purpose:** Stores system configuration

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| key | VARCHAR(100) | PRIMARY KEY | Config key |
| value | TEXT | NULL | Config value |
| description | TEXT | NULL | Config description |

---

## Relationships

```
Feed (1) ──────< (N) Article
  │
  └─ One feed can have many articles

Category (1) ──────< (N) Topic
  │
  └─ One category can have many topics

Topic (1) ──────< (N) Article
  │
  └─ One topic can match many articles

Article (N) >────── (1) Feed
  │
  └─ Each article belongs to one feed

Article (N) >────── (1) Topic
  │
  └─ Each article matches one primary topic
```

---

## ER Diagram (ASCII)

```
┌─────────────────┐
│      Feed       │
├─────────────────┤
│ PK  id          │
│     name        │
│     url         │
│     active      │
│     access_key  │
└────────┬────────┘
         │
         │ 1:N
         │
         ▼
┌─────────────────────────┐
│       Article           │
├─────────────────────────┤
│ PK  id                  │
│     title               │
│     url                 │
│     content             │
│     summary             │
│     author              │
│     relevancy_score     │
│     topic_scores        │
│ FK  feed_id             │◄────┐
│ FK  topic_id            │     │
│     published_date      │     │
│     created_at          │     │
│     category_name       │     │
│     category_color      │     │
│     user_feedback       │     │
│     rss_metadata        │     │
└─────────────────────────┘     │
         ▲                       │
         │                       │
         │ N:1                   │
         │                       │
┌────────┴────────┐              │
│     Topic       │              │
├─────────────────┤              │
│ PK  id          │              │
│     name        │              │
│     keywords    │              │
│ FK  category_id │              │
│     active      │              │
└────────┬────────┘              │
         │                       │
         │ N:1                   │
         │                       │
         ▼                       │
┌─────────────────┐              │
│    Category     │              │
├─────────────────┤              │
│ PK  id          │              │
│     name        │              │
│     description │              │
│     color       │              │
│     active      │              │
└─────────────────┘              │
                                 │
┌─────────────────┐              │
│  SystemConfig   │              │
├─────────────────┤              │
│ PK  key         │              │
│     value       │              │
│     description │              │
└─────────────────┘              │
                                 │
         (Feed 1:N relationship)─┘
```

---

## Key Constraints

### Primary Keys
- All tables have auto-incrementing integer primary keys
- SystemConfig uses string key as primary key

### Foreign Keys
- `Article.feed_id` → `Feed.id`
- `Article.topic_id` → `Topic.id`
- `Topic.category_id` → `Category.id`

### Unique Constraints
- `Feed.name` - No duplicate feed names
- `Feed.url` - No duplicate feed URLs
- `Article.url` - No duplicate articles
- `Category.name` - No duplicate categories
- `Topic.name` - No duplicate topics

### Indexes (Recommended)
- `Article.url` - Fast duplicate checking
- `Article.created_at` - Efficient cleanup queries
- `Article.feed_id` - Fast feed-based queries
- `Article.category_name` - Category filtering
- `Article.relevancy_score` - Score-based filtering

---

## Data Flow

1. **Feed Management**: Admin adds RSS feeds to `Feed` table
2. **Category Setup**: Admin creates categories in `Category` table
3. **Topic Definition**: Admin defines topics with keywords in `Topic` table
4. **Article Processing**:
   - System fetches RSS entries from active feeds
   - AI analyzes content against all categories
   - Articles with relevancy_score ≥ 75 are saved to `Article` table
   - Foreign keys link to source feed and matched topic
5. **User Interaction**: Users view articles and provide feedback via `user_feedback`
6. **Cleanup**: Articles older than 24 hours are automatically deleted

---

## Sample Queries

### Get all articles for a category
```sql
SELECT * FROM articles 
WHERE category_name = 'Technology' 
ORDER BY created_at DESC;
```

### Get articles from specific feed
```sql
SELECT a.*, f.name as feed_name 
FROM articles a 
JOIN feeds f ON a.feed_id = f.id 
WHERE f.id = 1;
```

### Get high-relevancy articles
```sql
SELECT * FROM articles 
WHERE relevancy_score >= 85 
ORDER BY relevancy_score DESC;
```

### Cleanup old articles
```sql
DELETE FROM articles 
WHERE created_at < datetime('now', '-24 hours');
```

### Get articles by topic
```sql
SELECT a.*, t.name as topic_name 
FROM articles a 
JOIN topics t ON a.topic_id = t.id 
WHERE t.name = 'AI';
```

---
