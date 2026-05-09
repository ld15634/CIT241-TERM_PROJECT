-- Active: 1769614827732@@127.0.0.1@3306@stanford_dogs
-- 1) Total number of breeds, images, and bounding boxes.
SELECT
    (SELECT COUNT(*) FROM breeds) AS total_breeds,
    (SELECT COUNT(*) FROM images) AS total_images,
    (SELECT COUNT(*) FROM bounding_boxes) AS total_bounding_boxes;

-- 2) Number of images in train vs test.
SELECT split, COUNT(*) AS image_count
FROM dataset_split
GROUP BY split
ORDER BY split;

-- 3) Top 10 breeds with the most images.
SELECT b.breed_name, b.synset, COUNT(*) AS image_count
FROM images i
JOIN breeds b ON b.breed_id = i.breed_id
GROUP BY b.breed_id
ORDER BY image_count DESC, b.breed_name
LIMIT 10;

-- 4) Average bounding box area by breed (top 10 by area).
SELECT
    b.breed_name,
    AVG((bb.xmax - bb.xmin) * (bb.ymax - bb.ymin)) AS avg_bbox_area
FROM bounding_boxes bb
JOIN images i ON i.image_id = bb.image_id
JOIN breeds b ON b.breed_id = i.breed_id
GROUP BY b.breed_id
ORDER BY avg_bbox_area DESC
LIMIT 10;

-- 5) Breeds where train/test is imbalanced by more than 25 images.
WITH split_counts AS (
    SELECT
        i.breed_id,
        SUM(CASE WHEN ds.split = 'train' THEN 1 ELSE 0 END) AS train_count,
        SUM(CASE WHEN ds.split = 'test' THEN 1 ELSE 0 END) AS test_count
    FROM images i
    JOIN dataset_split ds ON ds.image_id = i.image_id
    GROUP BY i.breed_id
)
SELECT
    b.breed_name,
    s.train_count,
    s.test_count,
    ABS(s.train_count - s.test_count) AS difference
FROM split_counts s
JOIN breeds b ON b.breed_id = s.breed_id
WHERE ABS(s.train_count - s.test_count) > 25
ORDER BY difference DESC, b.breed_name;
