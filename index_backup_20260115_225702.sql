-- Index Restoration Script
-- Generated: 2026-01-15 22:57:02.767326


-- Indexes for table: creneaux
CREATE INDEX idx_creneaux_periode ON creneaux(id_periode);

-- Indexes for table: etudiants
CREATE INDEX idx_etudiants_formation ON etudiants(id_formation);
CREATE INDEX idx_etudiants_groupe ON etudiants(id_groupe);

-- Indexes for table: examens
CREATE UNIQUE INDEX id_module ON examens(id_module);
CREATE INDEX idx_examens_module ON examens(id_module);

-- Indexes for table: formations
CREATE INDEX id_dept ON formations(id_dept);

-- Indexes for table: groupes
CREATE UNIQUE INDEX code_groupe ON groupes(code_groupe);
CREATE INDEX idx_groupes_formation ON groupes(id_formation);

-- Indexes for table: inscriptions
CREATE INDEX idx_inscriptions_etudiant ON inscriptions(id_etudiant);
CREATE INDEX idx_inscriptions_module ON inscriptions(id_module);

-- Indexes for table: lieux_examen
CREATE INDEX idx_lieux_type ON lieux_examen(type);

-- Indexes for table: modules
CREATE INDEX idx_modules_formation ON modules(id_formation);

-- Indexes for table: planning_examens
CREATE INDEX id_creneau ON planning_examens(id_creneau);
CREATE INDEX id_examen ON planning_examens(id_examen);
CREATE INDEX id_lieu ON planning_examens(id_lieu);
CREATE INDEX idx_planning_creneau ON planning_examens(id_creneau);
CREATE INDEX idx_planning_examen ON planning_examens(id_examen);

-- Indexes for table: planning_groupes
CREATE INDEX id_groupe ON planning_groupes(id_groupe);
CREATE INDEX idx_split_part ON planning_groupes(split_part);

-- Indexes for table: professeurs
CREATE INDEX id_dept ON professeurs(id_dept);

-- Indexes for table: roles
CREATE UNIQUE INDEX nom_role ON roles(nom_role);

-- Indexes for table: surveillances
CREATE INDEX id_planning ON surveillances(id_planning);
CREATE INDEX idx_surveillances_prof ON surveillances(id_prof);

-- Indexes for table: users
CREATE INDEX id_etudiant ON users(id_etudiant);
CREATE INDEX id_prof ON users(id_prof);
CREATE INDEX id_role ON users(id_role);
CREATE UNIQUE INDEX username ON users(username);