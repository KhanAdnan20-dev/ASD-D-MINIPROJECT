CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS poi (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE PRECISION NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    location geometry(Point, 4326)
        GENERATED ALWAYS AS (
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
        ) STORED
);

CREATE INDEX IF NOT EXISTS poi_location_gist_idx
    ON poi USING GIST (location);

-- Synthetic demonstration data around Bandra, Mumbai; no external POI source.
INSERT INTO poi (name, category, latitude, longitude)
VALUES
    ('Bandra Wellness Pharmacy', 'pharmacy', 19.0556, 72.8295),
    ('Hill Road Delicacies Cafe', 'restaurant', 19.0544, 72.8292),
    ('Lilavati Healthcare Center', 'hospital', 19.0509, 72.8291),
    ('Carter Road Fresh Grocers', 'grocery', 19.0689, 72.8223)
ON CONFLICT (name) DO NOTHING;