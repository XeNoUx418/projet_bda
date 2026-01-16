import streamlit as st
import time
import subprocess
from datetime import date
from db import query_df, get_conn

# ----------------------------
# CONFIG
# ----------------------------
st.set_page_config(page_title="Exam Timetabling", layout="wide")

st.markdown(
    """
    <style>
      .block-container { padding-top: 1.0rem; padding-bottom: 2.0rem; max-width: 1350px; }
      header, footer {visibility: hidden;}

      [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      }

      .card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(51,65,85,0.12);
        background: #ffffff;
        box-shadow: 0 4px 12px rgba(51,65,85,0.08);
      }

      .muted { color: rgba(71,85,105,0.75); }
      .title { font-size: 44px; font-weight: 700; margin: 0; letter-spacing: -0.5px; color: rgba(15,23,42,0.92); }
      .subtitle { margin: 6px 0 0 0; font-size: 15px; color: rgba(71,85,105,0.75); }

      div.stButton > button {
        border-radius: 10px !important;
        padding: 0.65rem 1.0rem !important;
        border: 1px solid rgba(51,65,85,0.12) !important;
        background: #ffffff !important;
        color: rgba(15,23,42,0.92) !important;
        font-weight: 500 !important;
      }
      div.stButton > button:hover {
        border: 1px solid rgba(51,65,85,0.20) !important;
        background: rgba(51,65,85,0.04) !important;
      }

      [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(51,65,85,0.12);
      }

      [data-testid="stMetricValue"] {
        color: #2563eb;
      }
    </style>
    """,
    unsafe_allow_html=True
)

# ----------------------------
# STATE
# ----------------------------
if "role" not in st.session_state:
    st.session_state.role = None
if "id_etudiant" not in st.session_state:
    st.session_state.id_etudiant = None
if "id_prof" not in st.session_state:
    st.session_state.id_prof = None

def go_menu():
    st.session_state.role = None
    st.session_state.id_etudiant = None
    st.session_state.id_prof = None
    st.rerun()

def safe_count(sql, default="—"):
    try:
        return query_df(sql).iloc[0]["n"]
    except Exception:
        return default

def header_block():
    left, right = st.columns([8, 2])
    with left:
        st.markdown(
            """
            <p class="title">Exam Timetabling</p>
            <p class="subtitle muted">Academic Examination Scheduling System</p>
            """,
            unsafe_allow_html=True
        )
    with right:
        if st.session_state.role is not None:
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            if st.button("Back to menu", use_container_width=True):
                go_menu()

header_block()
st.divider()

# ----------------------------
# MENU
# ----------------------------
if st.session_state.role is None:
    st.markdown(
        """
        <div class="card">
          <h2 style="margin:0; font-weight:900; letter-spacing:-0.4px;">Select role</h2>
          <p class="muted" style="margin:8px 0 0 0;">
            Choose a view to consult schedules and dashboards. No login mode (demo).
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

    b1, b2, b3, b4 = st.columns(4)
    with b1:
        if st.button("Student", use_container_width=True):
            st.session_state.role = "etudiant"
            st.rerun()
    with b2:
        if st.button("Professor", use_container_width=True):
            st.session_state.role = "prof"
            st.rerun()
    with b3:
        if st.button("Manager", use_container_width=True):
            st.session_state.role = "chef"
            st.rerun()
    with b4:
        if st.button("Vice Dean", use_container_width=True):
            st.session_state.role = "doyen"
            st.rerun()

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Students", safe_count("SELECT COUNT(*) AS n FROM etudiants"))
    k2.metric("Professors", safe_count("SELECT COUNT(*) AS n FROM professeurs"))
    k3.metric("Exams", safe_count("SELECT COUNT(*) AS n FROM examens"))
    k4.metric("Planning rows", safe_count("SELECT COUNT(*) AS n FROM planning_examens"))

    st.stop()

# ----------------------------
# STUDENT VIEW
# ----------------------------
st.markdown(
    """
    <style>
      .block-container { padding-top: 1.0rem; padding-bottom: 2.0rem; max-width: 1350px; }
      header, footer {visibility: hidden;}

      [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
      }

      .card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid rgba(51,65,85,0.12);
        background: #ffffff;
        box-shadow: 0 4px 12px rgba(51,65,85,0.08);
      }

      .muted { color: rgba(71,85,105,0.75); }
      .title { font-size: 44px; font-weight: 700; margin: 0; letter-spacing: -0.5px; color: rgba(15,23,42,0.92); }
      .subtitle { margin: 6px 0 0 0; font-size: 15px; color: rgba(71,85,105,0.75); }

      div.stButton > button {
        border-radius: 10px !important;
        padding: 0.65rem 1.0rem !important;
        border: 1px solid rgba(51,65,85,0.12) !important;
        background: #ffffff !important;
        color: rgba(15,23,42,0.92) !important;
        font-weight: 500 !important;
      }
      div.stButton > button:hover {
        border: 1px solid rgba(51,65,85,0.20) !important;
        background: rgba(51,65,85,0.04) !important;
      }

      [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(51,65,85,0.12);
      }

      .group-header {
        background: linear-gradient(90deg, #2563eb 0%, #0891b2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 10px;
        margin: 16px 0 10px 0;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 13px;
      }

      .exam-card {
        background: #ffffff;
        border: 1px solid rgba(51,65,85,0.12);
        border-left: 4px solid #2563eb;
        padding: 14px;
        margin-bottom: 10px;
        border-radius: 10px;
        transition: all 0.2s;
      }
      .exam-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(51,65,85,0.08);
      }
    </style>
    """,
    unsafe_allow_html=True
)

if st.session_state.role == "etudiant":

    st.markdown(
        """
        <div class="card">
          <h3 style="margin:0;">📅 Exam Schedule</h3>
          <p class="muted" style="margin:8px 0 0 0;">
            Browse exam planning by department, formation and academic year.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # =========================
    # 1. Filters
    # =========================
    col1, col2, col3 = st.columns(3)

    with col1:
        depts = query_df("SELECT id_dept, nom FROM departements ORDER BY nom")
        if depts.empty:
            st.error("No departments found.")
            st.stop()
        selected_dept_name = st.selectbox("📚 Department", depts["nom"].tolist())
        selected_dept = int(depts.loc[depts["nom"] == selected_dept_name, "id_dept"].iloc[0])

    with col2:
        formations = query_df("""
            SELECT id_formation, nom FROM formations WHERE id_dept = %s ORDER BY nom
        """, params=[selected_dept])
        if formations.empty:
            st.warning("No formations found for this department.")
            st.stop()
        formation_name = st.selectbox("🎓 Formation", formations["nom"].tolist())
        id_formation = int(formations.loc[formations["nom"] == formation_name, "id_formation"].iloc[0])

    with col3:
        annees = query_df("""
            SELECT DISTINCT annee FROM modules WHERE id_formation = %s AND annee IS NOT NULL ORDER BY annee
        """, params=[id_formation])
        if annees.empty:
            st.warning("No academic years found for this formation.")
            st.stop()
        annee = st.selectbox("📚 Academic Year", annees["annee"].tolist())

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # =========================
    # Session filter (Exam period)
    # =========================
    sessions = query_df("""
        SELECT DISTINCT
            p.id_periode,
            CONCAT(
                p.description,
                ' (',
                DATE_FORMAT(p.date_debut, '%d %b %Y'),
                ' → ',
                DATE_FORMAT(p.date_fin, '%d %b %Y'),
                ')'
            ) AS label
        FROM periodes_examens p
        JOIN creneaux c ON c.id_periode = p.id_periode
        JOIN planning_examens pe ON pe.id_creneau = c.id_creneau
        JOIN examens e ON e.id_examen = pe.id_examen
        JOIN modules m ON m.id_module = e.id_module
        WHERE m.id_formation = %s
        AND m.annee = %s
        ORDER BY p.date_debut DESC
    """, params=[id_formation, annee])

    if sessions.empty:
        st.warning("No exam sessions found for this formation and year.")
        st.stop()

    session_label = st.selectbox("🗓 Exam Session", sessions["label"].tolist())
    id_periode = int(
        sessions.loc[sessions["label"] == session_label, "id_periode"].iloc[0]
    )


    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

    # =========================
    # 2. Query Exams (Group specific)
    # =========================
    sql = """
        SELECT
            c.date                                   AS exam_date,
            DATE_FORMAT(c.date, '%W, %M %d')      AS Date,
            TIME_FORMAT(c.heure_debut, '%H:%i')    AS Start,
            TIME_FORMAT(c.heure_fin, '%H:%i')      AS End,
            m.nom                                    AS Module,
            e.duree_minutes                          AS Duration,
            le.nom                                   AS Room,
            le.type                                  AS Type,
            le.batiment                              AS Building,
            g.code_groupe                            AS GroupCode,
            pg.split_part                            AS SplitPart
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
    """

    df = query_df(sql, params=[id_formation, annee, id_periode])

    # =========================
    # 3. Display Results
    # =========================
    if df.empty:
        st.info("ℹ️ No exams found for this selection.")
        st.stop()

    # Create distinct "Group Label" (G1, G1 (P1), etc.)
    df['FullGroupLabel'] = df.apply(
        lambda x: f"{x['GroupCode']} (Part {x['SplitPart']})" if x['SplitPart'] else x['GroupCode'], axis=1
    )

    unique_groups = df['FullGroupLabel'].unique()
    
    for group_label in unique_groups:
        group_df = df[df['FullGroupLabel'] == group_label]
        
        # Colorful Group Header
        st.markdown(f'<div class="group-header">👥 Group: {group_label}</div>', unsafe_allow_html=True)
        
        # Table-like Display for this specific group
        for _, exam in group_df.iterrows():
            st.markdown(f"""
                <div class="exam-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <span style="font-size: 1.1em; font-weight: 700; color: #fff;">📚 {exam['Module']}</span><br/>
                            <span class="muted" style="font-size: 0.9em;">📅 {exam['Date']} | ⏰ {exam['Start']} - {exam['End']}</span>
                        </div>
                        <div style="text-align: right;">
                            <span style="background: #4facfe; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold;">
                                {exam['Room']}
                            </span><br/>
                            <span class="muted" style="font-size: 0.8em;">🏢 {exam['Building']} ({exam['Type'].upper()})</span>
                        </div>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)
    
    # Export all results
    csv_df = df[['Date', 'Start', 'End', 'Module', 'Duration', 'Room', 'Building', 'FullGroupLabel']].copy()
    st.download_button(
        label="💾 Download Full CSV Schedule",
        data=csv_df.to_csv(index=False).encode("utf-8"),
        file_name=f"exam_schedule_{formation_name}_{annee}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.stop()

# ----------------------------
# PROFESSOR VIEW
# ----------------------------
if st.session_state.role == "prof":
    st.markdown(
        """
        <div class="card">
          <h3 style="margin:0;">Professor schedule</h3>
          <p class="muted" style="margin:8px 0 0 0;">Select a professor and a period to display invigilation.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    profs = query_df("""
        SELECT id_prof,
               CONCAT(nom, ' (', specialite, ')') AS label
        FROM professeurs
        ORDER BY nom
    """)
    if profs.empty:
        st.error("No professors found.")
        st.stop()

    c1, c2, c3 = st.columns([2.4, 1, 1])
    with c1:
        label = st.selectbox("Professor", profs["label"].tolist(), index=0)
        st.session_state.id_prof = int(profs.loc[profs["label"] == label, "id_prof"].iloc[0])
    with c2:
        d1 = st.date_input("Start date", value=date(2026, 1, 6), key="p1")
    with c3:
        d2 = st.date_input("End date", value=date(2026, 1, 26), key="p2")

    if d1 > d2:
        st.error("Start date must be before end date.")
        st.stop()

    sql = """
        SELECT
            pe.id_planning,

            c.date                                   AS exam_date,
            DATE_FORMAT(c.date, '%W, %M %d')         AS Date,
            TIME_FORMAT(c.heure_debut, '%H:%i')      AS Start,
            TIME_FORMAT(c.heure_fin, '%H:%i')        AS End,

            m.nom                                    AS Module,
            e.duree_minutes                          AS Duration,

            le.nom                                   AS Room,
            le.type                                  AS Type,
            le.batiment                              AS Building,

            COALESCE(
                pg.merged_groups,
                CASE
                    WHEN pg.split_part IS NULL THEN g.code_groupe
                    ELSE CONCAT(g.code_groupe, ' (Part ', pg.split_part, ')')
                END
            ) AS GroupLabel

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

        GROUP BY pe.id_planning
        ORDER BY c.date, c.heure_debut;

    """
    df = query_df(sql, params=[st.session_state.id_prof, d1, d2])

    m1, m2, m3 = st.columns(3)
    m1.metric("surveillances", int(len(df)))
    m2.metric("Professor", label.split("(")[0].strip())
    m3.metric("Period", f"{d1.strftime('%d/%m')} - {d2.strftime('%d/%m')}")

    if df.empty:
        st.info("No surveillances found for this selection.")
        st.stop()

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "Download CSV",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=f"professor_schedule_{st.session_state.id_prof}.csv",
        mime="text/csv",
        use_container_width=True
    )
    st.stop()

# ----------------------------
# MANAGER DASHBOARD (CHEF)
# ----------------------------
if st.session_state.role == "chef":

    st.markdown(
        """
        <div class="card">
          <h3 style="margin:0;">Manager dashboard</h3>
          <p class="muted" style="margin:8px 0 0 0;">
            Manage exam periods, generate planning, and monitor conflicts.
          </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    # ----------------------------
    # GLOBAL METRICS
    # ----------------------------
    a, b, c, d = st.columns(4)
    a.metric("Exams", safe_count("SELECT COUNT(*) AS n FROM examens"))
    b.metric("Planning rows", safe_count("SELECT COUNT(*) AS n FROM planning_examens"))
    c.metric("Rooms", safe_count("SELECT COUNT(*) AS n FROM lieux_examen"))
    d.metric("surveillances", safe_count("SELECT COUNT(*) AS n FROM surveillances"))

    st.divider()

    # ----------------------------
    # CREATE EXAM PERIOD
    # ----------------------------
    st.subheader("Create exam period")

    with st.form("period_form"):
        col1, col2 = st.columns(2)
        with col1:
            d_start = st.date_input("Start date")
        with col2:
            d_end = st.date_input("End date")

        description = st.text_input("Description", "Session d'examen")
        submit = st.form_submit_button("Create period")

    if submit:
        if d_start > d_end:
            st.error("Start date must be before end date.")
        else:
            conn = get_conn()
            cur = conn.cursor()

            cur.execute(
                """
                INSERT INTO periodes_examens (date_debut, date_fin, description)
                VALUES (%s, %s, %s)
                """,
                (d_start, d_end, description)
            )

            period_id = cur.lastrowid

            # Generate slots ONLY for this period
            cur.execute("CALL GenerateTimeSlotsForPeriod(%s)", (period_id,))

            conn.commit()
            cur.close()
            conn.close()

            st.success("Exam period created and time slots generated.")
            time.sleep(1)
            st.rerun()

    st.divider()

    # ----------------------------
    # PERIODS TABLE
    # ----------------------------
    st.subheader("Exam periods")

    periods = query_df("""
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
                )
                THEN 1 ELSE 0
            END AS has_planning
        FROM periodes_examens p
        ORDER BY p.date_debut DESC
    """)

    if periods.empty:
        st.info("No exam periods defined.")
        st.stop()

    for _, row in periods.iterrows():
        with st.container():
            c1, c2, c3 = st.columns([4, 2, 2])

            c1.markdown(f"**{row['description']}**")
            c1.caption(f"{row['date_debut']} → {row['date_fin']}")

            if row["has_planning"]:
                c2.success("Planning generated")

                col_view, col_delete = c3.columns(2)

                if col_view.button("👁 View", key=f"view_{row['id_periode']}"):
                    st.session_state.view_period = int(row["id_periode"])

                if col_delete.button("🗑 Delete", key=f"del_{row['id_periode']}"):
                    st.session_state.delete_period = int(row["id_periode"])

            else:
                c2.warning("No planning")
                if c3.button("⚙ Generate", key=f"gen_{row['id_periode']}"):
                    st.session_state.generate_period = int(row["id_periode"])

    # ----------------------------
    # DELETE PLANNING (BACKEND)
    # ----------------------------
    if "delete_period" in st.session_state:
        pid = st.session_state.delete_period

        st.warning(
            f"⚠️ You are about to permanently delete the planning for period {pid}."
        )

        c1, c2 = st.columns(2)

        if c1.button("❌ Cancel"):
            del st.session_state.delete_period
            st.rerun()

        if c2.button("🗑 Confirm delete"):
            conn = get_conn()
            cur = conn.cursor()

            cur.execute("CALL DeletePlanningForPeriod(%s)", (pid,))
            conn.commit()

            cur.close()
            conn.close()

            st.success(f"Planning for period {pid} deleted successfully.")

            del st.session_state.delete_period
            time.sleep(1)
            st.rerun()



            st.divider()

    # ----------------------------
    # GENERATE PLANNING (BACKEND)
    # ----------------------------
    if "generate_period" in st.session_state:
        pid = st.session_state.generate_period

        with st.spinner(f"Generating planning for period {pid}..."):
            start = time.time()
            result = subprocess.run(
                ["python", "generate_assign.py", str(pid)],
                capture_output=True,
                text=True
            )
            elapsed = time.time() - start

        if result.returncode == 0:
            st.success(f"Planning generated for period {pid}")
            st.info(f"⏱ Execution time: {elapsed:.2f} seconds")
            with st.expander("Logs"):
                st.code(result.stdout)
        else:
            st.error("Generation failed")
            st.code(result.stderr)

        del st.session_state.generate_period
        time.sleep(1)
        st.rerun()

    # ----------------------------
    # PERIOD-SPECIFIC PREVIEW
    # ----------------------------
    if "view_period" in st.session_state:
        pid = st.session_state.view_period

        st.subheader(f"Planning preview (Period {pid})")

        preview = query_df("""
            SELECT
                c.date AS Date,
                TIME_FORMAT(c.heure_debut,'%H:%i') AS Start,
                TIME_FORMAT(c.heure_fin,'%H:%i') AS End,
                m.nom AS Module,
                le.nom AS Room
            FROM planning_examens pe
            JOIN examens e       ON e.id_examen = pe.id_examen
            JOIN modules m       ON m.id_module = e.id_module
            JOIN creneaux c      ON c.id_creneau = pe.id_creneau
            JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
            WHERE c.id_periode = %s
            ORDER BY c.date, c.heure_debut
            LIMIT 100
        """, [pid])

        st.dataframe(preview, use_container_width=True, hide_index=True)

        # ----------------------------
        # CONFLICTS (PER PERIOD)
        # ----------------------------
        st.subheader("Room/slot conflicts")

        conflicts = query_df("""
            SELECT
                le.nom AS Room,
                c.date,
                TIME_FORMAT(c.heure_debut,'%H:%i') AS Start,
                COUNT(*) AS Exams
            FROM planning_examens pe
            JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
            JOIN creneaux c      ON c.id_creneau = pe.id_creneau
            WHERE c.id_periode = %s
            GROUP BY pe.id_lieu, c.date, c.heure_debut
            HAVING COUNT(*) > 1
            ORDER BY c.date, c.heure_debut
        """, [pid])

        if conflicts.empty:
            st.success("No conflicts detected.")
        else:
            st.dataframe(conflicts, use_container_width=True, hide_index=True)

    st.stop()



# ----------------------------
# VICE DEAN DASHBOARD
# ----------------------------
if st.session_state.role == "doyen":
    st.markdown('<div class="main-title">Strategic Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle-text">Global academic KPIs and capacity analysis for the current session</div>', unsafe_allow_html=True)

    # 1. TOP LEVEL KPIs (Summary Cards)
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    
    # Calculate global stats
    total_planned = query_df("SELECT COUNT(*) as n FROM planning_examens").iloc[0]['n']
    merged_count = query_df("SELECT COUNT(DISTINCT id_planning) as n FROM planning_groupes WHERE merged_groups IS NOT NULL").iloc[0]['n']
    split_count = query_df("SELECT COUNT(DISTINCT id_groupe) as n FROM planning_groupes WHERE split_part IS NOT NULL").iloc[0]['n']
    total_profs = query_df("SELECT COUNT(*) as n FROM professeurs").iloc[0]['n']
    
    with kpi_col1:
        st.metric("Total Exams Planned", total_planned)
    with kpi_col2:
        st.metric("Merged Exams (Amphis)", merged_count)
    with kpi_col3:
        st.metric("Groups Split", split_count)
    with kpi_col4:
        st.metric("Total Professors", total_profs)

    st.markdown("---")

    # 2. ROOM UTILIZATION & DISTRIBUTION
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("📊 Room Type Distribution")
        room_dist = query_df("""
            SELECT l.type, COUNT(pe.id_planning) as usage_count
            FROM lieux_examen l
            LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            GROUP BY l.type
        """)
        if not room_dist.empty:
            # We'll use a simple bar chart since we are in a single-file environment
            st.bar_chart(room_dist.set_index('type'))
        else:
            st.info("No room usage data yet.")

    with col_b:
        st.subheader("📍 Top Utilized Rooms")
        top_rooms = query_df("""
            SELECT l.nom, l.type, COUNT(pe.id_planning) as sessions
            FROM lieux_examen l
            JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            GROUP BY l.id_lieu
            ORDER BY sessions DESC
            LIMIT 5
        """)
        st.table(top_rooms)

    # 3. MERGE & SPLIT ANALYSIS
    st.markdown("---")
    st.subheader("🔄 Group Handling Analysis")
    tab1, tab2 = st.tabs(["Merged Groups (Amphi Usage)", "Split Groups (Small Room Logic)"])
    
    with tab1:
        # Show which groups were merged together
        merge_details = query_df("""
            SELECT pe.id_planning, m.nom as Module, l.nom as Room, pg.merged_groups
            FROM planning_groupes pg
            JOIN planning_examens pe ON pg.id_planning = pe.id_planning
            JOIN examens e ON pe.id_examen = e.id_examen
            JOIN modules m ON e.id_module = m.id_module
            JOIN lieux_examen l ON pe.id_lieu = l.id_lieu
            WHERE pg.merged_groups IS NOT NULL
            GROUP BY pe.id_planning
        """)
        if merge_details.empty:
            st.info("No merged groups found.")
        else:
            st.dataframe(merge_details, use_container_width=True, hide_index=True)

    with tab2:
        # Show which groups were split across rooms
        split_details = query_df("""
            SELECT g.code_groupe, m.nom as Module, COUNT(pg.id_planning) as rooms_count
            FROM planning_groupes pg
            JOIN groupes g ON pg.id_groupe = g.id_groupe
            JOIN planning_examens pe ON pg.id_planning = pe.id_planning
            JOIN examens e ON pe.id_examen = e.id_examen
            JOIN modules m ON e.id_module = m.id_module
            WHERE pg.split_part IS NOT NULL
            GROUP BY g.id_groupe, m.id_module
        """)
        if split_details.empty:
            st.info("No groups were split.")
        else:
            st.dataframe(split_details, use_container_width=True, hide_index=True)

    # 4. PROFESSOR LOAD KPI
    st.markdown("---")
    st.subheader("👨‍🏫 Professor Workload (Surveillance)")
    prof_load = query_df("""
        SELECT p.nom, d.nom as Dept, COUNT(s.id_planning) as total_surveillances
        FROM professeurs p
        JOIN departements d ON p.id_dept = d.id_dept
        LEFT JOIN surveillances s ON p.id_prof = s.id_prof
        GROUP BY p.id_prof
        ORDER BY total_surveillances DESC
    """)
    st.dataframe(prof_load, use_container_width=True, hide_index=True)

    # 5. CONFLICT CHECKER
    st.markdown("---")
    st.subheader("🚨 Critical Conflict Warnings")
    conflits_prof = query_df("""
        SELECT p.nom AS Professor, c.date, TIME_FORMAT(c.heure_debut,'%H:%i') AS Start, COUNT(*) AS Assignments
        FROM surveillances s
        JOIN professeurs p ON p.id_prof = s.id_prof
        JOIN planning_examens pe ON pe.id_planning = s.id_planning
        JOIN creneaux c ON c.id_creneau = pe.id_creneau
        GROUP BY s.id_prof, c.date, c.heure_debut
        HAVING COUNT(*) > 1
    """)
    if conflits_prof.empty:
        st.success("✅ No Professor Overlaps Detected.")
    else:
        st.warning("⚠️ Double assignments found for the following:")
        st.dataframe(conflits_prof, use_container_width=True, hide_index=True)

    st.stop()