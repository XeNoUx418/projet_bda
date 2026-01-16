-- Foreign Key Restoration Script
-- Generated: 2026-01-15 22:43:10.766948

ALTER TABLE creneaux ADD CONSTRAINT creneaux_ibfk_1 FOREIGN KEY (id_periode) REFERENCES periodes_examens(id_periode);
ALTER TABLE etudiants ADD CONSTRAINT etudiants_ibfk_1 FOREIGN KEY (id_formation) REFERENCES formations(id_formation);
ALTER TABLE examens ADD CONSTRAINT examens_ibfk_1 FOREIGN KEY (id_module) REFERENCES modules(id_module);
ALTER TABLE formations ADD CONSTRAINT formations_ibfk_1 FOREIGN KEY (id_dept) REFERENCES departements(id_dept);
ALTER TABLE groupes ADD CONSTRAINT groupes_ibfk_1 FOREIGN KEY (id_formation) REFERENCES formations(id_formation);
ALTER TABLE inscriptions ADD CONSTRAINT inscriptions_ibfk_1 FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant);
ALTER TABLE inscriptions ADD CONSTRAINT inscriptions_ibfk_2 FOREIGN KEY (id_module) REFERENCES modules(id_module);
ALTER TABLE modules ADD CONSTRAINT modules_ibfk_1 FOREIGN KEY (id_formation) REFERENCES formations(id_formation);
ALTER TABLE planning_examens ADD CONSTRAINT planning_examens_ibfk_1 FOREIGN KEY (id_examen) REFERENCES examens(id_examen);
ALTER TABLE planning_examens ADD CONSTRAINT planning_examens_ibfk_2 FOREIGN KEY (id_creneau) REFERENCES creneaux(id_creneau);
ALTER TABLE planning_examens ADD CONSTRAINT planning_examens_ibfk_3 FOREIGN KEY (id_lieu) REFERENCES lieux_examen(id_lieu);
ALTER TABLE planning_groupes ADD CONSTRAINT planning_groupes_ibfk_1 FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning);
ALTER TABLE planning_groupes ADD CONSTRAINT planning_groupes_ibfk_2 FOREIGN KEY (id_groupe) REFERENCES groupes(id_groupe);
ALTER TABLE professeurs ADD CONSTRAINT professeurs_ibfk_1 FOREIGN KEY (id_dept) REFERENCES departements(id_dept);
ALTER TABLE surveillances ADD CONSTRAINT surveillances_ibfk_1 FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof);
ALTER TABLE surveillances ADD CONSTRAINT surveillances_ibfk_2 FOREIGN KEY (id_planning) REFERENCES planning_examens(id_planning);
ALTER TABLE users ADD CONSTRAINT users_ibfk_1 FOREIGN KEY (id_role) REFERENCES roles(id_role);
ALTER TABLE users ADD CONSTRAINT users_ibfk_2 FOREIGN KEY (id_etudiant) REFERENCES etudiants(id_etudiant);
ALTER TABLE users ADD CONSTRAINT users_ibfk_3 FOREIGN KEY (id_prof) REFERENCES professeurs(id_prof);