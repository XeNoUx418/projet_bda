-- PostgreSQL Schema for Exam Timetabling System
-- Converted from MySQL

-- Enable UUID extension (optional, for future use)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- STRUCTURE ACADÉMIQUE
-- ============================================

-- Table des départements
CREATE TABLE departements (
  id_dept SERIAL PRIMARY KEY,
  nom VARCHAR(100) NOT NULL
);

-- Table des formations
CREATE TABLE formations (
  id_formation SERIAL PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  id_dept INTEGER NOT NULL,
  FOREIGN KEY (id_dept) REFERENCES departements(id_dept)
);

-- Table des modules
CREATE TABLE modules (
  id_module SERIAL PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  credits INTEGER,
  id_formation INTEGER NOT NULL,
  annee VARCHAR(10),
  FOREIGN KEY (id_formation) REFERENCES formations(id_formation)
);

-- ============================================
-- GROUPES ET ÉTUDIANTS
-- ============================================

-- Table des groupes
CREATE TABLE groupes (
  id_groupe SERIAL PRIMARY KEY,
  code_groupe VARCHAR(20) NOT NULL UNIQUE,
  id_formation INTEGER NOT NULL,
  effectif INTEGER DEFAULT 0,
  annee VARCHAR(10),
  FOREIGN KEY (id_formation) REFERENCES formations(id_formation)
);

-- Table des étudiants
CREATE TABLE etudiants (
    id_etudiant SERIAL PRIMARY KEY,
    nom VARCHAR(100),
    prenom VARCHAR(100),
    annee VARCHAR(20),
    id_formation INTEGER NOT NULL,
    id_groupe INTEGER DEFAULT NULL,
    FOREIGN KEY (id_formation) REFERENCES formations(id_formation)
);

-- ============================================
-- EXAMENS ET PÉRIODES
-- ============================================

-- Table des examens
CREATE TABLE examens (
  id_examen SERIAL PRIMARY KEY,
  id_module INTEGER NOT NULL UNIQUE,
  duree_minutes INTEGER NOT NULL,
  FOREIGN KEY (id_module) REFERENCES modules(id_module)
);

-- Table des périodes d'examen
CREATE TABLE periodes_examens (
  id_periode SERIAL PRIMARY KEY,
  description VARCHAR(100),
  date_debut DATE NOT NULL,
  date_fin DATE NOT NULL,
  generation_time_seconds DECIMAL(10, 2) DEFAULT NULL,
  generation_completed_at TIMESTAMP DEFAULT NULL
);

-- Table des créneaux horaires
CREATE TABLE creneaux (
  id_creneau SERIAL PRIMARY KEY,
  id_periode INTEGER NOT NULL,
  date DATE NOT NULL,
  heure_debut TIME NOT NULL,
  heure_fin TIME NOT NULL,
  FOREIGN KEY (id_periode) REFERENCES periodes_examens(id_periode),
  CHECK (heure_debut < heure_fin)
);

-- ============================================
-- SALLES D'EXAMEN
-- ============================================

-- Table des lieux d'examen (use VARCHAR with CHECK instead of ENUM)
CREATE TABLE lieux_examen (
  id_lieu SERIAL PRIMARY KEY,
  nom VARCHAR(100) NOT NULL,
  capacite INTEGER NOT NULL CHECK (capacite > 0),
  type VARCHAR(10) NOT NULL CHECK (type IN ('salle', 'amphi')),
  batiment VARCHAR(50)
);

-- ============================================
-- PLANNING DES EXAMENS
-- ============================================

-- Table du planning des examens
CREATE TABLE planning_examens (
  id_planning SERIAL PRIMARY KEY,
  id_examen INTEGER NOT NULL,
  id_creneau INTEGER NOT NULL,
  id_lieu INTEGER NOT NULL,
  FOREIGN KEY (id_examen) REFERENCES examens(id_examen),
  FOREIGN KEY (id_creneau) REFERENCES creneaux(id_creneau),
  FOREIGN KEY (id_lieu) REFERENCES lieux_examen(id_lieu)
);

-- Table d'assignation groupes-salles
CREATE TABLE planning_groupes (
  id_planning INTEGER,
  id_groupe INTEGER,
  split_part SMALLINT DEFAULT NULL,
  merged_groups VARCHAR(255) DEFAULT NULL,
  PRIMARY KEY (id_planning, id_groupe),
  FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning),
  FOREIGN KEY (id_groupe) REFERENCES groupes(id_groupe)
);

-- ============================================
-- PROFESSEURS ET SURVEILLANCE
-- ============================================

-- Table des professeurs
CREATE TABLE professeurs (
  id_prof SERIAL PRIMARY KEY,
  nom VARCHAR(100),
  specialite VARCHAR(100),
  id_dept INTEGER NOT NULL,
  FOREIGN KEY (id_dept) REFERENCES departements(id_dept)
);

-- Table des surveillances
CREATE TABLE surveillances (
  id_prof INTEGER,
  id_planning INTEGER,
  PRIMARY KEY (id_prof, id_planning),
  FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof),
  FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning)
);

-- ============================================
-- INSCRIPTIONS
-- ============================================

-- Table des inscriptions étudiants-modules
CREATE TABLE inscriptions (
  id_etudiant INTEGER NOT NULL,
  id_module INTEGER NOT NULL,
  PRIMARY KEY (id_etudiant, id_module),
  FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant),
  FOREIGN KEY (id_module) REFERENCES modules(id_module)
);

-- ============================================
-- UTILISATEURS ET RÔLES
-- ============================================

-- Table des rôles
CREATE TABLE roles (
  id_role SERIAL PRIMARY KEY,
  nom_role VARCHAR(50) UNIQUE
);

-- Table des utilisateurs
CREATE TABLE users (
  id_user SERIAL PRIMARY KEY,
  username VARCHAR(50) UNIQUE,
  password VARCHAR(255),
  id_role INTEGER,
  id_etudiant INTEGER,
  id_prof INTEGER,
  FOREIGN KEY (id_role) REFERENCES roles(id_role),
  FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant),
  FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Index for modules
CREATE INDEX idx_modules_formation ON modules(id_formation);

-- Index for groupes
CREATE INDEX idx_groupes_formation ON groupes(id_formation);

-- Index for examens
CREATE INDEX idx_examens_module ON examens(id_module);

-- Index for creneaux
CREATE INDEX idx_creneaux_periode ON creneaux(id_periode);

-- Index for planning_examens
CREATE INDEX idx_planning_examen ON planning_examens(id_examen);
CREATE INDEX idx_planning_creneau ON planning_examens(id_creneau);

-- Index for inscriptions
CREATE INDEX idx_inscriptions_module ON inscriptions(id_module);
CREATE INDEX idx_inscriptions_etudiant ON inscriptions(id_etudiant);

-- Index for surveillances
CREATE INDEX idx_surveillances_prof ON surveillances(id_prof);

-- Index for etudiants
CREATE INDEX idx_etudiants_formation ON etudiants(id_formation);
CREATE INDEX idx_etudiants_groupe ON etudiants(id_groupe);

-- Index for lieux_examen
CREATE INDEX idx_lieux_type ON lieux_examen(type);

-- Index for planning_groupes
CREATE INDEX idx_split_part ON planning_groupes(split_part);

-- Index for planning_examens lookups (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_pe_creneau_planning
ON planning_examens (id_creneau, id_planning);

-- Index for planning_groupes lookups (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_pg_planning
ON planning_groupes (id_planning);

-- Composite index for group conflict checks (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_pg_groupe_planning
ON planning_groupes (id_groupe, id_planning);

-- Index for surveillances lookups (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_surv_planning_prof
ON surveillances (id_planning, id_prof);

-- Composite index for creneaux by period (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_creneaux_periode_creneau
ON creneaux (id_periode, id_creneau);

-- Index for date lookups in creneaux
CREATE INDEX IF NOT EXISTS idx_creneaux_date
ON creneaux (date);

-- ============================================
-- INDEXES FOR DASHBOARD QUERIES
-- ============================================

-- Index for dashboard KPI queries
CREATE INDEX IF NOT EXISTS idx_pe_examen
ON planning_examens (id_examen);

-- Index for professor conflicts dashboard
CREATE INDEX IF NOT EXISTS idx_surv_prof
ON surveillances (id_prof);

-- ============================================
-- INDEXES FOR STUDENT/PROFESSOR SCHEDULES
-- ============================================

-- Index for student schedule queries
CREATE INDEX IF NOT EXISTS idx_etudiants_groupe_formation
ON etudiants (id_groupe, id_formation);

-- Composite index for planning_examens with all joins
CREATE INDEX IF NOT EXISTS idx_pe_composite
ON planning_examens (id_examen, id_creneau, id_lieu);
