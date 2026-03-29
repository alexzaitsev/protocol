-------------------------------------------------------------
--------------------------- USERS ---------------------------
-------------------------------------------------------------

-- Users
INSERT INTO person.users (id, google_email, display_name, sex, date_of_birth) VALUES
    ('jane', 'jane@google.com', 'Jane', 'f', '1990-05-15'),
    ('john', 'john@google.com', 'John', 'm', '1985-11-22');

-- Health Profiles: Jane
INSERT INTO person.health_profiles (
    user_id,
    conditions,
    family_history,
    substances,
    diet_notes,
    activity_notes,
    health_priorities,
    safety_checks,
    methodology_notes
) VALUES (
    'jane',                          -- user_id
    '[
        {"name": "seasonal allergies", "status": "active", "notes": "spring pollen, managed with antihistamines"},
        {"name": "mild iron deficiency", "status": "monitoring", "notes": "borderline ferritin, retesting in 6 months"}
    ]'::jsonb,                       -- conditions
    '[
        {"condition": "type 2 diabetes", "relative": "mother"},
        {"condition": "hypertension", "relative": "grandfather"}
    ]'::jsonb,                       -- family_history
    '[
        {"name": "coffee", "frequency": "daily", "notes": "1 cup black coffee, morning, ~95mg caffeine"},
        {"name": "alcohol", "frequency": "occasional", "notes": "wine, 1-2 glasses on weekends"}
    ]'::jsonb,                       -- substances
    'Mostly plant-based, 3 meals/day. Focus on iron-rich foods (lentils, spinach, tofu). Breakfast: oatmeal with fruit. Lunch: salad or grain bowl. Dinner: varied, home-cooked.', -- diet_notes
    'Yoga 3x/week, running 2x/week (5K). Desk job with standing desk, ~8h/day.', -- activity_notes
    '[
        "iron optimization (ferritin monitoring, absorption enhancers)",
        "diabetes prevention (family history)",
        "stress management and sleep quality",
        "seasonal allergy symptom reduction"
    ]'::jsonb,                       -- health_priorities
    '[
        "iron absorption interactions (avoid calcium/tannins with iron-rich meals)",
        "allergy medication interactions",
        "blood sugar impact of supplements",
        "protocol coherence (no redundancy/antagonism)"
    ]'::jsonb,                       -- safety_checks
    'Evidence-based approach (PubMed, Examine.com). Preventative focus on metabolic health. Track via regular blood work. Conservative supplementation — food-first philosophy.' -- methodology_notes
);

-- Health Profiles: John
INSERT INTO person.health_profiles (
    user_id,
    conditions,
    family_history,
    substances,
    diet_notes,
    activity_notes,
    health_priorities,
    safety_checks,
    methodology_notes
) VALUES (
    'john',                          -- user_id
    '[
        {"name": "mild hypertension", "status": "managed", "notes": "controlled with lifestyle, BP ~135/85"},
        {"name": "lower back pain", "status": "intermittent", "notes": "from previous sports injury, managed with PT exercises"}
    ]'::jsonb,                       -- conditions
    '[
        {"condition": "cardiovascular disease", "relative": "father"},
        {"condition": "osteoarthritis", "relative": "grandmother"}
    ]'::jsonb,                       -- family_history
    '[
        {"name": "coffee", "frequency": "daily", "notes": "2 cups, morning and early afternoon"},
        {"name": "alcohol", "frequency": "rare"}
    ]'::jsonb,                       -- substances
    'High-protein diet, 3 meals + 1 snack. Focus on lean meats, fish 2x/week, vegetables. Limits sodium. Meal preps on weekends.', -- diet_notes
    'Weight training 4x/week, walking 30 min daily. Former competitive swimmer. Sedentary work (software developer) offset with gym routine.', -- activity_notes
    '[
        "cardiovascular health (BP management, family history)",
        "joint and back health maintenance",
        "muscle recovery optimization",
        "sleep quality improvement"
    ]'::jsonb,                       -- health_priorities
    '[
        "blood pressure impact of supplements (avoid stimulants, watch sodium)",
        "caffeine interaction (moderate daily intake ~200mg)",
        "joint supplement interactions with any future Rx",
        "protocol coherence (no redundancy/antagonism)"
    ]'::jsonb,                       -- safety_checks
    'Evidence-based medicine (PubMed, Cochrane, Examine.com — state confidence levels). Data-driven approach with regular blood work tracking. Focus on longevity and functional fitness.' -- methodology_notes
);

-- User Preferences: Jane
INSERT INTO person.preferences (
    user_id,
    location,
    occupation,
    language,
    units,
    currency,
    date_format,
    communication
) VALUES (
    'jane',                          -- user_id
    'Portland, Oregon, USA',         -- location
    'UX Designer',                   -- occupation
    'en',                            -- language
    'metric',                        -- units
    'USD',                           -- currency
    'YYYY-MM-DD',                    -- date_format
    'Friendly and clear. Evidence-based but accessible. Prefer concise bullet points over long paragraphs.' -- communication
);

-- User Preferences: John
INSERT INTO person.preferences (
    user_id,
    location,
    occupation,
    language,
    units,
    currency,
    date_format,
    communication
) VALUES (
    'john',                          -- user_id
    'Austin, Texas, USA',            -- location
    'Software Developer',            -- occupation
    'en',                            -- language
    'imperial',                      -- units
    'USD',                           -- currency
    'YYYY-MM-DD',                    -- date_format
    'Direct and technical. Include mechanism of action when relevant. Data and numbers preferred over qualitative descriptions.' -- communication
);

-------------------------------------------------------------
------------------------ SUPPLEMENTS ------------------------
-------------------------------------------------------------

-- Inventory (shared catalog)
INSERT INTO supplement.inventory
    (id, name, brand, category, form, dosage_per_unit, features)
OVERRIDING SYSTEM VALUE
VALUES
    (1,  'Iron Bisglycinate',         'Thorne',              'mineral',       'capsule',     '36mg',           '[]'::jsonb),
    (2,  'Vitamin C',                 'NOW Foods',           'vitamin',       'capsule',     '1000mg',         '[]'::jsonb),
    (3,  'Vitamin D3',                'Thorne',              'vitamin',       'liquid drop', '1000 IU',        '[]'::jsonb),
    (4,  'Magnesium Glycinate',       'Pure Encapsulations', 'mineral',       'capsule',     '120mg',          '[]'::jsonb),
    (5,  'Quercetin',                 'Thorne',              'flavonoid',     'capsule',     '250mg',          '[]'::jsonb),
    (6,  'Daily Synbiotic',           'Seed',                'probiotic',     'capsule',     '24 billion CFU', '["synbiotic"]'::jsonb),
    (7,  'Omega-3 Fish Oil',          'Nordic Naturals',     'fatty acid',    'softgel',     '1100mg EPA+DHA', '["triglyceride form"]'::jsonb),
    (8,  'Glucosamine + Chondroitin', 'NOW Foods',           'joint support', 'capsule',     '750mg/600mg',    '[]'::jsonb),
    (9,  'CoQ10',                     'Thorne',              'antioxidant',   'capsule',     '100mg',          '["ubiquinone"]'::jsonb),
    (10, 'Creatine Monohydrate',      'Thorne',              'amino acid',    'powder',      '5g',             '["micronized"]'::jsonb);

-- Supplements: Jane
-- Health priorities: iron optimization, diabetes prevention, stress/sleep, allergy reduction
INSERT INTO supplement.supplements
    (id, user_id, inventory_id, time_blocks, dosage, frequency, started_at, ended_at, replaces_id, breaks)
OVERRIDING SYSTEM VALUE
VALUES
    -- Iron Bisglycinate: iron deficiency management
    (1, 'jane', 1, '["morning"]'::jsonb,            '1 capsule',  'daily', '2025-10-15', NULL,          NULL, NULL),
    -- Vitamin C: pairs with iron for absorption
    (2, 'jane', 2, '["morning"]'::jsonb,            '1 capsule',  'daily', '2025-10-15', NULL,          NULL, NULL),
    -- Vitamin D3: original dose (ended, replaced by id=4)
    (3, 'jane', 3, '["morning"]'::jsonb,            '1 drop',     'daily', '2025-09-01', '2025-12-01',  NULL, NULL),
    -- Vitamin D3: increased dose after blood work (SCD Type 2)
    (4, 'jane', 3, '["morning"]'::jsonb,            '2 drops',    'daily', '2025-12-01', NULL,          3,    NULL),
    -- Magnesium Glycinate: stress and sleep support
    (5, 'jane', 4, '["evening"]'::jsonb,            '2 capsules', 'daily', '2026-01-10', NULL,          NULL, NULL),
    -- Quercetin: seasonal allergy management (morning + evening split)
    (6, 'jane', 5, '["morning", "evening"]'::jsonb, '1 capsule',  'daily', '2026-02-15', NULL,          NULL, NULL);

-- Supplements: John
-- Health priorities: cardiovascular health, joint/back health, muscle recovery, sleep
INSERT INTO supplement.supplements
    (id, user_id, inventory_id, time_blocks, dosage, frequency, started_at, ended_at, replaces_id)
OVERRIDING SYSTEM VALUE
VALUES
    -- Omega-3 Fish Oil: cardiovascular and joint support
    (7,  'john', 7, '["morning"]'::jsonb,            '2 softgels', 'daily', '2025-08-01', NULL,          NULL),
    -- Magnesium Glycinate: original dose (ended, replaced by id=9)
    (8,  'john', 4, '["evening"]'::jsonb,            '1 capsule',  'daily', '2025-07-15', '2025-11-01',  NULL),
    -- Magnesium Glycinate: increased for BP management (SCD Type 2)
    (9,  'john', 4, '["evening"]'::jsonb,            '2 capsules', 'daily', '2025-11-01', NULL,          8   ),
    -- CoQ10: cardiovascular health
    (10, 'john', 9, '["morning"]'::jsonb,            '1 capsule',  'daily', '2025-09-01', NULL,          NULL),
    -- Creatine Monohydrate: muscle recovery (8 weeks on, 4 weeks off)
    (11, 'john', 10, '["any"]'::jsonb,               '1 scoop',    'daily', '2025-06-01', NULL,          NULL),
    -- Glucosamine + Chondroitin: joint and back health (morning + evening split)
    (12, 'john', 8, '["morning", "evening"]'::jsonb, '1 capsule',  'daily', '2026-01-05', NULL,          NULL);

-- Reset identity sequences after explicit ID inserts
SELECT setval(pg_get_serial_sequence('supplement.inventory', 'id'), (SELECT MAX(id) FROM supplement.inventory));
SELECT setval(pg_get_serial_sequence('supplement.supplements', 'id'), (SELECT MAX(id) FROM supplement.supplements));
