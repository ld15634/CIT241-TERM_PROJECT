-- MySQL security script: role with SELECT-only access.
CREATE ROLE IF NOT EXISTS dogs_readonly;

CREATE USER IF NOT EXISTS 'student_a'@'localhost' IDENTIFIED BY 'ChangeMe_A1!';
CREATE USER IF NOT EXISTS 'student_b'@'localhost' IDENTIFIED BY 'ChangeMe_B1!';
CREATE USER IF NOT EXISTS 'student_c'@'localhost' IDENTIFIED BY 'ChangeMe_C1!';

GRANT dogs_readonly TO 'student_a'@'localhost';
GRANT dogs_readonly TO 'student_b'@'localhost';
GRANT dogs_readonly TO 'student_c'@'localhost';

GRANT SELECT ON stanford_dogs.* TO dogs_readonly;

REVOKE INSERT, UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES
ON stanford_dogs.* FROM dogs_readonly;

SET DEFAULT ROLE dogs_readonly FOR 'student_a'@'localhost';
SET DEFAULT ROLE dogs_readonly FOR 'student_b'@'localhost';
SET DEFAULT ROLE dogs_readonly FOR 'student_c'@'localhost';
