USE exam_timetabling;

-- Generate Time Slots For Period Procedure
DELIMITER $$

CREATE PROCEDURE GenerateTimeSlotsForPeriod(IN p_id_periode INT)
BEGIN
    -- Rename variable to avoid conflict with SQL keyword 'CURRENT_DATE'
    DECLARE v_date DATE;
    DECLARE v_end_date DATE;

    -- Get period dates
    SELECT date_debut, date_fin
    INTO v_date, v_end_date
    FROM periodes_examens
    WHERE id_periode = p_id_periode;

    -- Safety check
    IF v_date IS NULL OR v_end_date IS NULL THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Invalid exam period ID';
    END IF;

    -- Loop through all days in the period
    WHILE v_date <= v_end_date DO

        INSERT INTO creneaux (id_periode, date, heure_debut, heure_fin)
        VALUES
        (p_id_periode, v_date, '08:30:00', '10:00:00'),
        (p_id_periode, v_date, '10:15:00', '11:45:00'),
        (p_id_periode, v_date, '12:00:00', '13:30:00'),
        (p_id_periode, v_date, '13:45:00', '15:15:00');

        SET v_date = DATE_ADD(v_date, INTERVAL 1 DAY);
    END WHILE;
END$$

DELIMITER ;


DELIMITER $$

CREATE PROCEDURE DeletePlanningForPeriod(IN p_id_periode INT)
BEGIN
    -- Disable FK checks temporarily
    SET FOREIGN_KEY_CHECKS = 0;

    -- 1. Delete surveillances linked to this period
    DELETE s
    FROM surveillances s
    JOIN planning_examens pe ON pe.id_planning = s.id_planning
    JOIN creneaux c ON c.id_creneau = pe.id_creneau
    WHERE c.id_periode = p_id_periode;

    -- 2. Delete planning_groupes
    DELETE pg
    FROM planning_groupes pg
    JOIN planning_examens pe ON pe.id_planning = pg.id_planning
    JOIN creneaux c ON c.id_creneau = pe.id_creneau
    WHERE c.id_periode = p_id_periode;

    -- 3. Delete planning_examens
    DELETE pe
    FROM planning_examens pe
    JOIN creneaux c ON c.id_creneau = pe.id_creneau
    WHERE c.id_periode = p_id_periode;

    -- 4. Delete creneaux
    DELETE FROM creneaux
    WHERE id_periode = p_id_periode;

    -- 5. Delete the period itself
    DELETE FROM periodes_examens
    WHERE id_periode = p_id_periode;

    -- Re-enable FK checks
    SET FOREIGN_KEY_CHECKS = 1;
END$$

DELIMITER ;

