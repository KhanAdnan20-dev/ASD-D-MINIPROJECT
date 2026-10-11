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

-- Curated Mumbai Transit Corridor Dataset across 8 Key Categories
INSERT INTO poi (name, category, latitude, longitude)
VALUES
    -- ── Foundation Seed Points (Bandra) ──
    ('Bandra Wellness Pharmacy', 'pharmacy', 19.0556, 72.8295),
    ('Hill Road Delicacies Cafe', 'restaurant', 19.0544, 72.8292),
    ('Lilavati Healthcare Center', 'hospital', 19.0509, 72.8291),
    ('Carter Road Fresh Grocers', 'grocery', 19.0689, 72.8223),

    -- ── Pharmacies & Chemists ──
    ('Wellness Forever 24/7 Bandra', 'pharmacy', 19.0558, 72.8302),
    ('Noble Plus Chemist Dadar TT', 'pharmacy', 19.0178, 72.8478),
    ('Apollo Pharmacy Andheri West', 'pharmacy', 19.1197, 72.8464),
    ('Frank Ross Pharmacy Fort', 'pharmacy', 18.9322, 72.8335),
    ('MedPlus Pharmacy Chembur East', 'pharmacy', 19.0622, 72.8998),
    ('Wellness Forever Juhu Tara Road', 'pharmacy', 19.0883, 72.8262),
    ('Health & Glow Chemist Ghatkopar', 'pharmacy', 19.0998, 72.9165),
    ('Bandra Medical Stores Hill Road', 'pharmacy', 19.0548, 72.8290),
    ('Lifeline Chemist Goregaon West', 'pharmacy', 19.1645, 72.8492),
    ('Dhanvantari Medical Borivali West', 'pharmacy', 19.2312, 72.8567),
    ('Apollo Pharmacy Lower Parel', 'pharmacy', 18.9954, 72.8272),
    ('Wadala Medical Store', 'pharmacy', 19.0234, 72.8689),

    -- ── Hospitals & Healthcare Centers ──
    ('Lilavati Hospital & Research Centre', 'hospital', 19.0515, 72.8288),
    ('P.D. Hinduja Hospital Mahim', 'hospital', 19.0330, 72.8384),
    ('KEM Hospital Parel', 'hospital', 19.0033, 72.8423),
    ('Bombay Hospital Marine Lines', 'hospital', 18.9388, 72.8282),
    ('Nanavati Max Super Speciality Hospital Vile Parle', 'hospital', 19.0968, 72.8412),
    ('Kokilaben Dhirubhai Ambani Hospital Andheri', 'hospital', 19.1314, 72.8252),
    ('Fortis Hospital Mulund', 'hospital', 19.1624, 72.9431),
    ('Asian Heart Institute BKC', 'hospital', 19.0662, 72.8683),
    ('Hiranandani Hospital Powai', 'hospital', 19.1192, 72.9098),
    ('S.L. Raheja Hospital Mahim', 'hospital', 19.0435, 72.8432),
    ('Tata Memorial Hospital Parel', 'hospital', 19.0051, 72.8435),
    ('Bhatia Hospital Tardeo', 'hospital', 18.9662, 72.8145),

    -- ── Restaurants & Dining ──
    ('Leopold Cafe Colaba', 'restaurant', 18.9228, 72.8317),
    ('Britannia & Co. Ballard Estate', 'restaurant', 18.9362, 72.8402),
    ('Pritam Da Dhaba Dadar', 'restaurant', 19.0195, 72.8431),
    ('Candies Pali Hill Bandra', 'restaurant', 19.0621, 72.8274),
    ('Shiv Sagar Juhu', 'restaurant', 19.0988, 72.8279),
    ('Joeys Pizza Andheri West', 'restaurant', 19.1245, 72.8312),
    ('Guru Kripa Restaurant Sion', 'restaurant', 19.0392, 72.8615),
    ('Manis Lunch Home Chembur', 'restaurant', 19.0588, 72.8982),
    ('Sarvi Restaurant Byculla', 'restaurant', 18.9662, 72.8295),
    ('Copper Chimney Worli', 'restaurant', 18.9982, 72.8165),
    ('Mahesh Lunch Home Fort', 'restaurant', 18.9335, 72.8348),
    ('Gajalee Seafood Vile Parle', 'restaurant', 19.1022, 72.8475),

    -- ── Cafes & Bakeries ──
    ('Kyani & Co. Bakery Marine Lines', 'cafe', 18.9438, 72.8278),
    ('Blue Tokai Coffee Roasters Bandra', 'cafe', 19.0645, 72.8315),
    ('Theobroma Patisserie Colaba', 'cafe', 18.9245, 72.8322),
    ('Subko Coffee Roasters Bandra Village', 'cafe', 19.0562, 72.8268),
    ('Third Wave Coffee BKC', 'cafe', 19.0682, 72.8675),
    ('Starbucks Reserve Fort', 'cafe', 18.9312, 72.8340),
    ('Cafe Madras Matunga', 'cafe', 19.0275, 72.8552),
    ('Kala Ghoda Cafe Fort', 'cafe', 18.9298, 72.8328),
    ('Blue Tokai Lower Parel Mills', 'cafe', 18.9945, 72.8258),
    ('Candies Mac Ronells Bandra', 'cafe', 19.0552, 72.8320),

    -- ── Supermarkets & Groceries ──
    ('Natures Basket Turner Road Bandra', 'supermarket', 19.0578, 72.8335),
    ('Foodhall Linking Road Santacruz', 'supermarket', 19.0812, 72.8365),
    ('DMart Andheri East', 'supermarket', 19.1145, 72.8692),
    ('Star Bazaar Andheri Link Road', 'supermarket', 19.1352, 72.8328),
    ('Reliance Smart Superstore Ghatkopar', 'supermarket', 19.0855, 72.9082),
    ('Natures Basket Worli', 'supermarket', 19.0125, 72.8188),
    ('Haiko Supermarket Powai', 'supermarket', 19.1215, 72.9102),
    ('Sahakari Bhandar Dadar West', 'supermarket', 19.0215, 72.8415),
    ('DMart Chembur East', 'supermarket', 19.0498, 72.8885),
    ('Reliance Fresh Kurla West', 'grocery', 19.0715, 72.8752),
    ('Local Fresh Mart Wadala', 'grocery', 19.0245, 72.8712),

    -- ── Fuel Stations & EV Fast Chargers ──
    ('BPCL Auto Care & EV Fast Charger Bandra', 'fuel', 19.0475, 72.8322),
    ('HP Petrol Pump Dadar TT', 'fuel', 19.0162, 72.8465),
    ('Indian Oil Auto Fuel Station WEH Khar', 'fuel', 19.0712, 72.8425),
    ('Tata Power EV Superfast Hub BKC', 'fuel', 19.0655, 72.8715),
    ('Bharat Petroleum Pump Marine Drive', 'fuel', 18.9412, 72.8235),
    ('Shell Fuel Station Kurla SCLR', 'fuel', 19.0688, 72.8795),
    ('Indian Oil Pump Chakala Andheri WEH', 'fuel', 19.1122, 72.8615),
    ('HPCL Fuel Station Sion Circle', 'fuel', 19.0375, 72.8628),
    ('Jio-bp Mobility Station Chembur', 'fuel', 19.0515, 72.8942),
    ('BPCL Petrol Pump JVLR Powai', 'fuel', 19.1235, 72.8985),

    -- ── Banks & Financial Hubs ──
    ('State Bank of India Main Branch Fort', 'bank', 18.9325, 72.8355),
    ('HDFC Bank & 24/7 ATM Bandra Linking Rd', 'bank', 19.0612, 72.8345),
    ('ICICI Bank Regional Hub BKC', 'bank', 19.0672, 72.8665),
    ('Kotak Mahindra Bank Lower Parel', 'bank', 18.9942, 72.8245),
    ('Axis Bank Dadar TT Circle', 'bank', 19.0182, 72.8452),
    ('HDFC Bank Andheri West SV Road', 'bank', 19.1185, 72.8445),
    ('Bank of Baroda Chembur Naka', 'bank', 19.0575, 72.8955),
    ('Standard Chartered Bank Marine Lines', 'bank', 18.9442, 72.8295)
ON CONFLICT (name) DO NOTHING;