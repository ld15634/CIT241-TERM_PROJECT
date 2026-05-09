CREATE OR REPLACE VIEW vw_breed_dataset_summary AS
SELECT
    b.breed_id,
    b.class_label,
    b.synset,
    b.breed_name,
    COUNT(DISTINCT i.image_id) AS total_images,
    SUM(CASE WHEN ds.split = 'train' THEN 1 ELSE 0 END) AS train_images,
    SUM(CASE WHEN ds.split = 'test' THEN 1 ELSE 0 END) AS test_images,
    COUNT(bb.bbox_id) AS total_bounding_boxes,
    ROUND(AVG((bb.xmax - bb.xmin) * (bb.ymax - bb.ymin)), 2) AS avg_bbox_area
FROM breeds b
LEFT JOIN images i ON i.breed_id = b.breed_id
LEFT JOIN dataset_split ds ON ds.image_id = i.image_id
LEFT JOIN bounding_boxes bb ON bb.image_id = i.image_id
GROUP BY b.breed_id, b.class_label, b.synset, b.breed_name;
