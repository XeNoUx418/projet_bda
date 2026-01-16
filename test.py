"""
Simplified Wave 1 Test - Schedule exactly ONE exam per department
Focus:  Verify insertion logic works before full optimization
"""
import mysql.connector
import logging
from datetime import datetime

logging.basicConfig(
    filename='wave1_test.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Wave1Optimizer:
    def __init__(self, period_id):
        self.period_id = period_id
        self.conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="exam_timetabling"
        )
        self.cursor = self.conn.cursor(dictionary=True)
        
    def load_data(self):
        """Load minimal data for Wave 1"""
        # Get ALL slots (don't filter by Friday yet)
        self.cursor.execute("""
            SELECT id_creneau, date, heure_debut
            FROM creneaux
            WHERE id_periode = %s
            ORDER BY date, heure_debut
        """, (self.period_id,))
        self.slots = self.cursor.fetchall()
        
        print(f"✓ Loaded {len(self.slots)} time slots")
        logging.info(f"Loaded {len(self.slots)} time slots")
        
        # Get rooms
        self.cursor.execute("SELECT id_lieu, capacite, type FROM lieux_examen ORDER BY capacite DESC")
        self.rooms = self.cursor.fetchall()
        print(f"✓ Loaded {len(self.rooms)} rooms")
        
        # Get FIRST exam from each department
        self.cursor. execute("""
            SELECT DISTINCT
                d.id_dept,
                d.nom as dept_name,
                e.id_examen,
                m.id_module,
                m.nom as module_name,
                m.id_formation,
                m.annee,
                COUNT(DISTINCT i.id_etudiant) as student_count
            FROM departements d
            JOIN formations f ON f.id_dept = d.id_dept
            JOIN modules m ON m.id_formation = f.id_formation
            JOIN examens e ON e.id_module = m.id_module
            LEFT JOIN inscriptions i ON i.id_module = m.id_module
            WHERE m.id_module IN (
                SELECT MIN(id_module) FROM modules GROUP BY id_formation
            )
            GROUP BY d.id_dept, e.id_examen
            ORDER BY d.id_dept
        """)
        self.dept_exams = self.cursor. fetchall()
        print(f"✓ Found {len(self.dept_exams)} departments with exams")
        
        # Get groups for each exam
        self.cursor.execute("""
            SELECT id_groupe, id_formation, code_groupe, effectif
            FROM groupes
            ORDER BY id_formation, code_groupe
        """)
        self.all_groups = self.cursor.fetchall()
        print(f"✓ Loaded {len(self.all_groups)} groups\n")
        
    def schedule_wave_1(self):
        """Schedule ONE exam per department"""
        print("="*70)
        print("WAVE 1: Schedule ONE exam per department")
        print("="*70 + "\n")
        logging.info("Starting Wave 1 scheduling")
        
        scheduled_count = 0
        failed_count = 0
        
        slot_index = 0  # Start at slot 0
        room_index = 0  # Start at room 0
        
        for dept_exam in self.dept_exams:
            dept_id = dept_exam['id_dept']
            dept_name = dept_exam['dept_name']
            exam_id = dept_exam['id_examen']
            module_id = dept_exam['id_module']
            formation_id = dept_exam['id_formation']
            
            print(f"\n[DEPT {dept_id}] {dept_name}")
            print(f"  Exam ID: {exam_id}, Module ID: {module_id}")
            logging.info(f"Department {dept_id} ({dept_name}): Exam {exam_id}, Module {module_id}")
            
            # Get groups for this formation
            formation_groups = [
                g for g in self.all_groups 
                if g['id_formation'] == formation_id
            ]
            
            if not formation_groups:
                print(f"  ✗ NO GROUPS FOUND for formation {formation_id}")
                logging.error(f"No groups for formation {formation_id}")
                failed_count += 1
                continue
            
            print(f"  Groups for formation: {len(formation_groups)}")
            
            # Get next slot (cycle through slots)
            if slot_index >= len(self. slots):
                slot_index = 0
            slot = self.slots[slot_index]
            slot_index += 1
            
            print(f"  Slot:  {slot['date']} at {slot['heure_debut']}")
            
            # Get next room (cycle through rooms)
            if room_index >= len(self.rooms):
                room_index = 0
            room = self.rooms[room_index]
            room_index += 1
            
            print(f"  Room:  {room['id_lieu']} (type={room['type']}, capacity={room['capacite']})")
            
            try:
                # INSERT planning_examens
                self.cursor. execute("""
                    INSERT INTO planning_examens 
                    (id_examen, id_creneau, id_lieu)
                    VALUES (%s, %s, %s)
                """, (exam_id, slot['id_creneau'], room['id_lieu']))
                
                planning_id = self.cursor.lastrowid
                print(f"  → Inserted planning_examens (ID: {planning_id})")
                logging.info(f"Inserted planning_examens ID {planning_id}")
                
                # INSERT planning_groupes for each group
                for group in formation_groups:
                    self.cursor.execute("""
                        INSERT INTO planning_groupes
                        (id_planning, id_groupe, merged_groups, split_part)
                        VALUES (%s, %s, %s, NULL)
                    """, (planning_id, group['id_groupe'], group['code_groupe']))
                    
                print(f"  → Inserted {len(formation_groups)} groups in planning_groupes")
                logging. info(f"Inserted {len(formation_groups)} groups for planning {planning_id}")
                
                self.conn.commit()
                print(f"  ✓ COMMITTED")
                scheduled_count += 1
                
            except Exception as e:
                print(f"  ✗ ERROR: {str(e)}")
                logging.error(f"Failed to schedule department {dept_id}:  {str(e)}")
                self.conn.rollback()
                failed_count += 1
        
        print("\n" + "="*70)
        print(f"WAVE 1 RESULTS")
        print("="*70)
        print(f"✓ Scheduled:  {scheduled_count} departments")
        print(f"✗ Failed: {failed_count} departments")
        print(f"Total: {len(self.dept_exams)} departments\n")
        
        logging.info(f"Wave 1 complete: {scheduled_count} scheduled, {failed_count} failed")
        
        # Verify what was inserted
        self.verify_insertions()
    
    def verify_insertions(self):
        """Verify that exams were actually inserted"""
        print("="*70)
        print("VERIFICATION")
        print("="*70)
        
        # Check planning_examens
        self.cursor.execute("""
            SELECT COUNT(*) as total
            FROM planning_examens pe
            JOIN creneaux c ON c.id_creneau = pe.id_creneau
            WHERE c.id_periode = %s
        """, (self.period_id,))
        result = self.cursor.fetchone()
        print(f"\nTotal planning_examens inserted: {result['total']}")
        logging.info(f"Total planning_examens:  {result['total']}")
        
        # Check distribution by department
        self.cursor.execute("""
            SELECT 
                d.id_dept,
                d.nom as dept_name,
                COUNT(DISTINCT pe.id_planning) as num_planifications,
                COUNT(DISTINCT pg.id_groupe) as num_groups
            FROM departements d
            JOIN formations f ON f.id_dept = d.id_dept
            JOIN modules m ON m.id_formation = f.id_formation
            JOIN examens e ON e.id_module = m.id_module
            LEFT JOIN planning_examens pe ON pe.id_examen = e.id_examen
            LEFT JOIN planning_groupes pg ON pg.id_planning = pe.id_planning
            WHERE m.id_module IN (
                SELECT MIN(id_module) FROM modules GROUP BY id_formation
            )
            GROUP BY d.id_dept, d. nom
            ORDER BY d.id_dept
        """)
        results = self.cursor.fetchall()
        
        print("\nPlannings per department:")
        for row in results:
            status = "✓" if row['num_planifications'] > 0 else "✗"
            print(f"  {status} Dept {row['id_dept']} ({row['dept_name']}): {row['num_planifications']} plannings, {row['num_groups']} groups")
            logging.info(f"Department {row['id_dept']}: {row['num_planifications']} plannings, {row['num_groups']} groups")
        
        print()
    
    def close(self):
        self.cursor.close()
        self.conn.close()

if __name__ == "__main__":
    print("\n" + "="*70)
    print("WAVE 1 TEST OPTIMIZER - Simple One-Per-Department Schedule")
    print("="*70 + "\n")
    
    period_id = 11
    optimizer = Wave1Optimizer(period_id)
    
    try:
        optimizer. load_data()
        optimizer.schedule_wave_1()
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        logging.error(f"Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        optimizer.close()
        print("="*70)
        print("WAVE 1 TEST COMPLETE")
        print("="*70 + "\n")