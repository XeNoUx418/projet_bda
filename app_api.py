from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import date
import time
import os

from db import query_df, get_conn

PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("DEBUG", "False") == "True"

app = Flask(__name__)
CORS(app)

# -------------------------
# Helpers
# -------------------------
def ok(data=None, **extra):
    payload = {"ok": True, "data": data}
    payload.update(extra)
    return jsonify(payload)

def fail(message, code=400):
    return jsonify({"ok": False, "error": message}), code

# -------------------------
# Database Initialization
# -------------------------
@app.route('/api/admin/init_database', methods=['POST'])
def init_database():
    """Initialize database with schema, procedures, and data"""
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load Schema
        schema_path = os.path.join(base_dir, 'Database', 'schema_postgresql.sql')
        with open(schema_path, 'r', encoding='utf-8') as f:
            cur.execute(f.read())
            conn.commit()
        
        # Load Procedures
        procedures_path = os.path.join(base_dir, 'Database', 'procedures_postgresql.sql')
        with open(procedures_path, 'r', encoding='utf-8') as f:
            cur.execute(f.read())
            conn.commit()
        
        # Load Data
        data_path = os.path.join(base_dir, 'Database', 'data_postgresql.sql')
        with open(data_path, 'r', encoding='utf-8') as f:
            cur.execute(f.read())
            conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({"ok": True, "message": "Database initialized successfully"})
    except Exception as e:
        import traceback
        return jsonify({"ok": False, "error": str(e), "traceback": traceback.format_exc()}), 500

@app.get("/api/health")
def health():
    return ok({"status": "up"})

# -------------------------
# Reference lists
# -------------------------
@app.get("/api/departements")
def departements():
    df = query_df("SELECT id_dept, nom FROM departements ORDER BY nom")
    return ok(df.to_dict(orient="records"))

@app.get("/api/formations")
def formations():
    dept_id = request.args.get("dept_id", type=int)
    if not dept_id:
        return fail("dept_id is required")
    df = query_df(
        "SELECT id_formation, nom FROM formations WHERE id_dept=%s ORDER BY nom",
        params=[dept_id],
    )
    return ok(df.to_dict(orient="records"))

@app.get("/api/annees")
def annees():
    formation_id = request.args.get("formation_id", type=int)
    if not formation_id:
        return fail("formation_id is required")
    df = query_df(
        "SELECT DISTINCT annee FROM modules WHERE id_formation=%s AND annee IS NOT NULL ORDER BY annee",
        params=[formation_id],
    )
    return ok([r["annee"] for r in df.to_dict(orient="records")])

@app.get("/api/periodes")
def periodes():
    df = query_df("""
        SELECT
            p.id_periode,
            p.description,
            p.date_debut,
            p.date_fin,
            CASE
                WHEN EXISTS (
                    SELECT 1
                    FROM planning_examens pe
                    JOIN creneaux c ON c.id_creneau = pe.id_creneau
                    WHERE c.id_periode = p.id_periode
                ) THEN 1 ELSE 0
            END AS has_planning
        FROM periodes_examens p
        ORDER BY p.date_debut DESC
    """)
    return ok(df.to_dict(orient="records"))

@app.get("/api/sessions")
def sessions():
    formation_id = request.args.get("formation_id", type=int)
    annee = request.args.get("annee", type=str)
    if not formation_id or not annee:
        return fail("formation_id and annee are required")

    df = query_df("""
        SELECT DISTINCT
            p.id_periode,
            p.description,
            p.date_debut,
            p.date_fin,
            p.description || ' (' ||
            TO_CHAR(p.date_debut, 'DD Mon YYYY') ||
            ' → ' ||
            TO_CHAR(p.date_fin, 'DD Mon YYYY') ||
            ')' AS label
        FROM periodes_examens p
        JOIN creneaux c ON c.id_periode = p.id_periode
        JOIN planning_examens pe ON pe.id_creneau = c.id_creneau
        JOIN examens e ON e.id_examen = pe.id_examen
        JOIN modules m ON m.id_module = e.id_module
        WHERE m.id_formation = %s AND m.annee = %s
        ORDER BY p.date_debut DESC
    """, params=[formation_id, annee])

    return ok(df.to_dict(orient="records"))

# -------------------------
# Student schedule - FIXED FOR POSTGRESQL
# -------------------------
@app.route("/api/schedule")
def schedule():
    formation_id = request.args.get("formation_id", type=int)
    annee = request.args.get("annee", type=str)
    periode_id = request.args.get("periode_id", type=int)

    if not formation_id or not annee or not periode_id:
        return fail("formation_id, annee, periode_id are required")

    # PostgreSQL compatible query with quoted aliases to preserve case
    df = query_df("""
        SELECT
            c.date                                   AS exam_date,
            TO_CHAR(c.date, 'FMDay, FMMonth DD')     AS "DateLabel",
            TO_CHAR(c.heure_debut, 'HH24:MI')        AS "Start",
            TO_CHAR(c.heure_fin, 'HH24:MI')          AS "End",
            m.nom                                    AS "Module",
            e.duree_minutes                          AS "Duration",
            le.nom                                   AS "Room",
            le.type                                  AS "Type",
            le.batiment                              AS "Building",
            g.code_groupe                            AS "GroupCode",
            pg.split_part                            AS "SplitPart",
            pg.merged_groups                         AS "MergedGroups"
        FROM planning_examens pe
        JOIN examens e           ON e.id_examen = pe.id_examen
        JOIN modules m           ON m.id_module = e.id_module
        JOIN formations f        ON f.id_formation = m.id_formation
        JOIN creneaux c          ON c.id_creneau = pe.id_creneau
        JOIN lieux_examen le     ON le.id_lieu = pe.id_lieu
        JOIN planning_groupes pg ON pg.id_planning = pe.id_planning
        JOIN groupes g           ON g.id_groupe = pg.id_groupe
        WHERE f.id_formation = %s
          AND m.annee = %s
          AND c.id_periode = %s
        ORDER BY g.code_groupe, pg.split_part, c.date, c.heure_debut
    """, params=[formation_id, annee, periode_id])

    rows = df.to_dict(orient="records")

    groups = {}

    for r in rows:
        # 1. Determine the Group Key & Label
        #    Use .get() for safety, though keys should exist now
        merged_groups = r.get("MergedGroups")
        split_part = r.get("SplitPart")
        group_code = r.get("GroupCode")

        if merged_groups:
            # MERGED CASE (e.g. "G1+G2")
            key = merged_groups
            label = merged_groups.replace("+", " + ")
            group_type = "merged"
        elif split_part:
            # SPLIT CASE
            key = f"{group_code}_{split_part}"
            label = f"{group_code} (Part {split_part})"
            group_type = "split"
        else:
            # NORMAL CASE
            key = group_code
            label = group_code
            group_type = "normal"

        if key not in groups:
            groups[key] = {
                "label": label,
                "type": group_type,
                "exams": []
            }

        # 2. Prepare Data for Comparison & Insertion
        #    Convert date/time objects to strings if they aren't already
        #    (TO_CHAR usually returns strings, but 'exam_date' is raw date)
        
        raw_date = r.get("exam_date")
        if hasattr(raw_date, 'isoformat'):
            date_str = raw_date.isoformat()
        else:
            date_str = str(raw_date) if raw_date else ""

        # 3. DEDUPLICATION LOGIC
        #    We check if an exam with the same Module, Date, Start, End, Room
        #    already exists in this specific group's list.
        
        current_exam_signature = (
            r.get("Module"),
            date_str,
            r.get("Start"),
            r.get("End"),
            r.get("Room")
        )

        existing_signatures = {
            (
                e["module"],
                e["date"],
                e["start"],
                e["end"],
                e["room"]
            )
            for e in groups[key]["exams"]
        }

        if current_exam_signature not in existing_signatures:
            groups[key]["exams"].append({
                "date": date_str,
                "dateLabel": r.get("DateLabel", ""),
                "start": r.get("Start", ""),
                "end": r.get("End", ""),
                "module": r.get("Module", ""),
                "room": r.get("Room", ""),
                "building": r.get("Building", ""),
                "type": r.get("Type", "")
            })

    return ok(groups)


# -------------------------
# Professors
# -------------------------
@app.get("/api/professeurs")
def professeurs():
    df = query_df("""
        SELECT id_prof, nom, specialite, id_dept
        FROM professeurs
        ORDER BY nom
    """)
    return ok(df.to_dict(orient="records"))

@app.get("/api/prof_schedule")
def prof_schedule():
    prof_id = request.args.get("prof_id", type=int)
    date_start = request.args.get("date_start", type=str)
    date_end = request.args.get("date_end", type=str)

    if not prof_id or not date_start or not date_end:
        return fail("prof_id, date_start, date_end are required (YYYY-MM-DD)")

    df = query_df("""
        SELECT DISTINCT ON (pe.id_planning)
            pe.id_planning,
            c.date                                   AS exam_date,
            TO_CHAR(c.date, 'FMDay, FMMonth DD')     AS "DateLabel",
            TO_CHAR(c.heure_debut, 'HH24:MI')        AS "Start",
            TO_CHAR(c.heure_fin, 'HH24:MI')          AS "End",
            m.nom                                    AS "Module",
            e.duree_minutes                          AS "Duration",
            le.nom                                   AS "Room",
            le.type                                  AS "Type",
            le.batiment                              AS "Building",
            COALESCE(
                pg.merged_groups,
                CASE
                    WHEN pg.split_part IS NULL THEN g.code_groupe
                    ELSE g.code_groupe || ' (Part ' || pg.split_part || ')'
                END
            ) AS "GroupLabel"
        FROM surveillances s
        JOIN planning_examens pe ON pe.id_planning = s.id_planning
        JOIN creneaux c          ON c.id_creneau = pe.id_creneau
        JOIN examens e           ON e.id_examen = pe.id_examen
        JOIN modules m           ON m.id_module = e.id_module
        JOIN lieux_examen le     ON le.id_lieu = pe.id_lieu
        JOIN planning_groupes pg ON pg.id_planning = pe.id_planning
        JOIN groupes g           ON g.id_groupe = pg.id_groupe
        WHERE s.id_prof = %s
          AND c.date BETWEEN %s AND %s
        ORDER BY pe.id_planning, c.date, c.heure_debut
    """, params=[prof_id, date_start, date_end])

    return ok(df.to_dict(orient="records"))

# -------------------------
# Manager actions
# -------------------------
@app.post("/api/periodes")
def create_periode():
    body = request.get_json(silent=True) or {}
    d_start = body.get("date_debut")
    d_end = body.get("date_fin")
    description = body.get("description", "Session d'examen")

    if not d_start or not d_end:
        return fail("date_debut and date_fin are required")

    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO periodes_examens (date_debut, date_fin, description)
            VALUES (%s, %s, %s)
            RETURNING id_periode
        """, (d_start, d_end, description))
        
        period_id = cur.fetchone()[0]
        cur.execute("SELECT generate_time_slots_for_period(%s)", (period_id,))
        conn.commit()
        return ok({"id_periode": period_id})
    finally:
        conn.close()

@app.post("/api/periodes/<int:pid>/generate_planning")
def generate_planning(pid: int):
    """
    ✅ OPTIMIZED: Direct function call (no subprocess)
    This is 10-50x faster than subprocess.run()
    """
    start = time.time()
    
    try:
        # ✅ Import and call directly (much faster than subprocess)
        from generate_assign import generate_planning_for_period
        
        generate_planning_for_period(pid)
        
        elapsed = time.time() - start

        # Update generation stats
        conn = get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                UPDATE periodes_examens 
                SET generation_time_seconds = %s,
                    generation_completed_at = NOW()
                WHERE id_periode = %s
            """, (round(elapsed, 2), pid))
            conn.commit()
        finally:
            conn.close()

        return ok({
            "period_id": pid,
            "elapsed_seconds": round(elapsed, 2),
            "message": "Planning generated successfully"
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Generation error: {error_details}")
        return fail(f"Generation error: {str(e)}", 500)

@app.delete("/api/periodes/<int:pid>/planning")
def delete_planning(pid: int):
    """
    ✅ OPTIMIZED: PostgreSQL-optimized bulk delete
    Deletes planning data and optionally the period itself
    """
    # Get optional query parameter to delete period too
    delete_period = request.args.get("delete_period", "false").lower() == "true"
    
    conn = get_conn()
    try:
        cur = conn.cursor()
        
        # ✅ PostgreSQL-optimized: DELETE ... USING is much faster
        # Delete surveillances first (foreign key constraint)
        cur.execute("""
            DELETE FROM surveillances s
            USING planning_examens pe, creneaux c
            WHERE s.id_planning = pe.id_planning
            AND pe.id_creneau = c.id_creneau
            AND c.id_periode = %s
        """, (pid,))
        
        # Delete planning_groupes
        cur.execute("""
            DELETE FROM planning_groupes pg
            USING planning_examens pe, creneaux c
            WHERE pg.id_planning = pe.id_planning
            AND pe.id_creneau = c.id_creneau
            AND c.id_periode = %s
        """, (pid,))
        
        # Delete planning_examens
        cur.execute("""
            DELETE FROM planning_examens pe
            USING creneaux c
            WHERE pe.id_creneau = c.id_creneau
            AND c.id_periode = %s
        """, (pid,))
        
        # Optionally delete the period and its creneaux
        if delete_period:
            # Delete creneaux
            cur.execute("""
                DELETE FROM creneaux
                WHERE id_periode = %s
            """, (pid,))
            
            # Delete period
            cur.execute("""
                DELETE FROM periodes_examens
                WHERE id_periode = %s
            """, (pid,))
        
        conn.commit()
        
        message = "Planning and period deleted successfully" if delete_period else "Planning deleted successfully"
        return ok({"deleted_period": pid, "period_removed": delete_period, "message": message})
    except Exception as e:
        conn.rollback()
        return fail(f"Delete error: {str(e)}", 500)
    finally:
        conn.close()

@app.get("/api/periodes/<int:pid>/preview")
def preview(pid: int):
    limit = request.args.get("limit", default=100, type=int)
    df = query_df("""
        SELECT
            c.date AS "Date",
            TO_CHAR(c.heure_debut, 'HH24:MI') AS "Start",
            TO_CHAR(c.heure_fin, 'HH24:MI') AS "End",
            m.nom AS "Module",
            le.nom AS "Room"
        FROM planning_examens pe
        JOIN examens e       ON e.id_examen = pe.id_examen
        JOIN modules m       ON m.id_module = e.id_module
        JOIN creneaux c      ON c.id_creneau = pe.id_creneau
        JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
        WHERE c.id_periode = %s
        ORDER BY c.date, c.heure_debut
        LIMIT %s
    """, params=[pid, limit])
    return ok(df.to_dict(orient="records"))

@app.get("/api/periodes/<int:pid>/conflicts/surveillances")
def surveillance_conflicts(pid: int):
    """
    Check for surveillance conflicts:
    1. Professors assigned to multiple exams at the same time
    2. Professors with more than 3 surveillances per day
    """
    # Time slot conflicts
    time_conflicts_df = query_df("""
        SELECT 
            p.nom AS "Professor",
            c.date AS "Date",
            TO_CHAR(c.heure_debut, 'HH24:MI') AS "Time",
            COUNT(DISTINCT pe.id_examen) AS "ExamCount",
            STRING_AGG(DISTINCT le.nom, ', ') AS "Rooms"
        FROM surveillances s
        JOIN professeurs p ON p.id_prof = s.id_prof
        JOIN planning_examens pe ON pe.id_planning = s.id_planning
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
        WHERE c.id_periode = %s
        GROUP BY p.id_prof, p.nom, c.date, c.heure_debut
        HAVING COUNT(DISTINCT pe.id_examen) > 1
        ORDER BY c.date, c.heure_debut, p.nom
    """, params=[pid])
    
    # Daily overload conflicts
    daily_conflicts_df = query_df("""
        SELECT 
            p.nom AS "Professor",
            c.date AS "Date",
            COUNT(DISTINCT s.id_planning) AS "DailyCount"
        FROM surveillances s
        JOIN professeurs p ON p.id_prof = s.id_prof
        JOIN planning_examens pe ON pe.id_planning = s.id_planning
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = %s
        GROUP BY p.id_prof, p.nom, c.date
        HAVING COUNT(DISTINCT s.id_planning) > 3
        ORDER BY "DailyCount" DESC, c.date
    """, params=[pid])
    
    return ok({
        "time_conflicts": time_conflicts_df.to_dict(orient="records"),
        "daily_conflicts": daily_conflicts_df.to_dict(orient="records"),
        "total_time_conflicts": len(time_conflicts_df),
        "total_daily_conflicts": len(daily_conflicts_df)
    })

@app.get("/api/periodes/<int:pid>/conflicts/rooms")
def room_conflicts(pid: int):
    df = query_df("""
        SELECT
            le.nom AS "Room",
            c.date,
            TO_CHAR(c.heure_debut, 'HH24:MI') AS "Start",
            COUNT(*) AS "Exams"
        FROM planning_examens pe
        JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
        JOIN creneaux c      ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = %s
        GROUP BY le.nom, c.date, c.heure_debut
        HAVING COUNT(*) > 1
        ORDER BY c.date, c.heure_debut
    """, params=[pid])
    return ok(df.to_dict(orient="records"))

@app.get("/api/student_schedule")
def student_schedule():
    student_id = request.args.get("student_id", type=int)
    periode_id = request.args.get("periode_id", type=int)

    if not student_id or not periode_id:
        return fail("student_id and periode_id are required")

    df = query_df("""
        SELECT
            c.date                                   AS exam_date,
            TO_CHAR(c.date, 'FMDay, FMMonth DD')     AS "DateLabel",
            TO_CHAR(c.heure_debut, 'HH24:MI')        AS "Start",
            TO_CHAR(c.heure_fin, 'HH24:MI')          AS "End",
            m.nom                                    AS "Module",
            e.duree_minutes                          AS "Duration",
            le.nom                                   AS "Room",
            le.type                                  AS "Type",
            le.batiment                              AS "Building",
            g.code_groupe                            AS "GroupCode",
            pg.split_part                            AS "SplitPart",
            pg.merged_groups                         AS "MergedGroups"
        FROM etudiants et
        JOIN groupes g ON g.id_groupe = et.id_groupe
        JOIN planning_groupes pg ON pg.id_groupe = g.id_groupe
        JOIN planning_examens pe ON pe.id_planning = pg.id_planning
        JOIN examens e ON e.id_examen = pe.id_examen
        JOIN modules m ON m.id_module = e.id_module
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
        WHERE et.id_etudiant = %s
          AND c.id_periode = %s
        ORDER BY c.date, c.heure_debut
    """, params=[student_id, periode_id])

    rows = df.to_dict(orient="records")
    for r in rows:
        if r.get("SplitPart"):
            r["FullGroupLabel"] = f"{r['GroupCode']} (Part {r['SplitPart']})"
        else:
            r["FullGroupLabel"] = r["GroupCode"]

    return ok(rows)

# -------------------------
# Vice dean dashboard
# -------------------------
@app.get("/api/dashboard/kpis")
def dash_kpis():
    periode_id = request.args.get("periode_id", type=int)

    if periode_id:
        total_planned = query_df("""
            SELECT COUNT(DISTINCT pe.id_planning) AS n
            FROM planning_examens pe
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
        """, params=[periode_id]).iloc[0]["n"]

        expected_data = query_df("""
            SELECT 
                COALESCE(SUM(CASE WHEN f.nom LIKE 'Licence%%' THEN 4 ELSE 3 END), 0) as expected
            FROM modules m
            JOIN formations f ON m.id_formation = f.id_formation
        """, params=[])
        expected_slots = int(expected_data.iloc[0]["expected"] or 0)

        merged_count = query_df("""
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.merged_groups IS NOT NULL
            AND c.id_periode = %s
        """, params=[periode_id]).iloc[0]["n"]

        split_count = query_df("""
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.split_part IS NOT NULL
            AND c.id_periode = %s
        """, params=[periode_id]).iloc[0]["n"]

    else:
        total_planned = query_df("SELECT COUNT(*) as n FROM planning_examens", params=[]).iloc[0]["n"]
        merged_count = query_df("SELECT COUNT(DISTINCT id_planning) as n FROM planning_groupes WHERE merged_groups IS NOT NULL", params=[]).iloc[0]["n"]
        split_count = query_df("SELECT COUNT(DISTINCT id_groupe) as n FROM planning_groupes WHERE split_part IS NOT NULL", params=[]).iloc[0]["n"]
        expected_slots = 0

    total_profs = query_df("SELECT COUNT(*) as n FROM professeurs", params=[]).iloc[0]["n"]
    total_students = query_df("SELECT COUNT(*) as n FROM etudiants", params=[]).iloc[0]["n"]
    
    return ok({
        "total_planned": int(total_planned),
        "expected_slots": int(expected_slots),
        "merged_count": int(merged_count),
        "split_count": int(split_count),
        "total_profs": int(total_profs),
        "total_students": int(total_students),
    })

@app.get("/api/dashboard/room_distribution")
def dash_room_dist():
    periode_id = request.args.get("periode_id", type=int)
    if periode_id:
        df = query_df("""
            SELECT l.type, COUNT(pe.id_planning) as usage_count
            FROM lieux_examen l
            LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY l.type
        """, params=[periode_id])
    else:
        df = query_df("""
            SELECT l.type, COUNT(pe.id_planning) as usage_count
            FROM lieux_examen l
            LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            GROUP BY l.type
        """)
    return ok(df.to_dict(orient="records"))

@app.get("/api/dashboard/top_rooms")
def dash_top_rooms():
    periode_id = request.args.get("periode_id", type=int)
    if periode_id:
        df = query_df("""
            SELECT l.nom, l.type, COUNT(pe.id_planning) as sessions
            FROM lieux_examen l
            JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY l.nom, l.type
            ORDER BY sessions DESC
        """, params=[periode_id])
    else:
        df = query_df("""
            SELECT l.nom, l.type, COUNT(pe.id_planning) as sessions
            FROM lieux_examen l
            JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            GROUP BY l.nom, l.type
            ORDER BY sessions DESC
        """)
    return ok(df.to_dict(orient="records"))

@app.get("/api/dashboard/prof_load")
def dash_prof_load():
    periode_id = request.args.get("periode_id", type=int)
    if periode_id:
        df = query_df("""
            SELECT p.nom, d.nom as "Dept", COUNT(s.id_planning) as total_surveillances
            FROM professeurs p
            JOIN departements d ON p.id_dept = d.id_dept
            LEFT JOIN surveillances s ON p.id_prof = s.id_prof
            LEFT JOIN planning_examens pe ON s.id_planning = pe.id_planning
            LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY p.nom, d.nom
            ORDER BY total_surveillances DESC
        """, params=[periode_id])
    else:
        df = query_df("""
            SELECT p.nom, d.nom as "Dept", COUNT(s.id_planning) as total_surveillances
            FROM professeurs p
            JOIN departements d ON p.id_dept = d.id_dept
            LEFT JOIN surveillances s ON p.id_prof = s.id_prof
            GROUP BY p.nom, d.nom
            ORDER BY total_surveillances DESC
        """)
    return ok(df.to_dict(orient="records"))

@app.get("/api/dashboard/prof_conflicts")
def dash_prof_conflicts():
    periode_id = request.args.get("periode_id", type=int)

    df = query_df("""
        SELECT
            p.nom AS "Professor",
            c.date,
            TO_CHAR(c.heure_debut, 'HH24:MI') AS "Start",
            COUNT(DISTINCT pe.id_examen) AS "Assignments",
            STRING_AGG(
                DISTINCT m.nom || ' — ' || le.nom || ' (' || le.type || ')',
                '<br>'
            ) AS "Details"
        FROM surveillances s
        JOIN professeurs p ON p.id_prof = s.id_prof
        JOIN planning_examens pe ON pe.id_planning = s.id_planning
        JOIN examens e ON e.id_examen = pe.id_examen
        JOIN modules m ON m.id_module = e.id_module
        JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        WHERE c.id_periode = %s
        GROUP BY p.nom, c.date, c.heure_debut
        HAVING COUNT(DISTINCT pe.id_examen) > 1
        ORDER BY c.date, c.heure_debut
    """, params=[periode_id])

    return ok(df.to_dict(orient="records"))

# -------------------------
# Frontend Routes
# -------------------------
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/pages/<path:filename>')
def serve_pages(filename):
    return send_from_directory('frontend/pages', filename)

@app.route('/assets/<path:path>')
def serve_assets(path):
    return send_from_directory('frontend/assets', path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
