CREATE TABLE IF NOT EXISTS breeds (
    breed_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    class_label INTEGER UNIQUE,
    synset TEXT NOT NULL UNIQUE,
    breed_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS images (
    image_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    breed_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    width INTEGER,
    height INTEGER,
    CONSTRAINT fk_images_breed
        FOREIGN KEY (breed_id) REFERENCES breeds (breed_id)
);

CREATE TABLE IF NOT EXISTS dataset_split (
    image_id INTEGER PRIMARY KEY,
    split TEXT NOT NULL CHECK (split IN ('train', 'test')),
    list_label INTEGER,
    CONSTRAINT fk_split_image
        FOREIGN KEY (image_id) REFERENCES images (image_id)
);

CREATE TABLE IF NOT EXISTS bounding_boxes (
    bbox_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    image_id INTEGER NOT NULL,
    xmin INTEGER NOT NULL,
    ymin INTEGER NOT NULL,
    xmax INTEGER NOT NULL,
    ymax INTEGER NOT NULL,
    source TEXT NOT NULL DEFAULT 'annotation',
    CONSTRAINT fk_bbox_image
        FOREIGN KEY (image_id) REFERENCES images (image_id)
);

CREATE INDEX IF NOT EXISTS idx_images_breed_id ON images (breed_id);
CREATE INDEX IF NOT EXISTS idx_split_split ON dataset_split (split);
CREATE INDEX IF NOT EXISTS idx_bbox_image_id ON bounding_boxes (image_id);
