#!/usr/bin/env python3
import sys
from collections import defaultdict
from datetime import datetime

# Import PostgreSQL connector and our centralized DB config
from db import get_conn
from psycopg2.extras import RealDictCursor

# --------------------------------------------------
# MAIN SCHEDULER
# --------------------------------------------------
class ExamScheduler:

    def __init__(self, period_id: int):
        self.period_id = period_id
        self.conn = get_conn()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)

        # Global round-robin pointers
        self.slot_ptr = 0
        self.salle_ptr = 0
        self.amphi_ptr = 0

    # --------------------------------------------------
    # LOAD DATA
    # --------------------------------------------------
    def load_data(self):

        # ---- Slots (exclude Friday)
        self.cursor.execute("""
            SELECT id_creneau, date, heure_debut
            FROM creneaux
            WHERE id_periode = %s
            ORDER BY date, heure_debut
        """, (self.period_id,))
        
        all_slots = self.cursor.fetchall()
        
        # Filter out Fridays (weekday 4)
        self.slots = [
            s for s in all_slots
            if s["date"].weekday() != 4
        ]

        if not self.slots:
            raise RuntimeError("No usable time slots found")

        # ---- Rooms
        self.cursor.execute("""
            SELECT id_lieu, capacite, type
            FROM lieux_examen
            ORDER BY capacite
        """)
        rooms = self.cursor.fetchall()
        self.salles = [r for r in rooms if r["type"] == "salle"]
        self.amphis = [r for r in rooms if r["type"] == "amphi"]

        # ---- Departments
        self.cursor.execute("SELECT id_dept FROM departements ORDER BY id_dept")
        self.departments = [d["id_dept"] for d in self.cursor.fetchall()]

        # ---- Formations by department
        self.cursor.execute("""
            SELECT id_formation, id_dept
            FROM formations
        """)
        self.formations_by_dept = defaultdict(list)
        for f in self.cursor.fetchall():
            self.formations_by_dept[f["id_dept"]].append(f["id_formation"])

        # ---- Groups
        self.cursor.execute("""
            SELECT id_groupe, id_formation, annee, effectif, code_groupe
            FROM groupes
            ORDER BY id_formation, annee, code_groupe
        """)
        self.groups = self.cursor.fetchall()

        self.groups_by_fy = defaultdict(list)
        for g in self.groups:
            self.groups_by_fy[(g["id_formation"], g["annee"])].append(g)

        # ---- Exams
        self.cursor.execute("""
            SELECT
                e.id_examen,
                m.id_module,
                m.id_formation,
                m.annee,
                f.id_dept
            FROM examens e
            JOIN modules m ON m.id_module = e.id_module
            JOIN formations f ON f.id_formation = m.id_formation
            ORDER BY m.id_formation, m.annee, m.id_module
        """)
        self.exams = self.cursor.fetchall()

        # ---- Professors
        self.cursor.execute("""
            SELECT id_prof, id_dept
            FROM professeurs
        """)
        self.professors = self.cursor.fetchall()

        self.profs_by_dept = defaultdict(list)
        for p in self.professors:
            self.profs_by_dept[p["id_dept"]].append(p)

        # ---- Surveillance counters
        self.prof_daily = defaultdict(lambda: defaultdict(int))
        self.prof_total = defaultdict(int)
        
        # Track which professors are assigned to which time slots
        # Format: prof_slot_assignments[prof_id][(date, time)] = exam_id
        self.prof_slot_assignments = defaultdict(dict)


    # --------------------------------------------------
    # PACK CREATION (MERGE / SPLIT LOGIC)
    # --------------------------------------------------
    def create_packs(self, groups, annee):
        """
        Licence logic:
        - Merge (G01+G02), (G03+G04)
        - Split last group (G05)
        
        Master logic (unchanged):
        - Merge 2 groups
        - Split last if odd
        """

        packs = []

        # Ensure deterministic order: G01, G02, ...
        groups = sorted(groups, key=lambda g: g["code_groupe"])

        i = 0
        n = len(groups)

        # ======================
        # LICENCE CASE
        # ======================
        if annee.startswith("L"):
            while i < n:
                # Merge pairs
                if i + 1 < n:
                    packs.append({
                        "type": "amphi",
                        "groups": [groups[i], groups[i + 1]],
                        "capacity": groups[i]["effectif"] + groups[i + 1]["effectif"],
                        "split_part": None
                    })
                    i += 2
                else:
                    half = groups[i]["effectif"] // 2
                    packs.append({
                        "type": "salle",
                        "groups": [groups[i]],
                        "capacity": half,
                        "split": True,
                        "split_part": 'A'
                    })
                    packs.append({
                        "type": "salle",
                        "groups": [groups[i]],
                        "capacity": half,
                        "split": True,
                        "split_part": 'B'
                    })
                    i += 1

            return packs

        # ======================
        # MASTER CASE (unchanged)
        # ======================
        while i < n:
            if i + 1 < n:
                packs.append({
                    "type": "amphi",
                    "groups": [groups[i], groups[i + 1]],
                    "capacity": groups[i]["effectif"] + groups[i + 1]["effectif"],
                    "split_part": None
                })
                i += 2
            else:
                half = groups[i]["effectif"] // 2
                packs.append({
                    "type": "salle",
                    "groups": [groups[i]],
                    "capacity": half,
                    "split": True,
                    "split_part": 'A'
                })
                packs.append({
                    "type": "salle",
                    "groups": [groups[i]],
                    "capacity": half,
                    "split": True,
                    "split_part": 'B'
                })
                i += 1

        return packs


    # --------------------------------------------------
    # SLOT SELECTION
    # --------------------------------------------------
    def find_slot(self, packs):
        attempts = 0
        while attempts < len(self.slots):
            slot = self.slots[self.slot_ptr % len(self.slots)]
            self.slot_ptr += 1
            attempts += 1

            conflict = False
            for p in packs:
                for g in p["groups"]:
                    if self.group_has_exam_same_day(g["id_groupe"], slot["date"]):
                        conflict = True
                        break
                if conflict:
                    break

            if not conflict:
                return slot

        return None

    # --------------------------------------------------
    # ROOM ASSIGNMENT
    # --------------------------------------------------
    def assign_room(self, pack):
        if pack["type"] == "amphi":
            candidates = [r for r in self.amphis if r["capacite"] >= pack["capacity"]]
            if not candidates:
                return None
            room = candidates[self.amphi_ptr % len(candidates)]
            self.amphi_ptr += 1
            return room
        else:
            candidates = [r for r in self.salles if r["capacite"] >= pack["capacity"]]
            if not candidates:
                return None
            room = candidates[self.salle_ptr % len(candidates)]
            self.salle_ptr += 1
            return room

    # --------------------------------------------------
    # CONFLICT CHECK
    # --------------------------------------------------
    def group_has_exam_same_day(self, group_id, date):
        self.cursor.execute("""
            SELECT 1
            FROM planning_examens pe
            JOIN planning_groupes pg ON pg.id_planning = pe.id_planning
            JOIN creneaux c ON c.id_creneau = pe.id_creneau
            WHERE pg.id_groupe = %s AND c.date = %s
            LIMIT 1
        """, (group_id, date))
        return self.cursor.fetchone() is not None
    
    def required_surveillants(self, room_type):
        """
        Returns number of professors needed to supervise an exam
        depending on the room type.
        """
        if room_type == "amphi":
            return 3
        return 2


    def pick_professors(self, exam_dept, room_type, exam_date, slot_time, exam_id):
        """
        Select professors for an exam session (ONCE per exam+slot).
        Returns list of professor IDs and updates counters.
        
        CRITICAL: Checks that professors are not already assigned at this time slot.
        """
        needed = self.required_surveillants(room_type)
        selected = []

        # 1️⃣ Priority: same department
        priority = self.profs_by_dept.get(exam_dept, [])

        # 2️⃣ Fallback: other departments
        others = [p for p in self.professors if p not in priority]

        # 3️⃣ Combined candidates
        candidates = priority + others

        # 4️⃣ Sort by fairness (least assigned goes first)
        candidates = sorted(
            candidates,
            key=lambda p: self.prof_total[p["id_prof"]]
        )

        for prof in candidates:
            pid = prof["id_prof"]

            # ✅ CRITICAL CHECK: Is this professor already assigned at this time slot?
            slot_key = (exam_date, slot_time)
            if slot_key in self.prof_slot_assignments[pid]:
                # Professor is already supervising another exam at this time
                continue

            # Max 3 exams per day
            if self.prof_daily[pid][exam_date] >= 3:
                continue

            selected.append(pid)
            
            if len(selected) == needed:
                break

        # Update counters ONCE for all selected professors
        for pid in selected:
            self.prof_daily[pid][exam_date] += 1
            self.prof_total[pid] += 1
            
            # ✅ Mark this professor as assigned to this time slot
            slot_key = (exam_date, slot_time)
            self.prof_slot_assignments[pid][slot_key] = exam_id

        if len(selected) < needed:
            print(f"[WARNING] Could only assign {len(selected)}/{needed} professors for exam {exam_id}")
        
        return selected


    # --------------------------------------------------
    # MAIN GENERATION
    # --------------------------------------------------
    def generate(self):

        self.load_data()

        # ---- Build waves
        exams_by_fy = defaultdict(list)
        for e in self.exams:
            exams_by_fy[(e["id_formation"], e["annee"])].append(e)

        for k in exams_by_fy:
            exams_by_fy[k].sort(key=lambda x: x["id_module"])

        waves = defaultdict(list)
        for (formation, annee), exams in exams_by_fy.items():
            for idx, exam in enumerate(exams):
                waves[idx].append(exam)

        print(f"[INFO] Total waves: {len(waves)}")

        # ---- Schedule wave by wave
        for wave_idx in sorted(waves.keys()):
            print(f"[WAVE {wave_idx + 1}]")

            wave_exams = waves[wave_idx]

            # Round-robin by department
            for dept_id in self.departments:
                dept_exams = [
                    e for e in wave_exams
                    if e["id_dept"] == dept_id
                ]

                for exam in dept_exams:
                    fy = (exam["id_formation"], exam["annee"])
                    groups = self.groups_by_fy.get(fy, [])
                    if not groups:
                        continue

                    packs = self.create_packs(groups, exam["annee"])
                    slot = self.find_slot(packs)
                    if not slot:
                        print(f"  [SKIP] Exam {exam['id_examen']} (no slot)")
                        continue

                    # Determine room type ONCE for the entire exam
                    global_room_type = "amphi" if any(p["type"] == "amphi" for p in packs) else "salle"
                    
                    # Pick professors ONCE per exam+slot
                    shared_profs = self.pick_professors(
                        exam_dept=exam["id_dept"],
                        room_type=global_room_type,
                        exam_date=slot["date"],
                        slot_time=slot["heure_debut"],
                        exam_id=exam["id_examen"]
                    )
                    
                    if not shared_profs:
                        print(f"  [SKIP] Exam {exam['id_examen']} (no professors available)")
                        continue

                    # Now assign rooms and create planning entries
                    for pack in packs:
                        room = self.assign_room(pack)
                        if not room:
                            print(f"  [SKIP] No room for pack")
                            continue

                        # ✅ PostgreSQL: Use RETURNING instead of lastrowid
                        self.cursor.execute("""
                            INSERT INTO planning_examens (id_examen, id_creneau, id_lieu)
                            VALUES (%s, %s, %s)
                            RETURNING id_planning
                        """, (exam["id_examen"], slot["id_creneau"], room["id_lieu"]))

                        planning_id = self.cursor.fetchone()["id_planning"]

                        # Reuse the SAME professors for all packs
                        for pid in shared_profs:
                            self.cursor.execute("""
                                INSERT INTO surveillances (id_prof, id_planning)
                                VALUES (%s, %s)
                            """, (pid, planning_id))

                        # Handle merged/split group labels
                        if len(pack["groups"]) > 1:
                            merged_codes = "+".join(g["code_groupe"] for g in pack["groups"])
                        else:
                            merged_codes = None

                        for g in pack["groups"]:
                            self.cursor.execute("""
                                INSERT INTO planning_groupes
                                (id_planning, id_groupe, split_part, merged_groups)
                                VALUES (%s, %s, %s, %s)
                            """, (
                                planning_id,
                                g["id_groupe"],
                                pack["split_part"],
                                merged_codes
                            ))

        self.conn.commit()
        print("[SUCCESS] Planning generation completed")

    def close(self):
        self.cursor.close()
        self.conn.close()

    
# --------------------------------------------------
# ENTRY POINT
# --------------------------------------------------
if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python generate_assign.py <period_id>")
        sys.exit(1)

    try:
        period_id = int(sys.argv[1])
    except ValueError:
        print(f"Error: period_id must be an integer, got '{sys.argv[1]}'")
        sys.exit(1)
    
    scheduler = ExamScheduler(period_id)
    try:
        scheduler.generate()
    finally:
        scheduler.close()
