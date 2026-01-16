-- Créer la base de données
drop database exam_timetabling;
CREATE DATABASE IF NOT EXISTS exam_timetabling
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE exam_timetabling;

-- ============================================
-- STRUCTURE ACADÉMIQUE
-- ============================================

-- Table des départements
CREATE TABLE departements (
  id_dept INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL
);

-- Table des formations
CREATE TABLE formations (
  id_formation INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  id_dept INT NOT NULL,
  FOREIGN KEY (id_dept) REFERENCES departements(id_dept)
);

-- Table des modules
CREATE TABLE modules (
  id_module INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  credits INT,
  id_formation INT NOT NULL,
  annee VARCHAR(10),
  FOREIGN KEY (id_formation) REFERENCES formations(id_formation)
);

-- ============================================
-- GROUPES ET ÉTUDIANTS
-- ============================================

-- Table des groupes
CREATE TABLE groupes (
  id_groupe INT AUTO_INCREMENT PRIMARY KEY,
  code_groupe VARCHAR(20) NOT NULL,
  id_formation INT NOT NULL,
  effectif INT DEFAULT 0,
  annee VARCHAR(10),
  FOREIGN KEY (id_formation) REFERENCES formations(id_formation),
  UNIQUE (code_groupe)
);

-- Table des étudiants
CREATE TABLE etudiants (
    id_etudiant INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    annee VARCHAR(20),
    id_formation INT NOT NULL,
    id_groupe INT DEFAULT NULL,
    FOREIGN KEY (id_formation) REFERENCES formations(id_formation)
);

-- ============================================
-- EXAMENS ET PÉRIODES
-- ============================================

-- Table des examens
CREATE TABLE examens (
  id_examen INT AUTO_INCREMENT PRIMARY KEY,
  id_module INT NOT NULL,
  duree_minutes INT NOT NULL,
  FOREIGN KEY (id_module) REFERENCES modules(id_module),
  UNIQUE (id_module)
);

-- Table des périodes d'examen
CREATE TABLE periodes_examens (
  id_periode INT AUTO_INCREMENT PRIMARY KEY,
  description VARCHAR(100),
  date_debut DATE NOT NULL,
  date_fin DATE NOT NULL
);

-- Table des créneaux horaires
CREATE TABLE creneaux (
  id_creneau INT AUTO_INCREMENT PRIMARY KEY,
  id_periode INT NOT NULL,
  date DATE NOT NULL,
  heure_debut TIME NOT NULL,
  heure_fin TIME NOT NULL,
  CHECK (heure_debut < heure_fin),
  FOREIGN KEY (id_periode) REFERENCES periodes_examens(id_periode)
);

-- ============================================
-- SALLES D'EXAMEN (SALLES / AMPHITHÉÂTRES)
-- ============================================

-- Table des lieux d'examen
CREATE TABLE lieux_examen (
  id_lieu INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  capacite INT NOT NULL CHECK (capacite > 0),
  type ENUM('salle', 'amphi') NOT NULL,
  batiment VARCHAR(50)
);

-- ============================================
-- 🔥 PLANNING DES EXAMENS (TABLE CENTRALE)
-- ============================================

-- Table du planning des examens
CREATE TABLE planning_examens (
  id_planning INT AUTO_INCREMENT PRIMARY KEY,
  id_examen INT NOT NULL,
  id_creneau INT NOT NULL,
  id_lieu INT NOT NULL,
  FOREIGN KEY (id_examen) REFERENCES examens(id_examen),
  FOREIGN KEY (id_creneau) REFERENCES creneaux(id_creneau),
  FOREIGN KEY (id_lieu) REFERENCES lieux_examen(id_lieu),
  INDEX (id_examen),
  INDEX (id_creneau),
  INDEX (id_lieu)
);

-- ============================================
-- ASSIGNATION GROUPES ↔ SALLES (MANQUANT AVANT)
-- ============================================

-- Table d'assignation groupes-salles
CREATE TABLE planning_groupes (
  id_planning INT,
  id_groupe INT,
  split_part TINYINT NULL DEFAULT NULL COMMENT 'NULL=not split, 1=A, 2=B',
  merged_groups VARCHAR(255) NULL DEFAULT NULL COMMENT 'Codes of all groups merged in this exam',
  PRIMARY KEY (id_planning, id_groupe),
  FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning),
  FOREIGN KEY (id_groupe) REFERENCES groupes(id_groupe)
);

-- ============================================
-- PROFESSEURS ET SURVEILLANCE
-- ============================================

-- Table des professeurs
CREATE TABLE professeurs (
  id_prof INT AUTO_INCREMENT PRIMARY KEY,
  nom VARCHAR(100),
  specialite VARCHAR(100),
  id_dept INT NOT NULL,
  FOREIGN KEY (id_dept) REFERENCES departements(id_dept)
);

-- Table des surveillances
CREATE TABLE surveillances (
  id_prof INT,
  id_planning INT,
  PRIMARY KEY (id_prof, id_planning),
  FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof),
  FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning)
);

-- ============================================
-- INSCRIPTIONS DES ÉTUDIANTS AUX MODULES
-- ============================================

-- Table des inscriptions étudiants-modules
CREATE TABLE inscriptions (
  id_etudiant INT NOT NULL,
  id_module INT NOT NULL,
  PRIMARY KEY (id_etudiant, id_module),
  FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant),
  FOREIGN KEY (id_module) REFERENCES modules(id_module)
);

-- ============================================
-- UTILISATEURS ET RÔLES (COUCHE APPLICATION)
-- ============================================

-- Table des rôles
CREATE TABLE roles (
  id_role INT AUTO_INCREMENT PRIMARY KEY,
  nom_role VARCHAR(50) UNIQUE
);

-- Table des utilisateurs
CREATE TABLE users (
  id_user INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  password VARCHAR(255),
  id_role INT,
  id_etudiant INT,
  id_prof INT,
  FOREIGN KEY (id_role) REFERENCES roles(id_role),
  FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant),
  FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof)
);

-- ============================================
-- INDEX POUR LES PERFORMANCES
-- ============================================

-- Index pour la table modules
CREATE INDEX idx_modules_formation ON modules(id_formation);

-- Index pour la table groupes
CREATE INDEX idx_groupes_formation ON groupes(id_formation);

-- Index pour la table examens
CREATE INDEX idx_examens_module ON examens(id_module);

-- Index pour la table creneaux
CREATE INDEX idx_creneaux_periode ON creneaux(id_periode);

-- Index pour la table planning_examens
CREATE INDEX idx_planning_examen ON planning_examens(id_examen);
CREATE INDEX idx_planning_creneau ON planning_examens(id_creneau);

-- Index pour la table inscriptions
CREATE INDEX idx_inscriptions_module ON inscriptions(id_module);
CREATE INDEX idx_inscriptions_etudiant ON inscriptions(id_etudiant);

-- Index pour la table surveillances
CREATE INDEX idx_surveillances_prof ON surveillances(id_prof);

-- Index pour la table etudiants
CREATE INDEX idx_etudiants_formation ON etudiants(id_formation);
CREATE INDEX idx_etudiants_groupe ON etudiants(id_groupe);

-- Index pour la table lieux_examen
CREATE INDEX idx_lieux_type ON lieux_examen(type);

-- index for better query performance
CREATE INDEX idx_split_part ON planning_groupes(split_part);