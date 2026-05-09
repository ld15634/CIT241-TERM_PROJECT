-- SQLite demo runner for course requirements.
-- Usage:
-- sqlite3 stanford_dogs.db ".read sql/run_all.sql"

.read sql/schema.sql
.read sql/views.sql

-- Requirement queries
.read sql/requirements_queries.sql

-- Show top 100 rows from the useful view
SELECT *
FROM vw_breed_dataset_summary
ORDER BY total_images DESC, breed_name
LIMIT 100;
