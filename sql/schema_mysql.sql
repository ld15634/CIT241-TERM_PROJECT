CREATE TABLE IF NOT EXISTS breeds (
    breed_id INT AUTO_INCREMENT PRIMARY KEY,
    class_label INT UNIQUE,
    synset VARCHAR(64) NOT NULL UNIQUE,
    breed_name VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS images (
    image_id INT AUTO_INCREMENT PRIMARY KEY,
    breed_id INT NOT NULL,
    relative_path VARCHAR(512) NOT NULL UNIQUE,
    file_name VARCHAR(255) NOT NULL,
    width INT,
    height INT,
    CONSTRAINT fk_images_breed FOREIGN KEY (breed_id) REFERENCES breeds (breed_id)
);

CREATE TABLE IF NOT EXISTS dataset_split (
    image_id INT PRIMARY KEY,
    split ENUM('train', 'test') NOT NULL,
    list_label INT,
    CONSTRAINT fk_split_image FOREIGN KEY (image_id) REFERENCES images (image_id)
);

CREATE TABLE IF NOT EXISTS bounding_boxes (
    bbox_id INT AUTO_INCREMENT PRIMARY KEY,
    image_id INT NOT NULL,
    xmin INT NOT NULL,
    ymin INT NOT NULL,
    xmax INT NOT NULL,
    ymax INT NOT NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'annotation',
    CONSTRAINT fk_bbox_image FOREIGN KEY (image_id) REFERENCES images (image_id)
);

CREATE INDEX idx_images_breed_id ON images (breed_id);
CREATE INDEX idx_split_split ON dataset_split (split);
CREATE INDEX idx_bbox_image_id ON bounding_boxes (image_id);
