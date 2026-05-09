-- PostgreSQL demo runner for course requirements.
-- Usage (from project root):
-- psql -U <user> -d <database> -f sql/run_all_postgresql.sql

\i sql/schema_postgresql.sql
\i sql/views.sql
\i sql/requirements_queries.sql
\i sql/security_postgresql.sql

-- Show top 100 rows from the useful view
SELECT *
FROM vw_breed_dataset_summary
ORDER BY total_images DESC, breed_name
LIMIT 100;
