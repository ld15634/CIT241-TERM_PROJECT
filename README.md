# CIT241-TERM_PROJECT

Database Management term project based on the Stanford Dogs dataset:
http://vision.stanford.edu/aditya86/ImageNetDogs/

## Project Goal

Build a relational database that stores:
- Dog breeds (120 classes)
- Image records (20,580 total)
- Train/test split labels
- Bounding box annotations

The implementation in this repository uses SQLite for portability.

## Files Added

- `sql/schema.sql`: normalized database schema with keys and indexes
- `sql/analysis_queries.sql`: useful project/demo queries
- `scripts/import_stanford_dogs.py`: loader from Stanford Dogs `.mat` and annotation files

## 1) Download and Extract Dataset

From the dataset site, download:
- Images: `images.tar`
- Annotations: `annotation.tar`
- Lists: `lists.tar`

Suggested project structure after extraction:

```
CIT241-TERM_PROJECT/
	data/
		images/...
		annotation/...
		lists/
			train_list.mat
			test_list.mat
			file_list.mat
```

## 2) Install Python Dependencies

The importer needs:
- `scipy`

Install with:

```powershell
pip install scipy
```

## 3) Build the Database

Run from project root:

```powershell
python scripts/import_stanford_dogs.py --dataset-root data --lists-root data/lists --db-path stanford_dogs.db --schema-path sql/schema.sql
```

Expected output is a summary with counts for breeds, images, and bounding boxes.

## 4) Explore the Data

Run queries in `sql/analysis_queries.sql` using any SQLite client, for example:

```powershell
sqlite3 stanford_dogs.db ".read sql/analysis_queries.sql"
```

## Course Requirements Coverage

### Make the Database (DDL)

- Build tables and indexes with `sql/schema.sql`

### Import Data

- Import Stanford Dogs data with `scripts/import_stanford_dogs.py`
- Command:

```powershell
python scripts/import_stanford_dogs.py --dataset-root data --lists-root data/lists --db-path stanford_dogs.db --schema-path sql/schema.sql
```

### Queries

- Top 100 rows from each table: `sql/requirements_queries.sql`
- Join top 100 from two related tables: `sql/requirements_queries.sql`
- Aggregate summary query: `sql/requirements_queries.sql`

Run:

```powershell
sqlite3 stanford_dogs.db ".read sql/requirements_queries.sql"
```

### View

- View definition: `sql/views.sql` (`vw_breed_dataset_summary`)

Run:

```powershell
sqlite3 stanford_dogs.db ".read sql/views.sql"
```

### Security

- Role + users with SELECT-only access: `sql/security_postgresql.sql`
- Note: SQLite does not support users/roles. This requirement is implemented for PostgreSQL syntax.

## One-Command Demo (SQLite)

After importing data, run all core requirement SQL in one command:

```powershell
sqlite3 stanford_dogs.db ".read sql/run_all.sql"
```

This runs:
- schema creation (`sql/schema.sql`)
- view creation (`sql/views.sql`)
- requirement queries (`sql/requirements_queries.sql`)

## One-Command Demo (PostgreSQL)

Run all core requirement SQL plus security in one command:

```powershell
psql -U <user> -d <database> -f sql/run_all_postgresql.sql
```

This runs:
- schema creation (`sql/schema_postgresql.sql`)
- view creation (`sql/views.sql`)
- requirement queries (`sql/requirements_queries.sql`)
- security role/user permissions (`sql/security_postgresql.sql`)

## MySQL Scripts (For Existing stanford_dogs Server DB)

If you are using a MySQL database named `stanford_dogs`, use:
- `sql/schema_mysql.sql`
- `sql/views_mysql.sql`
- `sql/security_mysql.sql`

## Schema Overview

- `breeds`: one row per dog breed/synset
- `images`: one row per image, linked to breed
- `dataset_split`: train/test assignment per image
- `bounding_boxes`: one or more boxes per image

This design supports analytical queries and can be extended with feature vectors later if needed.
