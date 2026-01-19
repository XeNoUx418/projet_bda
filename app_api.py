from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import date
import subprocess
import time
import os
import sys

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
# Student schedule - CRITICAL FIX
# -------------------------
@app.get("/api/schedule")
def schedule():
    formation_id = request.args.get("formation_id", type=int)
    annee = request.args.get("annee", type=str)
    periode_id = request.args.get("periode_id", type=int)

    if not formation_id or not annee or not periode_id:
        return fail("formation_id, annee, periode_id are required")

    df = query_df("""
        SELECT
            c.date                                   AS "exam_date",
            TO_CHAR(c.date, 'Day, Month DD')         AS "DateLabel",
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
        # FIXED: Use .get() instead of direct access for NULL safety
        merged_groups = r.get("MergedGroups")
        split_part = r.get("SplitPart")
        group_code = r.get("GroupCode", "")
        
        if merged_groups:
            # MERGED CASE
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

        # CRITICAL: avoid duplicates for merged exams
        # FIXED: Convert date object to string for comparison
        exam_date = r.get("exam_date")
        if hasattr(exam_date, 'isoformat'):
            exam_date_str = exam_date.isoformat()
        else:
            exam_date_str = str(exam_date) if exam_date else None
            
        exam_signature = (
            r.get("Module"),
            exam_date_str,
            r.get("Start"),
            r.get("End"),
            r.get("Room")
        )

        existing = {
            (
                e.get("module"),
                e.get("date"),
                e.get("start"),
                e.get("end"),
                e.get("room")
            )
            for e in groups[key]["exams"]
        }

        if exam_signature not in existing:
            groups[key]["exams"].append({
                "date": exam_date_str,  # FIXED: Use converted string
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
        SELECT
            pe.id_planning,
            c.date                                   AS exam_date,
            TO_CHAR(c.date, 'Day, Month DD')         AS DateLabel,
            TO_CHAR(c.heure_debut, 'HH24:MI')        AS Start,
            TO_CHAR(c.heure_fin, 'HH24:MI')          AS End,
            m.nom                                    AS Module,
            e.duree_minutes                          AS Duration,
            le.nom                                   AS Room,
            le.type                                  AS Type,
            le.batiment                              AS Building,
            COALESCE(
                pg.merged_groups,
                CASE
                    WHEN pg.split_part IS NULL THEN g.code_groupe
                    ELSE g.code_groupe || ' (Part ' || pg.split_part || ')'
                END
            ) AS GroupLabel
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
        GROUP BY pe.id_planning, c.date, c.heure_debut, c.heure_fin, m.nom, e.duree_minutes, le.nom, le.type, le.batiment, pg.merged_groups, g.code_groupe, pg.split_part
        ORDER BY c.date, c.heure_debut
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
    start = time.time()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    script_path = os.path.join(script_dir, "generate_assign.py")

    if not os.path.exists(script_path):
        return fail(f"Script not found at {script_path}", 500)

    try:
        result = subprocess.run(
            [sys.executable, script_path, str(pid)],
            capture_output=True,
            text=True,
            timeout=300
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            return fail(result.stderr or result.stdout or "Generation failed", 500)

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
            "logs": result.stdout
        })

    except subprocess.TimeoutExpired:
        return fail("Generation script timed out (max 5 minutes)", 500)
    except Exception as e:
        return fail(f"Generation error: {str(e)}", 500)

@app.delete("/api/periodes/<int:pid>/planning")
def delete_planning(pid: int):
    conn = get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT delete_planning_for_period(%s)", (pid,))
        conn.commit()
        return ok({"deleted_period": pid})
    finally:
        conn.close()

@app.get("/api/periodes/<int:pid>/preview")
def preview(pid: int):
    limit = request.args.get("limit", default=100, type=int)
    df = query_df("""
        SELECT
            c.date AS Date,
            TO_CHAR(c.heure_debut, 'HH24:MI') AS Start,
            TO_CHAR(c.heure_fin, 'HH24:MI') AS End,
            m.nom AS Module,
            le.nom AS Room
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

@app.get("/api/periodes/<int:pid>/conflicts/rooms")
def room_conflicts(pid: int):
    df = query_df("""
        SELECT
            le.nom AS Room,
            c.date,
            TO_CHAR(c.heure_debut, 'HH24:MI') AS Start,
            COUNT(*) AS Exams
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
            TO_CHAR(c.date, 'Day, Month DD')         AS DateLabel,
            TO_CHAR(c.heure_debut, 'HH24:MI')        AS Start,
            TO_CHAR(c.heure_fin, 'HH24:MI')          AS End,
            m.nom                                    AS Module,
            e.duree_minutes                          AS Duration,
            le.nom                                   AS Room,
            le.type                                  AS Type,
            le.batiment                              AS Building,
            g.code_groupe                            AS GroupCode,
            pg.split_part                            AS SplitPart,
            pg.merged_groups                         AS MergedGroups
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
            WHERE (%s IS NULL OR c.id_periode = %s)
        """, params=[periode_id, periode_id]).iloc[0]["n"]

        expected_data = query_df("""
            SELECT 
                SUM(CASE WHEN f.nom LIKE 'Licence%' THEN 4 ELSE 3 END) as expected
            FROM modules m
            JOIN formations f ON m.id_formation = f.id_formation
        """)
        expected_slots = int(expected_data.iloc[0]["expected"])

        merged_count = query_df("""
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.merged_groups IS NOT NULL
            AND (%s IS NULL OR c.id_periode = %s)
        """, params=[periode_id, periode_id]).iloc[0]["n"]

        split_count = query_df("""
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.split_part IS NOT NULL
            AND (%s IS NULL OR c.id_periode = %s)
        """, params=[periode_id, periode_id]).iloc[0]["n"]

    else:
        total_planned = query_df("SELECT COUNT(*) as n FROM planning_examens").iloc[0]["n"]
        merged_count = query_df("SELECT COUNT(DISTINCT id_planning) as n FROM planning_groupes WHERE merged_groups IS NOT NULL").iloc[0]["n"]
        split_count = query_df("SELECT COUNT(DISTINCT id_groupe) as n FROM planning_groupes WHERE split_part IS NOT NULL").iloc[0]["n"]
        expected_slots = 0

    total_profs = query_df("SELECT COUNT(*) as n FROM professeurs").iloc[0]["n"]
    total_students = query_df("SELECT COUNT(*) as n FROM etudiants").iloc[0]["n"]
    
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
            SELECT p.nom, d.nom as Dept, COUNT(s.id_planning) as total_surveillances
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
            SELECT p.nom, d.nom as Dept, COUNT(s.id_planning) as total_surveillances
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
            p.nom AS Professor,
            c.date,
            TO_CHAR(c.heure_debut, 'HH24:MI') AS Start,
            COUNT(DISTINCT pe.id_examen) AS Assignments,
            STRING_AGG(
                DISTINCT m.nom || ' — ' || le.nom || ' (' || le.type || ')',
                '<br>'
            ) AS Details
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
