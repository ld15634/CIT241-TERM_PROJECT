-- Security requirement (PostgreSQL)
-- SQLite does not support CREATE ROLE or CREATE USER.
-- Run this script in PostgreSQL after creating equivalent tables there.

CREATE ROLE dogs_readonly NOINHERIT;

CREATE USER student_a WITH PASSWORD 'ChangeMe_A1!';
CREATE USER student_b WITH PASSWORD 'ChangeMe_B1!';
CREATE USER student_c WITH PASSWORD 'ChangeMe_C1!';

GRANT dogs_readonly TO student_a;
GRANT dogs_readonly TO student_b;
GRANT dogs_readonly TO student_c;

GRANT USAGE ON SCHEMA public TO dogs_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dogs_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO dogs_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON TABLES TO dogs_readonly;

ALTER DEFAULT PRIVILEGES IN SCHEMA public
GRANT SELECT ON SEQUENCES TO dogs_readonly;

REVOKE INSERT, UPDATE, DELETE, TRUNCATE, REFERENCES, TRIGGER
ON ALL TABLES IN SCHEMA public
FROM dogs_readonly;

REVOKE CREATE ON SCHEMA public FROM dogs_readonly;
