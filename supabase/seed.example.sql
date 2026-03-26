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
