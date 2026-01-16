-- Add Triggers

-- Trigger 1 — Max 3 exams per professor per day
DELIMITER $$

CREATE TRIGGER trg_prof_max_3_per_day
BEFORE INSERT ON surveillances
FOR EACH ROW
BEGIN
    DECLARE exam_date DATE;
    DECLARE nb INT;

    SELECT c.date INTO exam_date
    FROM planning_examens p
    JOIN creneaux c ON c.id_creneau = p.id_creneau
    WHERE p.id_examen = NEW.id_examen;

    SELECT COUNT(*) INTO nb
    FROM surveillances s
    JOIN planning_examens p ON p.id_examen = s.id_examen
    JOIN creneaux c ON c.id_creneau = p.id_creneau
    WHERE s.id_prof = NEW.id_prof
      AND c.date = exam_date;

    IF nb >= 3 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Professor cannot supervise more than 3 exams per day';
    END IF;
END$$

DELIMITER ;

-- Trigger 2 — Prevent duplicate surveillance of same exam
DELIMITER $$

CREATE TRIGGER trg_prof_no_slot_conflict
BEFORE INSERT ON surveillances
FOR EACH ROW
BEGIN
    DECLARE slot_id INT;
    DECLARE cnt INT;

    SELECT p.id_creneau INTO slot_id
    FROM planning_examens p
    WHERE p.id_examen = NEW.id_examen;

    SELECT COUNT(*) INTO cnt
    FROM surveillances s
    JOIN planning_examens p ON p.id_examen = s.id_examen
    WHERE s.id_prof = NEW.id_prof
      AND p.id_creneau = slot_id;

    IF cnt > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Professor already assigned to another exam in this time slot';
    END IF;
END$$

DELIMITER ;

