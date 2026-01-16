USE exam_timetabling;

SET SQL_SAFE_UPDATES = 0;

-- ============================================
-- 1. DEPARTMENTS & FORMATIONS (Static)
-- ============================================
INSERT INTO departements (nom) VALUES 
('Informatique'), ('Mathématiques'), ('Physique'), ('Chimie'), 
('Économie'), ('Droit'), ('Médecine');

INSERT INTO formations (nom, id_dept) VALUES
-- Informatique (ID 1)
('Licence Informatique', 1), ('Licence Systèmes et Réseaux', 1), ('Licence Développement Web', 1), ('Licence Big Data', 1), ('Licence Réalité Virtuelle', 1),
('Master Génie Logiciel', 1), ('Master Intelligence Artificielle', 1), ('Master Cybersécurité', 1), ('Master Cloud Computing', 1), ('Master IoT', 1),
-- Mathématiques (ID 2)
('Licence Mathématiques', 2), ('Licence Statistiques', 2), ('Licence Math-Info', 2), ('Licence Actuariat', 2), ('Licence Modélisation', 2),
('Master Mathématiques Appliquées', 2), ('Master Data Science', 2), ('Master Recherche Opérationnelle', 2), ('Master Cryptographie', 2), ('Master Mathématiques Fondamentales', 2),
-- Physique (ID 3)
('Licence Physique', 3), ('Licence Énergie', 3), ('Licence Mécanique', 3), ('Licence Nanotechnologies', 3), ('Licence Acoustique', 3),
('Master Physique Quantique', 3), ('Master Matériaux', 3), ('Master Astrophysique', 3), ('Master Physique Médicale', 3), ('Master Optique', 3),
-- Chimie (ID 4)
('Licence Chimie', 4), ('Licence Biochimie', 4), ('Licence Chimie Analytique', 4), ('Licence Chimie Environnementale', 4), ('Licence Chimie Industrielle', 4),
('Master Chimie Organique', 4), ('Master Génie Chimique', 4), ('Master Chimie Pharmaceutique', 4), ('Master Chimie des Matériaux', 4), ('Master Chimie Fine', 4),
-- Économie (ID 5)
('Licence Économie', 5), ('Licence Marketing', 5), ('Licence Banque', 5), ('Licence RH', 5), ('Licence Commerce International', 5),
('Master Finance', 5), ('Master Audit', 5), ('Master Management', 5), ('Master Supply Chain', 5), ('Master Entrepreneuriat', 5),
-- Droit (ID 6)
('Licence Droit Privé', 6), ('Licence Droit Public', 6), ('Licence Sciences Po', 6), ('Licence Criminologie', 6), ('Licence Droit Fiscal', 6),
('Master Droit des Affaires', 6), ('Master Droit International', 6), ('Master Droit Notarial', 6), ('Master Droit Social', 6), ('Master Droit Européen', 6),
-- Médecine (ID 7)
('Licence Médecine', 7), ('Licence Pharmacie', 7), ('Licence Dentaire', 7), ('Licence Kinésithérapie', 7), ('Licence Sage-femme', 7),
('Master Chirurgie', 7), ('Master Pédiatrie', 7), ('Master Cardiologie', 7), ('Master Neurologie', 7), ('Master Radiologie', 7);

-- ============================================
-- 2. MODULES GENERATION
-- ============================================
-- Generate modules: 6-9 per year for each formation
INSERT INTO modules (nom, credits, id_formation, annee)
WITH RECURSIVE years AS (
    SELECT 1 as year_num, 'L1' as annee UNION
    SELECT 2, 'L2' UNION
    SELECT 3, 'L3' UNION
    SELECT 4, 'M1' UNION
    SELECT 5, 'M2'
),
modules_per_year AS (
    SELECT 
        f.id_formation,
        CASE 
            WHEN f.nom LIKE 'Licence%' THEN y.annee
            WHEN f.nom LIKE 'Master%' AND y.year_num >= 4 THEN y.annee
            ELSE NULL
        END as annee,
        -- Random number of modules between 6 and 9
        FLOOR(6 + RAND() * 4) as num_modules
    FROM formations f
    CROSS JOIN years y
    WHERE (f.nom LIKE 'Licence%' AND y.year_num <= 3)
       OR (f.nom LIKE 'Master%' AND y.year_num >= 4)
),
module_numbers AS (
    SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION 
    SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9
)
SELECT 
    CONCAT('MOD_', mp.annee, '_F', mp.id_formation, '_', mn.n),
    5,
    mp.id_formation,
    mp.annee
FROM modules_per_year mp
CROSS JOIN module_numbers mn
WHERE mn.n <= mp.num_modules;

-- ============================================
-- 3. GROUPES GENERATION (STRICT RULES)
-- ============================================
-- Licence: 5 Groups (G01-G05) per year (L1-L3)
-- Master: 3 Groups (G01-G03) per year (M1-M2)
INSERT INTO groupes (code_groupe, id_formation, annee, effectif)
WITH 
group_nums_L AS (SELECT 1 as n UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5),
group_nums_M AS (SELECT 1 as n UNION SELECT 2 UNION SELECT 3),
years_L AS (SELECT 'L1' as annee UNION SELECT 'L2' UNION SELECT 'L3'),
years_M AS (SELECT 'M1' as annee UNION SELECT 'M2')
-- Licence Groups
SELECT 
    CONCAT(f.id_formation, '-', y.annee, '-G', LPAD(gn.n, 2, '0')), -- Unique Code
    f.id_formation,
    y.annee,
    30 -- Initialize with exactly 30
FROM formations f
CROSS JOIN years_L y
CROSS JOIN group_nums_L gn
WHERE f.nom LIKE 'Licence%'
UNION ALL
-- Master Groups
SELECT 
    CONCAT(f.id_formation, '-', y.annee, '-G', LPAD(gn.n, 2, '0')),
    f.id_formation,
    y.annee,
    30 -- Initialize with exactly 30
FROM formations f
CROSS JOIN years_M y
CROSS JOIN group_nums_M gn
WHERE f.nom LIKE 'Master%';

-- ============================================
-- 4. ETUDIANTS GENERATION (STRICT 30 PER GROUP)
-- ============================================
-- We iterate through existing groups and add exactly 30 students to each
INSERT INTO etudiants (nom, prenom, annee, id_formation, id_groupe)
WITH RECURSIVE 
students_per_group AS (
    SELECT 1 as n UNION ALL SELECT n + 1 FROM students_per_group WHERE n < 30
)
SELECT 
    CONCAT('Nom_', g.code_groupe, '_', LPAD(spg.n, 2, '0')),
    CONCAT('Prenom_', LPAD(FLOOR(RAND() * 1000), 3, '0')),
    g.annee,
    g.id_formation,
    g.id_groupe
FROM groupes g
CROSS JOIN students_per_group spg;

-- ============================================
-- 5: PROFESSEURS
-- ============================================

INSERT INTO professeurs (nom, specialite, id_dept)
SELECT 
    CONCAT('Prof_', LPAD(n, 4, '0')) as nom,
    CONCAT('Specialite_', 
           CASE d.nom
               WHEN 'Informatique' THEN 'INFO'
               WHEN 'Mathématiques' THEN 'MATH'
               WHEN 'Physique' THEN 'PHYS'
               WHEN 'Chimie' THEN 'CHIM'
               WHEN 'Économie' THEN 'ECO'
               WHEN 'Droit' THEN 'DROIT'
               WHEN 'Médecine' THEN 'MED'
               ELSE 'GEN'
           END,
           '_', LPAD(FLOOR(1 + RAND() * 20), 2, '0')) as specialite,
    d.id_dept
FROM departements d
CROSS JOIN (
    SELECT 
        (a.n + b.n*10) as n
    FROM 
        (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5 UNION SELECT 6 UNION SELECT 7 UNION SELECT 8 UNION SELECT 9) a,
        (SELECT 0 as n UNION SELECT 1 UNION SELECT 2 UNION SELECT 3) b  -- 10 × 4 = 40 numbers
    WHERE (a.n + b.n*10) > 0 AND (a.n + b.n*10) <= 34  -- Limit to 34 per department
) numbers
ORDER BY RAND();

-- ============================================
-- 6. INSCRIPTIONS (Link Students to Modules)
-- ============================================
-- Enroll every student in all modules for their formation and year
INSERT INTO inscriptions (id_etudiant, id_module)
SELECT e.id_etudiant, m.id_module
FROM etudiants e
JOIN modules m ON e.id_formation = m.id_formation AND e.annee = m.annee;

-- ============================================
-- PART 9: LIEUX EXAMEN (Exam rooms)
-- ============================================
INSERT INTO lieux_examen (nom, capacite, type, batiment) VALUES 
-- Small rooms (50 rooms, capacity 20)
('Salle A101', 20, 'salle', 'Bâtiment A'),
('Salle A102', 20, 'salle', 'Bâtiment A'),
('Salle A103', 20, 'salle', 'Bâtiment A'),
('Salle A104', 20, 'salle', 'Bâtiment A'),
('Salle A105', 20, 'salle', 'Bâtiment A'),
('Salle A106', 20, 'salle', 'Bâtiment A'),
('Salle A107', 20, 'salle', 'Bâtiment A'),
('Salle A108', 20, 'salle', 'Bâtiment A'),
('Salle A109', 20, 'salle', 'Bâtiment A'),
('Salle A110', 20, 'salle', 'Bâtiment A'),
('Salle B201', 20, 'salle', 'Bâtiment B'),
('Salle B202', 20, 'salle', 'Bâtiment B'),
('Salle B203', 20, 'salle', 'Bâtiment B'),
('Salle B204', 20, 'salle', 'Bâtiment B'),
('Salle B205', 20, 'salle', 'Bâtiment B'),
('Salle B206', 20, 'salle', 'Bâtiment B'),
('Salle B207', 20, 'salle', 'Bâtiment B'),
('Salle B208', 20, 'salle', 'Bâtiment B'),
('Salle B209', 20, 'salle', 'Bâtiment B'),
('Salle B210', 20, 'salle', 'Bâtiment B'),
('Salle C301', 20, 'salle', 'Bâtiment C'),
('Salle C302', 20, 'salle', 'Bâtiment C'),
('Salle C303', 20, 'salle', 'Bâtiment C'),
('Salle C304', 20, 'salle', 'Bâtiment C'),
('Salle C305', 20, 'salle', 'Bâtiment C'),
('Salle C306', 20, 'salle', 'Bâtiment C'),
('Salle C307', 20, 'salle', 'Bâtiment C'),
('Salle C308', 20, 'salle', 'Bâtiment C'),
('Salle C309', 20, 'salle', 'Bâtiment C'),
('Salle C310', 20, 'salle', 'Bâtiment C'),
('Salle D401', 20, 'salle', 'Bâtiment D'),
('Salle D402', 20, 'salle', 'Bâtiment D'),
('Salle D403', 20, 'salle', 'Bâtiment D'),
('Salle D404', 20, 'salle', 'Bâtiment D'),
('Salle D405', 20, 'salle', 'Bâtiment D'),
('Salle D406', 20, 'salle', 'Bâtiment D'),
('Salle D407', 20, 'salle', 'Bâtiment D'),
('Salle D408', 20, 'salle', 'Bâtiment D'),
('Salle D409', 20, 'salle', 'Bâtiment D'),
('Salle D410', 20, 'salle', 'Bâtiment D'),
('Salle E501', 20, 'salle', 'Bâtiment E'),
('Salle E502', 20, 'salle', 'Bâtiment E'),
('Salle E503', 20, 'salle', 'Bâtiment E'),
('Salle E504', 20, 'salle', 'Bâtiment E'),
('Salle E505', 20, 'salle', 'Bâtiment E'),
('Salle E506', 20, 'salle', 'Bâtiment E'),
('Salle E507', 20, 'salle', 'Bâtiment E'),
('Salle E508', 20, 'salle', 'Bâtiment E'),
('Salle E509', 20, 'salle', 'Bâtiment E'),
('Salle E510', 20, 'salle', 'Bâtiment E'),

-- Amphitheaters (15 amphis, capacity 100-500)
('Amphi Central', 500, 'amphi', 'Bâtiment Principal'),
('Amphi Grand', 400, 'amphi', 'Bâtiment Principal'),
('Amphi Nord', 300, 'amphi', 'Bâtiment Nord'),
('Amphi Sud', 300, 'amphi', 'Bâtiment Sud'),
('Amphi Est', 250, 'amphi', 'Bâtiment Est'),
('Amphi Ouest', 250, 'amphi', 'Bâtiment Ouest'),
('Amphi Sciences', 200, 'amphi', 'Bâtiment Sciences'),
('Amphi Lettres', 200, 'amphi', 'Bâtiment Lettres'),
('Amphi Droit', 150, 'amphi', 'Bâtiment Droit'),
('Amphi Médecine', 150, 'amphi', 'Bâtiment Médecine'),
('Amphi Économie', 200, 'amphi', 'Bâtiment Économie'),
('Amphi Informatique', 300, 'amphi', 'Bâtiment Informatique'),
('Amphi Conférence A', 100, 'amphi', 'Bâtiment Conférence'),
('Amphi Conférence B', 100, 'amphi', 'Bâtiment Conférence'),
('Amphi Conférence C', 100, 'amphi', 'Bâtiment Conférence');
-- ============================================
-- PART 10: EXAMENS (One exam per module, 90 minutes)
-- ============================================
INSERT INTO examens (id_module, duree_minutes)
SELECT id_module, 90 FROM modules;

SET SQL_SAFE_UPDATES = 1;