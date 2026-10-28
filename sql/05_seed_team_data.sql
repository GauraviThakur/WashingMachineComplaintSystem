
-- ============================================================
-- Washing Machine Complaint Management System
-- Seed: 05 - Teams and Issue-to-Team Mappings
-- ============================================================

-- 1. Create the teams responsible for resolving issues
INSERT INTO teams (team_name, team_description)
VALUES
    ('Electrical Team', 'Handles electrical and wiring-related issues.'),
    ('Mechanical Team', 'Handles mechanical and component-related issues.'),
    ('Water Leakage Team', 'Handles water leakage and water connection issues.'),
    ('Performance Team', 'Handles washing and performance-related issues.'),
    ('Installation Team', 'Handles installation-related issues.'),
    ('Quality Team', 'Handles quality verification and testing.')
ON CONFLICT (team_name) DO UPDATE
SET team_description = EXCLUDED.team_description,
    is_active = TRUE,
    updated_at = CURRENT_TIMESTAMP;


-- 2. Map each issue type to a primary team based on its category
INSERT INTO issue_type_team_mapping (
    issue_type_id,
    team_id,
    is_primary,
    is_active
)
SELECT
    it.issue_type_id,
    t.team_id,
    TRUE,
    TRUE
FROM issue_types AS it
JOIN complaint_categories AS cc
    ON cc.category_id = it.category_id
JOIN teams AS t
    ON t.team_name = CASE
        WHEN LOWER(cc.category_name) LIKE '%elect%'
            THEN 'Electrical Team'
        WHEN LOWER(cc.category_name) LIKE '%mechan%'
            THEN 'Mechanical Team'
        WHEN LOWER(cc.category_name) LIKE '%water%'
          OR LOWER(cc.category_name) LIKE '%leak%'
            THEN 'Water Leakage Team'
        WHEN LOWER(cc.category_name) LIKE '%performance%'
            THEN 'Performance Team'
        WHEN LOWER(cc.category_name) LIKE '%install%'
            THEN 'Installation Team'
        ELSE 'Quality Team'
    END
WHERE it.is_active = TRUE
ON CONFLICT (issue_type_id, team_id) DO UPDATE
SET is_primary = TRUE,
    is_active = TRUE;


-- 3. Display the teams created
SELECT
    team_id,
    team_name,
    is_active
FROM teams
ORDER BY team_id;


-- 4. Display issue types and their mapped teams
SELECT
    it.issue_type_id,
    it.issue_type_name,
    cc.category_name,
    t.team_name,
    itm.is_primary
FROM issue_type_team_mapping AS itm
JOIN issue_types AS it
    ON it.issue_type_id = itm.issue_type_id
JOIN complaint_categories AS cc
    ON cc.category_id = it.category_id
JOIN teams AS t
    ON t.team_id = itm.team_id
WHERE itm.is_active = TRUE
ORDER BY cc.category_name, it.issue_type_name;
