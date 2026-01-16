# Benchmark Configuration
# ========================

# Database connection settings
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "exam_timetabling"
}

# Benchmark execution settings
BENCHMARK_SETTINGS = {
    # Number of times to run each query for averaging
    "iterations": 5,
    
    # Include a warm-up run before timing (recommended)
    "warmup": True,
    
    # Generate EXPLAIN output for each query
    "analyze_query_plans": True,
    
    # Performance thresholds (in milliseconds)
    "thresholds": {
        "fast": 50,      # Queries faster than this are considered optimal
        "medium": 100,   # Queries between fast and medium need monitoring
        "slow": 100      # Queries slower than this need optimization
    },
    
    # Output settings
    "save_json": True,
    "save_html": True,
    "save_csv": True,
    "output_directory": "./benchmark_results"
}

# Query categories to benchmark
QUERY_CATEGORIES = [
    "Reference Data",
    "Student Interface",
    "Professor Interface",
    "Dashboard KPIs",
    "Conflict Detection",
    "Scheduler Algorithm"
]

# Optimization suggestions for common slow query patterns
OPTIMIZATION_TIPS = {
    "missing_index": "Consider adding an index on the frequently filtered columns",
    "full_table_scan": "Query is performing a full table scan - add WHERE conditions or indexes",
    "complex_join": "Simplify joins or ensure all join columns are indexed",
    "group_concat": "GROUP_CONCAT can be slow with large datasets - consider alternatives",
    "subquery": "Consider rewriting subquery as a JOIN for better performance",
    "date_functions": "Avoid using functions on indexed date columns in WHERE clauses"
}

# Sample test data for benchmarking
# These will be auto-detected from the database if not specified
TEST_DATA = {
    "periode_id": None,      # Will use first available period
    "formation_id": None,    # Will use first available formation
    "prof_id": None,         # Will use first available professor
    "student_id": None,      # Will use first available student
    "annee": "L1",          # Default year level
    "date_range": {
        "start": "2026-01-06",
        "end": "2026-01-26"
    }
}

# Queries to specifically benchmark with EXPLAIN ANALYZE
CRITICAL_QUERIES = [
    "student_schedule",
    "personal_student_schedule",
    "professor_schedule",
    "prof_conflicts",
    "dashboard_kpis"
]

# Expected index usage for validation
EXPECTED_INDEXES = {
    "planning_examens": ["id_examen", "id_creneau", "id_lieu"],
    "planning_groupes": ["id_planning", "id_groupe"],
    "creneaux": ["id_periode"],
    "surveillances": ["id_prof", "id_planning"],
    "etudiants": ["id_formation", "id_groupe"],
    "groupes": ["id_formation"],
    "modules": ["id_formation"]
}
