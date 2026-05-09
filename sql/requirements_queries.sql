-- Requirement: Top 100 rows from each table
SELECT * FROM breeds LIMIT 100;
SELECT * FROM images LIMIT 100;
SELECT * FROM dataset_split LIMIT 100;
SELECT * FROM bounding_boxes LIMIT 100;

-- Requirement: Join statement for two related tables (top 100)
SELECT
    i.image_id,
    i.relative_path,
    b.breed_name,
    b.synset
FROM images i
JOIN breeds b ON b.breed_id = i.breed_id
ORDER BY i.image_id
LIMIT 100;

-- Requirement: Aggregate summary query
SELECT
    ds.split,
    COUNT(*) AS image_count,
    AVG((bb.xmax - bb.xmin) * (bb.ymax - bb.ymin)) AS avg_bbox_area
FROM dataset_split ds
JOIN images i ON i.image_id = ds.image_id
LEFT JOIN bounding_boxes bb ON bb.image_id = i.image_id
GROUP BY ds.split
ORDER BY ds.split;
