-- ============================================
-- FUNCTION 1: Generate Time Slots For Period
-- ============================================
-- Converts MySQL PROCEDURE to PostgreSQL FUNCTION

CREATE OR REPLACE FUNCTION generate_time_slots_for_period(p_id_periode INTEGER)
RETURNS VOID AS $$
DECLARE
    v_date DATE;
    v_end_date DATE;
BEGIN
    -- Get period dates
    SELECT date_debut, date_fin
    INTO v_date, v_end_date
    FROM periodes_examens
    WHERE id_periode = p_id_periode;

    -- Safety check
    IF v_date IS NULL OR v_end_date IS NULL THEN
        RAISE EXCEPTION 'Invalid exam period ID: %', p_id_periode;
    END IF;

    -- Loop through all days in the period
    WHILE v_date <= v_end_date LOOP
        
        -- Insert 4 time slots per day
        INSERT INTO creneaux (id_periode, date, heure_debut, heure_fin)
        VALUES
        (p_id_periode, v_date, '08:30:00', '10:00:00'),
        (p_id_periode, v_date, '10:15:00', '11:45:00'),
        (p_id_periode, v_date, '12:00:00', '13:30:00'),
        (p_id_periode, v_date, '13:45:00', '15:15:00');

        -- Move to next day (PostgreSQL syntax)
        v_date := v_date + INTERVAL '1 day';
        
    END LOOP;
    
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- FUNCTION 2: Delete Planning For Period
-- ============================================
-- Converts MySQL PROCEDURE to PostgreSQL FUNCTION

CREATE OR REPLACE FUNCTION delete_planning_for_period(p_id_periode INTEGER)
RETURNS VOID AS $$
BEGIN
    -- PostgreSQL handles FK constraints differently
    -- We can use CASCADE or delete in order
    
    -- 1. Delete surveillances linked to this period
    DELETE FROM surveillances
    WHERE id_planning IN (
        SELECT pe.id_planning
        FROM planning_examens pe
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = p_id_periode
    );

    -- 2. Delete planning_groupes
    DELETE FROM planning_groupes
    WHERE id_planning IN (
        SELECT pe.id_planning
        FROM planning_examens pe
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = p_id_periode
    );

    -- 3. Delete planning_examens
    DELETE FROM planning_examens
    WHERE id_creneau IN (
        SELECT id_creneau
        FROM creneaux
        WHERE id_periode = p_id_periode
    );

    -- 4. Delete creneaux
    DELETE FROM creneaux
    WHERE id_periode = p_id_periode;

    -- 5. Delete the period itself
    DELETE FROM periodes_examens
    WHERE id_periode = p_id_periode;
    
    -- Note: In PostgreSQL, you can also use ON DELETE CASCADE in FK definitions
    -- to make this automatic
    
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- HELPER FUNCTIONS (Optional but useful)
-- ============================================

-- Function to get total exam duration for a period
CREATE OR REPLACE FUNCTION get_period_duration(p_id_periode INTEGER)
RETURNS INTERVAL AS $$
DECLARE
    v_start_date DATE;
    v_end_date DATE;
BEGIN
    SELECT date_debut, date_fin
    INTO v_start_date, v_end_date
    FROM periodes_examens
    WHERE id_periode = p_id_periode;
    
    IF v_start_date IS NULL THEN
        RETURN NULL;
    END IF;
    
    RETURN (v_end_date - v_start_date);
END;
$$ LANGUAGE plpgsql;

-- Function to count time slots in a period
CREATE OR REPLACE FUNCTION count_period_slots(p_id_periode INTEGER)
RETURNS INTEGER AS $$
DECLARE
    slot_count INTEGER;
BEGIN
    SELECT COUNT(*)
    INTO slot_count
    FROM creneaux
    WHERE id_periode = p_id_periode;
    
    RETURN slot_count;
END;
$$ LANGUAGE plpgsql;

-- Function to check if period has planning
CREATE OR REPLACE FUNCTION period_has_planning(p_id_periode INTEGER)
RETURNS BOOLEAN AS $$
DECLARE
    has_planning BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM planning_examens pe
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = p_id_periode
        LIMIT 1
    ) INTO has_planning;
    
    RETURN has_planning;
END;
$$ LANGUAGE plpgsql;
