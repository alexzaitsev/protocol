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
INSERT INTO supplements.inventory
    (id, name, brand, category, form, dosage_per_unit, features)
OVERRIDING SYSTEM VALUE
VALUES
    (1,  'Iron Bisglycinate',         'Thorne',              'mineral',       'capsule',     '36mg',           '{}'),
    (2,  'Vitamin C',                 'NOW Foods',           'vitamin',       'capsule',     '1000mg',         '{}'),
    (3,  'Vitamin D3',                'Thorne',              'vitamin',       'liquid drop', '1000 IU',        '{}'),
    (4,  'Magnesium Glycinate',       'Pure Encapsulations', 'mineral',       'capsule',     '120mg',          '{}'),
    (5,  'Quercetin',                 'Thorne',              'flavonoid',     'capsule',     '250mg',          '{}'),
    (6,  'Daily Synbiotic',           'Seed',                'probiotic',     'capsule',     '24 billion CFU', '{synbiotic}'),
    (7,  'Omega-3 Fish Oil',          'Nordic Naturals',     'fatty acid',    'softgel',     '1100mg EPA+DHA', '{"triglyceride form"}'),
    (8,  'Glucosamine + Chondroitin', 'NOW Foods',           'joint support', 'capsule',     '750mg/600mg',    '{}'),
    (9,  'CoQ10',                     'Thorne',              'antioxidant',   'capsule',     '100mg',          '{ubiquinone}'),
    (10, 'Creatine Monohydrate',      'Thorne',              'amino acid',    'powder',      '5g',             '{micronized}');

-- Supplements: Jane
-- Health priorities: iron optimization, diabetes prevention, stress/sleep, allergy reduction
INSERT INTO supplements.journal
    (id, user_id, inventory_id, time_blocks, dosage, frequency, started_at, replaces_id, replacement_reason, ended_at, end_reason)
OVERRIDING SYSTEM VALUE
VALUES
    -- Iron Bisglycinate: iron deficiency management
    (1, 'jane', 1, '{morning}',          '1 capsule',  'daily', '2025-10-15', NULL, NULL, NULL, NULL),
    -- Vitamin C: pairs with iron for absorption
    (2, 'jane', 2, '{morning}',          '1 capsule',  'daily', '2025-10-15', NULL, NULL, NULL, NULL),
    -- Vitamin D3: original dose (ended, replaced by id=4)
    (3, 'jane', 3, '{morning}',          '1 drop',     'daily', '2025-09-01', NULL, NULL, '2025-12-01', 'replaced — dose increase after blood work'),
    -- Vitamin D3: increased dose after blood work (SCD Type 2)
    (4, 'jane', 3, '{morning}',          '2 drops',    'daily', '2025-12-01', 3,    'Blood work showed 25(OH)D at 22 ng/mL — below optimal range; doubled dose per provider recommendation', NULL, NULL),
    -- Magnesium Glycinate: stress and sleep support
    (5, 'jane', 4, '{evening}',          '2 capsules', 'daily', '2026-01-10', NULL, NULL, NULL, NULL),
    -- Quercetin: seasonal allergy management (morning + evening split)
    (6, 'jane', 5, '{morning,evening}',  '1 capsule',  'daily', '2026-02-15', NULL, NULL, NULL, NULL),
    -- Daily Synbiotic: gut health trial (ended — GI discomfort)
    (13, 'jane', 6, '{morning}',         '1 capsule',  'daily', '2025-08-01', NULL, NULL, '2025-11-15', 'digestive discomfort at full dose'),
    -- Daily Synbiotic: reintroduced at reduced frequency, then discontinued (all columns set)
    (14, 'jane', 6, '{morning}',         '1 capsule',  'every other day', '2026-01-05', 13, 'Reintroduced at reduced frequency after GI adjustment period', '2026-02-28', 'no measurable benefit after 8-week trial');

-- Supplements: John
-- Health priorities: cardiovascular health, joint/back health, muscle recovery, sleep
INSERT INTO supplements.journal
    (id, user_id, inventory_id, time_blocks, dosage, frequency, started_at, replaces_id, replacement_reason, ended_at, end_reason)
OVERRIDING SYSTEM VALUE
VALUES
    -- Omega-3 Fish Oil: cardiovascular and joint support
    (7,  'john', 7, '{morning}',          '2 softgels', 'daily', '2025-08-01', NULL, NULL, NULL, NULL),
    -- Magnesium Glycinate: original dose (ended, replaced by id=9)
    (8,  'john', 4, '{evening}',          '1 capsule',  'daily', '2025-07-15', NULL, NULL, '2025-11-01', 'replaced — dose increase for BP management'),
    -- Magnesium Glycinate: increased for BP management (SCD Type 2)
    (9,  'john', 4, '{evening}',          '2 capsules', 'daily', '2025-11-01', 8,    'BP readings averaging 138/87 over 3 months; increased magnesium per cardiologist advice to support BP management', NULL, NULL),
    -- CoQ10: cardiovascular health
    (10, 'john', 9, '{morning}',          '1 capsule',  'daily', '2025-09-01', NULL, NULL, NULL, NULL),
    -- Creatine Monohydrate: muscle recovery (8 weeks on, 4 weeks off)
    (11, 'john', 10, '{any}',             '1 scoop',    'daily', '2025-06-01', NULL, NULL, NULL, NULL),
    -- Glucosamine + Chondroitin: joint and back health (morning + evening split)
    (12, 'john', 8, '{morning,evening}',  '1 capsule',  'daily', '2026-01-05', NULL, NULL, NULL, NULL),
    -- Vitamin D3: winter supplementation (ended — seasonal)
    (15, 'john', 3, '{morning}',          '1 drop',     'daily', '2025-10-01', NULL, NULL, '2026-01-15', 'target 25(OH)D reached after winter supplementation'),
    -- Vitamin D3: resumed at higher dose after retest, then paused (all columns set)
    (16, 'john', 3, '{morning}',          '2 drops',    'daily', '2026-02-01', 15, 'February retest showed 25(OH)D dropped to 24 ng/mL; resumed at double dose', '2026-03-15', '25(OH)D restored to 42 ng/mL — pausing for spring sun exposure');

-- Context: Jane
INSERT INTO supplements.context (user_id, inventory_id, purpose) VALUES
    ('jane', 1, '{iron optimization,address borderline ferritin}'),
    ('jane', 2, '{vitamin C paired with iron,enhance non-heme absorption}'),
    ('jane', 3, '{baseline vitamin D support}'),
    ('jane', 4, '{stress management,sleep quality improvement}'),
    ('jane', 5, '{natural antihistamine,seasonal allergy symptom reduction}'),
    ('jane', 6, '{gut health,digestive support}');

-- Context: John
INSERT INTO supplements.context (user_id, inventory_id, purpose) VALUES
    ('john', 3, '{vitamin D optimization,winter maintenance}'),
    ('john', 4, '{blood pressure management,sleep quality}'),
    ('john', 7, '{cardiovascular protection,joint anti-inflammatory support}'),
    ('john', 8, '{joint health maintenance,lower back health}'),
    ('john', 9, '{cardiovascular health,cellular energy production}'),
    ('john', 10, '{muscle recovery,strength maintenance}');

-- Reset identity sequences after explicit ID inserts
SELECT setval(pg_get_serial_sequence('supplements.inventory', 'id'), (SELECT MAX(id) FROM supplements.inventory));
SELECT setval(pg_get_serial_sequence('supplements.journal', 'id'), (SELECT MAX(id) FROM supplements.journal));
SELECT setval(pg_get_serial_sequence('supplements.context', 'id'), (SELECT MAX(id) FROM supplements.context));
