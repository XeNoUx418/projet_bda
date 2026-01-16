#!/usr/bin/env python3
"""
SQL Query Benchmarking Tool for Exam Timetabling System
========================================================

This script benchmarks all critical SQL queries used in the application
to measure performance, identify bottlenecks, and track optimization improvements.
"""

import mysql.connector
import time
import statistics
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from collections import defaultdict
import pandas as pd


# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "exam_timetabling"
}


class QueryBenchmark:
    """Handles benchmarking of individual SQL queries"""
    
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor(dictionary=True)
        
    def execute_with_timing(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Execute a query and measure its performance
        
        Returns:
            dict with timing metrics and results
        """
        # Warm-up run (not counted)
        self.cursor.execute(query, params or ())
        _ = self.cursor.fetchall()
        
        # Actual measured runs
        timings = []
        row_counts = []
        
        for _ in range(5):  # Run 5 times for average
            start = time.perf_counter()
            self.cursor.execute(query, params or ())
            results = self.cursor.fetchall()
            end = time.perf_counter()
            
            timings.append((end - start) * 1000)  # Convert to milliseconds
            row_counts.append(len(results))
        
        return {
            'avg_time_ms': statistics.mean(timings),
            'min_time_ms': min(timings),
            'max_time_ms': max(timings),
            'std_dev_ms': statistics.stdev(timings) if len(timings) > 1 else 0,
            'median_time_ms': statistics.median(timings),
            'row_count': row_counts[0],
            'all_timings': timings
        }
    
    def analyze_query_plan(self, query: str, params: tuple = None) -> List[Dict]:
        """Get EXPLAIN output for query optimization analysis"""
        explain_query = f"EXPLAIN {query}"
        self.cursor.execute(explain_query, params or ())
        return self.cursor.fetchall()


class BenchmarkSuite:
    """Complete benchmark suite for all application queries"""
    
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.benchmark = QueryBenchmark(self.conn)
        self.results = {}
        
    def setup_test_data(self):
        """Ensure we have test data - get actual IDs from database"""
        cursor = self.conn.cursor(dictionary=True)
        
        # Get sample periode_id
        cursor.execute("SELECT id_periode FROM periodes_examens LIMIT 1")
        result = cursor.fetchone()
        self.sample_periode = result['id_periode'] if result else 1
        
        # Get sample formation_id
        cursor.execute("SELECT id_formation FROM formations LIMIT 1")
        result = cursor.fetchone()
        self.sample_formation = result['id_formation'] if result else 1
        
        # Get sample professor
        cursor.execute("SELECT id_prof FROM professeurs LIMIT 1")
        result = cursor.fetchone()
        self.sample_prof = result['id_prof'] if result else 1
        
        # Get sample student
        cursor.execute("SELECT id_etudiant FROM etudiants LIMIT 1")
        result = cursor.fetchone()
        self.sample_student = result['id_etudiant'] if result else 1
        
        cursor.close()
    
    # ==========================================
    # REFERENCE DATA QUERIES
    # ==========================================
    
    def bench_departments(self):
        """Benchmark: Get all departments"""
        query = "SELECT id_dept, nom FROM departements ORDER BY nom"
        return self.benchmark.execute_with_timing(query)
    
    def bench_formations(self):
        """Benchmark: Get formations by department"""
        query = """
            SELECT id_formation, nom 
            FROM formations 
            WHERE id_dept = %s 
            ORDER BY nom
        """
        return self.benchmark.execute_with_timing(query, (1,))
    
    def bench_periods_with_planning(self):
        """Benchmark: Get periods with planning check"""
        query = """
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
        """
        return self.benchmark.execute_with_timing(query)
    
    # ==========================================
    # STUDENT SCHEDULE QUERIES
    # ==========================================
    
    def bench_student_schedule(self):
        """Benchmark: Get student schedule (most complex query)"""
        query = """
            SELECT
                c.date                                   AS exam_date,
                DATE_FORMAT(c.date, '%W, %M %d')         AS DateLabel,
                TIME_FORMAT(c.heure_debut, '%H:%i')      AS Start,
                TIME_FORMAT(c.heure_fin, '%H:%i')        AS End,
                m.nom                                    AS Module,
                e.duree_minutes                          AS Duration,
                le.nom                                   AS Room,
                le.type                                  AS Type,
                le.batiment                              AS Building,
                g.code_groupe                            AS GroupCode,
                pg.split_part                            AS SplitPart,
                pg.merged_groups                         AS MergedGroups
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
        return self.benchmark.execute_with_timing(
            query, 
            (self.sample_formation, 'L1', self.sample_periode)
        )
    
    def bench_personal_student_schedule(self):
        """Benchmark: Get personal student schedule"""
        query = """
            SELECT
                c.date                                   AS exam_date,
                DATE_FORMAT(c.date, '%W, %M %d')         AS DateLabel,
                TIME_FORMAT(c.heure_debut, '%H:%i')      AS Start,
                TIME_FORMAT(c.heure_fin, '%H:%i')        AS End,
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
        """
        return self.benchmark.execute_with_timing(
            query,
            (self.sample_student, self.sample_periode)
        )
    
    # ==========================================
    # PROFESSOR QUERIES
    # ==========================================
    
    def bench_professor_schedule(self):
        """Benchmark: Get professor surveillance schedule"""
        query = """
            SELECT
                c.date,
                TIME_FORMAT(c.heure_debut, '%H:%i') AS Start,
                TIME_FORMAT(c.heure_fin, '%H:%i') AS End,
                m.nom AS Module,
                le.nom AS Room,
                le.batiment AS Building,
                GROUP_CONCAT(DISTINCT g.code_groupe SEPARATOR ', ') AS Groups
            FROM surveillances s
            JOIN planning_examens pe ON s.id_planning = pe.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            JOIN examens e ON pe.id_examen = e.id_examen
            JOIN modules m ON e.id_module = m.id_module
            JOIN lieux_examen le ON pe.id_lieu = le.id_lieu
            LEFT JOIN planning_groupes pg ON pe.id_planning = pg.id_planning
            LEFT JOIN groupes g ON pg.id_groupe = g.id_groupe
            WHERE s.id_prof = %s
              AND c.date BETWEEN %s AND %s
            GROUP BY s.id_planning, c.date, c.heure_debut, c.heure_fin, m.nom, le.nom
            ORDER BY c.date, c.heure_debut
        """
        return self.benchmark.execute_with_timing(
            query,
            (self.sample_prof, '2026-01-06', '2026-01-26')
        )
    
    # ==========================================
    # DASHBOARD KPI QUERIES
    # ==========================================
    
    def bench_total_planned_exams(self):
        """Benchmark: Count total planned exams"""
        query = """
            SELECT COUNT(DISTINCT pe.id_planning) AS n
            FROM planning_examens pe
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_merged_count(self):
        """Benchmark: Count merged groups"""
        query = """
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.merged_groups IS NOT NULL
            AND c.id_periode = %s
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_split_count(self):
        """Benchmark: Count split groups"""
        query = """
            SELECT COUNT(DISTINCT pg.id_planning) AS n
            FROM planning_groupes pg
            JOIN planning_examens pe ON pe.id_planning = pg.id_planning
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE pg.split_part IS NOT NULL
            AND c.id_periode = %s
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_room_distribution(self):
        """Benchmark: Get room type distribution"""
        query = """
            SELECT l.type, COUNT(pe.id_planning) as usage_count
            FROM lieux_examen l
            LEFT JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY l.type
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_top_rooms(self):
        """Benchmark: Get most used rooms"""
        query = """
            SELECT l.nom, l.type, COUNT(pe.id_planning) as sessions
            FROM lieux_examen l
            JOIN planning_examens pe ON l.id_lieu = pe.id_lieu
            JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY l.id_lieu
            ORDER BY sessions DESC
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_professor_load(self):
        """Benchmark: Get professor workload"""
        query = """
            SELECT p.nom, d.nom as Dept, COUNT(s.id_planning) as total_surveillances
            FROM professeurs p
            JOIN departements d ON p.id_dept = d.id_dept
            LEFT JOIN surveillances s ON p.id_prof = s.id_prof
            LEFT JOIN planning_examens pe ON s.id_planning = pe.id_planning
            LEFT JOIN creneaux c ON pe.id_creneau = c.id_creneau
            WHERE c.id_periode = %s
            GROUP BY p.id_prof
            ORDER BY total_surveillances DESC
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    # ==========================================
    # CONFLICT DETECTION QUERIES
    # ==========================================
    
    def bench_professor_conflicts(self):
        """Benchmark: Detect professor scheduling conflicts"""
        query = """
            SELECT
                p.nom AS Professor,
                c.date,
                TIME_FORMAT(c.heure_debut, '%H:%i') AS Start,
                COUNT(DISTINCT pe.id_examen) AS Assignments,
                GROUP_CONCAT(
                    DISTINCT CONCAT(
                        m.nom, ' — ',
                        le.nom, ' (', le.type, ')'
                    ) SEPARATOR '<br>'
                ) AS Details
            FROM surveillances s
            JOIN professeurs p ON p.id_prof = s.id_prof
            JOIN planning_examens pe ON pe.id_planning = s.id_planning
            JOIN examens e ON e.id_examen = pe.id_examen
            JOIN modules m ON m.id_module = e.id_module
            JOIN lieux_examen le ON le.id_lieu = pe.id_lieu
            JOIN creneaux c ON c.id_creneau = pe.id_creneau
            WHERE c.id_periode = %s
            GROUP BY p.id_prof, c.date, c.heure_debut
            HAVING COUNT(DISTINCT pe.id_examen) > 1
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_room_conflicts(self):
        """Benchmark: Detect room double-booking"""
        query = """
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
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    # ==========================================
    # SCHEDULER ALGORITHM QUERIES
    # ==========================================
    
    def bench_load_slots(self):
        """Benchmark: Load available time slots (used in scheduler)"""
        query = """
            SELECT id_creneau, date, heure_debut
            FROM creneaux
            WHERE id_periode = %s
            ORDER BY date, heure_debut
        """
        return self.benchmark.execute_with_timing(query, (self.sample_periode,))
    
    def bench_load_rooms(self):
        """Benchmark: Load all rooms"""
        query = """
            SELECT id_lieu, capacite, type
            FROM lieux_examen
            ORDER BY capacite
        """
        return self.benchmark.execute_with_timing(query)
    
    def bench_load_groups(self):
        """Benchmark: Load all groups"""
        query = """
            SELECT id_groupe, id_formation, annee, effectif, code_groupe
            FROM groupes
            ORDER BY id_formation, annee, code_groupe
        """
        return self.benchmark.execute_with_timing(query)
    
    def bench_load_exams(self):
        """Benchmark: Load all exams with module info"""
        query = """
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
        """
        return self.benchmark.execute_with_timing(query)
    
    def bench_group_conflict_check(self):
        """Benchmark: Check if group has exam on specific date"""
        query = """
            SELECT 1
            FROM planning_examens pe
            JOIN planning_groupes pg ON pg.id_planning = pe.id_planning
            JOIN creneaux c ON c.id_creneau = pe.id_creneau
            WHERE pg.id_groupe = %s AND c.date = %s
            LIMIT 1
        """
        return self.benchmark.execute_with_timing(query, (1, '2026-01-15'))
    
    # ==========================================
    # RUN ALL BENCHMARKS
    # ==========================================
    
    def run_all(self) -> Dict[str, Any]:
        """Execute all benchmarks and return comprehensive results"""
        
        print("=" * 70)
        print("EXAM TIMETABLING SYSTEM - SQL QUERY BENCHMARK")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Database: {DB_CONFIG['database']}")
        print("=" * 70)
        
        self.setup_test_data()
        
        benchmarks = {
            # Reference Data
            'departments': ('Reference Data', self.bench_departments),
            'formations': ('Reference Data', self.bench_formations),
            'periods_with_planning': ('Reference Data', self.bench_periods_with_planning),
            
            # Student Queries
            'student_schedule': ('Student Interface', self.bench_student_schedule),
            'personal_student_schedule': ('Student Interface', self.bench_personal_student_schedule),
            
            # Professor Queries
            'professor_schedule': ('Professor Interface', self.bench_professor_schedule),
            
            # Dashboard KPIs
            'total_planned': ('Dashboard KPIs', self.bench_total_planned_exams),
            'merged_count': ('Dashboard KPIs', self.bench_merged_count),
            'split_count': ('Dashboard KPIs', self.bench_split_count),
            'room_distribution': ('Dashboard KPIs', self.bench_room_distribution),
            'top_rooms': ('Dashboard KPIs', self.bench_top_rooms),
            'professor_load': ('Dashboard KPIs', self.bench_professor_load),
            
            # Conflict Detection
            'prof_conflicts': ('Conflict Detection', self.bench_professor_conflicts),
            'room_conflicts': ('Conflict Detection', self.bench_room_conflicts),
            
            # Scheduler Queries
            'load_slots': ('Scheduler Algorithm', self.bench_load_slots),
            'load_rooms': ('Scheduler Algorithm', self.bench_load_rooms),
            'load_groups': ('Scheduler Algorithm', self.bench_load_groups),
            'load_exams': ('Scheduler Algorithm', self.bench_load_exams),
            'group_conflict_check': ('Scheduler Algorithm', self.bench_group_conflict_check),
        }
        
        results = {}
        current_category = None
        
        for name, (category, func) in benchmarks.items():
            if category != current_category:
                print(f"\n{'─' * 70}")
                print(f"  {category}")
                print(f"{'─' * 70}")
                current_category = category
            
            try:
                result = func()
                results[name] = {
                    'category': category,
                    **result
                }
                
                # Print result
                print(f"  ✓ {name:30s} │ "
                      f"Avg: {result['avg_time_ms']:7.2f}ms │ "
                      f"Min: {result['min_time_ms']:7.2f}ms │ "
                      f"Max: {result['max_time_ms']:7.2f}ms │ "
                      f"Rows: {result['row_count']:5d}")
                
            except Exception as e:
                print(f"  ✗ {name:30s} │ ERROR: {str(e)}")
                results[name] = {'error': str(e), 'category': category}
        
        # Summary statistics
        print(f"\n{'=' * 70}")
        print("SUMMARY")
        print(f"{'=' * 70}")
        
        successful = [r for r in results.values() if 'error' not in r]
        if successful:
            all_times = [r['avg_time_ms'] for r in successful]
            print(f"Total queries benchmarked: {len(results)}")
            print(f"Successful: {len(successful)}")
            print(f"Failed: {len(results) - len(successful)}")
            print(f"\nOverall Performance:")
            print(f"  Average execution time: {statistics.mean(all_times):.2f}ms")
            print(f"  Fastest query: {min(all_times):.2f}ms")
            print(f"  Slowest query: {max(all_times):.2f}ms")
            print(f"  Total time (sum): {sum(all_times):.2f}ms")
            
            # Identify slow queries (>100ms)
            slow_queries = [(name, r['avg_time_ms']) 
                           for name, r in results.items() 
                           if 'avg_time_ms' in r and r['avg_time_ms'] > 100]
            
            if slow_queries:
                print(f"\n⚠️  SLOW QUERIES (>100ms):")
                for name, time_ms in sorted(slow_queries, key=lambda x: x[1], reverse=True):
                    print(f"  • {name}: {time_ms:.2f}ms")
        
        print(f"\n{'=' * 70}\n")
        
        return {
            'timestamp': datetime.now().isoformat(),
            'database': DB_CONFIG['database'],
            'results': results,
            'summary': {
                'total': len(results),
                'successful': len(successful),
                'failed': len(results) - len(successful),
                'avg_time_ms': statistics.mean(all_times) if successful else 0,
                'total_time_ms': sum(all_times) if successful else 0
            }
        }
    
    def save_results(self, results: Dict, filename: str = None):
        """Save benchmark results to JSON file"""
        if filename is None:
            filename = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {filename}")
        return filename
    
    def generate_report(self, results: Dict) -> str:
        """Generate a detailed HTML report"""
        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Benchmark Report - Exam Timetabling</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{ margin: 0; }}
        .header .subtitle {{ opacity: 0.9; margin-top: 10px; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .card h3 {{ margin: 0 0 10px 0; color: #667eea; }}
        .card .value {{ font-size: 2em; font-weight: bold; color: #333; }}
        .card .label {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
        table {{
            width: 100%;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        tr:hover {{ background: #f9f9f9; }}
        .category-header {{
            background: #f0f0f0;
            font-weight: bold;
            padding: 15px;
            margin: 20px 0 10px 0;
            border-left: 4px solid #667eea;
        }}
        .slow {{ color: #e74c3c; font-weight: bold; }}
        .medium {{ color: #f39c12; }}
        .fast {{ color: #27ae60; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>SQL Query Benchmark Report</h1>
        <div class="subtitle">
            Exam Timetabling System Performance Analysis<br>
            Generated: {results['timestamp']}<br>
            Database: {results['database']}
        </div>
    </div>
    
    <div class="summary">
        <div class="card">
            <h3>Total Queries</h3>
            <div class="value">{results['summary']['total']}</div>
            <div class="label">Benchmarked</div>
        </div>
        <div class="card">
            <h3>Success Rate</h3>
            <div class="value">{results['summary']['successful']}/{results['summary']['total']}</div>
            <div class="label">Successful</div>
        </div>
        <div class="card">
            <h3>Average Time</h3>
            <div class="value">{results['summary']['avg_time_ms']:.1f}ms</div>
            <div class="label">Per Query</div>
        </div>
        <div class="card">
            <h3>Total Time</h3>
            <div class="value">{results['summary']['total_time_ms']:.0f}ms</div>
            <div class="label">All Queries</div>
        </div>
    </div>
"""
        
        # Group results by category
        by_category = defaultdict(list)
        for name, data in results['results'].items():
            if 'error' not in data:
                by_category[data['category']].append((name, data))
        
        # Generate table for each category
        for category in sorted(by_category.keys()):
            html += f'<div class="category-header">{category}</div>\n'
            html += '<table>\n<thead>\n<tr>\n'
            html += '<th>Query</th><th>Avg Time</th><th>Min</th><th>Max</th><th>Std Dev</th><th>Rows</th>\n'
            html += '</tr>\n</thead>\n<tbody>\n'
            
            for name, data in sorted(by_category[category], key=lambda x: x[1]['avg_time_ms'], reverse=True):
                avg = data['avg_time_ms']
                color_class = 'slow' if avg > 100 else 'medium' if avg > 50 else 'fast'
                
                html += '<tr>\n'
                html += f'<td>{name}</td>\n'
                html += f'<td class="{color_class}">{avg:.2f}ms</td>\n'
                html += f'<td>{data["min_time_ms"]:.2f}ms</td>\n'
                html += f'<td>{data["max_time_ms"]:.2f}ms</td>\n'
                html += f'<td>{data["std_dev_ms"]:.2f}ms</td>\n'
                html += f'<td>{data["row_count"]}</td>\n'
                html += '</tr>\n'
            
            html += '</tbody>\n</table>\n'
        
        html += '</body>\n</html>'
        
        return html
    
    def save_report(self, results: Dict, filename: str = None):
        """Save HTML report"""
        if filename is None:
            filename = f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        html = self.generate_report(results)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"HTML report saved to: {filename}")
        return filename
    
    def close(self):
        """Close database connection"""
        if self.benchmark.cursor:
            self.benchmark.cursor.close()
        if self.conn:
            self.conn.close()


# ==========================================
# MAIN EXECUTION
# ==========================================

if __name__ == "__main__":
    suite = BenchmarkSuite()
    
    try:
        # Run all benchmarks
        results = suite.run_all()
        
        # Save results
        json_file = suite.save_results(results)
        html_file = suite.save_report(results)
        
        print(f"\n✅ Benchmark completed successfully!")
        print(f"   JSON: {json_file}")
        print(f"   HTML: {html_file}")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
    finally:
        suite.close()
