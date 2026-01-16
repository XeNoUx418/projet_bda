import mysql.connector
import time
import sys
from collections import defaultdict

# =========================
# 1️⃣ Database connection
# =========================
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="bac@2021",
    database="exam_timetabling"
)
cursor = conn.cursor(dictionary=True)

start_time = time.time()

try:

# =========================
# 2️⃣ Preload data
# =========================

    # Exams
    cursor.execute("SELECT id_examen, id_module FROM examens")
    exams = cursor.fetchall()

    # Time slots
    cursor.execute("""
        SELECT id_creneau, date
        FROM creneaux
        ORDER BY date, heure_debut
    """)
    slots = cursor.fetchall()

    # Rooms
    cursor.execute("""
        SELECT id_lieu, capacite
        FROM lieux_examen
        ORDER BY capacite
    """)
    rooms = cursor.fetchall()

    # Students per module
    cursor.execute("""
        SELECT id_module, COUNT(*) AS nb
        FROM inscriptions
        GROUP BY id_module
    """)
    students_per_module = {
        r["id_module"]: r["nb"] for r in cursor.fetchall()
    }

    # Student lists per module
    cursor.execute("SELECT id_module, id_etudiant FROM inscriptions")
    students_in_module = defaultdict(set)
    for r in cursor.fetchall():
        students_in_module[r["id_module"]].add(r["id_etudiant"])

    # =========================
    # 3️⃣ In-memory constraints
    # =========================

    student_exam_day = defaultdict(set)   # student → set(dates)
    room_slot_used = set()                # (room, slot)

    # =========================
    # 4️⃣ Scheduling algorithm
    # =========================

    insert_rows = []

    for exam in exams:
        exam_id = exam["id_examen"]
        module_id = exam["id_module"]
        nb_students = students_per_module.get(module_id, 0)

        placed = False

        for slot in slots:
            slot_id = slot["id_creneau"]
            exam_date = slot["date"]

            # 🚫 Student constraint: max 1 exam per day
            if any(
                exam_date in student_exam_day[s]
                for s in students_in_module[module_id]
            ):
                continue

            for room in rooms:
                room_id = room["id_lieu"]

                if room["capacite"] < nb_students:
                    continue

                if (room_id, slot_id) in room_slot_used:
                    continue

                # ✅ Valid placement
                insert_rows.append((exam_id, room_id, slot_id))
                room_slot_used.add((room_id, slot_id))

                for s in students_in_module[module_id]:
                    student_exam_day[s].add(exam_date)

                placed = True
                break

            if placed:
                break

        if not placed:
            print(f"⚠️ Could not schedule exam {exam_id}")

    # =========================
    # 5️⃣ Insert (single commit)
    # =========================

    cursor.executemany("""
        INSERT INTO planning_examens (id_examen, id_lieu, id_creneau)
        VALUES (%s, %s, %s)
    """, insert_rows)

    conn.commit()

    elapsed = time.time() - start_time

    print("✅ Exam scheduling completed")
    print(f"📊 Exams scheduled : {len(insert_rows)}")
    print(f"⏱ Execution time  : {elapsed:.2f} seconds")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.rollback()
    sys.exit(1)
finally:
    # =========================
    # 6️⃣ Cleanup
    # =========================
    if cursor:
        cursor.close()
    if conn:
        conn.close()
