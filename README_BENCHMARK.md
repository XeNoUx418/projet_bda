# SQL Query Benchmark System
## Exam Timetabling Application Performance Testing

This benchmark system provides comprehensive performance analysis for all SQL queries used in the exam timetabling application.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Files Included](#files-included)
3. [Installation & Setup](#installation--setup)
4. [Running Benchmarks](#running-benchmarks)
5. [Understanding Results](#understanding-results)
6. [Query Optimization](#query-optimization)
7. [Integration with API](#integration-with-api)
8. [Continuous Monitoring](#continuous-monitoring)

---

## 🎯 Overview

The benchmark system measures:
- **Query execution times** (average, min, max, standard deviation)
- **Row counts** returned by each query
- **Query execution plans** (EXPLAIN analysis)
- **Index usage** and missing indexes
- **Performance bottlenecks** and optimization opportunities
- **Conflict detection query** efficiency

### Query Categories Benchmarked

1. **Reference Data Queries** - Departments, formations, periods
2. **Student Interface Queries** - Student schedules and exam calendars
3. **Professor Interface Queries** - Surveillance schedules
4. **Dashboard KPI Queries** - Statistics and analytics
5. **Conflict Detection Queries** - Professor and room conflicts
6. **Scheduler Algorithm Queries** - Data loading for the scheduling algorithm

---

## 📦 Files Included

### Core Benchmark Files

```
benchmark_queries.py       # Main benchmark execution script
query_analyzer.py         # Advanced query analysis and optimization suggestions
benchmark_config.py       # Configuration settings
benchmark_api.py          # Flask API endpoint for benchmarking
README_BENCHMARK.md       # This documentation
```

### Generated Output Files

```
benchmark_results_YYYYMMDD_HHMMSS.json    # Raw benchmark data
benchmark_report_YYYYMMDD_HHMMSS.html     # Visual HTML report
benchmark_summary.csv                      # CSV export for spreadsheet analysis
```

---

## 🚀 Installation & Setup

### Prerequisites

```bash
# Python packages required
pip install mysql-connector-python pandas flask flask-cors
```

### Database Configuration

Edit `benchmark_config.py` to match your database settings:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "exam_timetabling"
}
```

### Verify Database Connection

```bash
python3 -c "import mysql.connector; print('Connection test:', mysql.connector.connect(host='localhost', user='root', password='', database='exam_timetabling'))"
```

---

## 🏃 Running Benchmarks

### Method 1: Command Line (Recommended)

```bash
# Run full benchmark suite
python3 benchmark_queries.py

# This will:
# 1. Connect to database
# 2. Run all queries 5 times each
# 3. Calculate statistics
# 4. Generate JSON and HTML reports
# 5. Display results in terminal
```

### Method 2: Via API Endpoint

```bash
# Start the API server
python3 benchmark_api.py

# In another terminal, trigger benchmark
curl http://localhost:5000/api/benchmark/run

# Get latest results
curl http://localhost:5000/api/benchmark/latest
```

### Method 3: Programmatic Usage

```python
from benchmark_queries import BenchmarkSuite

suite = BenchmarkSuite()
results = suite.run_all()
suite.save_results(results)
suite.save_report(results)
suite.close()
```

### Running Specific Query Analysis

```python
from query_analyzer import QueryAnalyzer

analyzer = QueryAnalyzer()

# Analyze a specific query
query = "SELECT * FROM planning_examens WHERE id_periode = %s"
analysis = analyzer.analyze_query(query, (1,))

print(f"Performance Score: {analysis['performance_score']}/100")
print(f"Issues: {analysis['issues']}")
print(f"Recommendations: {analysis['recommendations']}")

analyzer.close()
```

---

## 📊 Understanding Results

### Terminal Output

```
======================================================================
EXAM TIMETABLING SYSTEM - SQL QUERY BENCHMARK
======================================================================
Started at: 2026-01-15 14:30:00
Database: exam_timetabling
======================================================================

──────────────────────────────────────────────────────────────────────
  Reference Data
──────────────────────────────────────────────────────────────────────
  ✓ departments                  │ Avg:    12.50ms │ Min:    11.20ms │ Max:    14.30ms │ Rows:     5
  ✓ formations                   │ Avg:    15.80ms │ Min:    14.10ms │ Max:    18.20ms │ Rows:    12
```

### Performance Thresholds

| Category | Time Range | Interpretation |
|----------|-----------|----------------|
| **Fast** | < 50ms | ✅ Optimal performance |
| **Medium** | 50-100ms | ⚠️ Acceptable, monitor |
| **Slow** | > 100ms | ❌ Needs optimization |

### HTML Report

The HTML report (`benchmark_report_*.html`) includes:

- **Summary cards** with key metrics
- **Color-coded tables** by category
- **Performance indicators** (fast/medium/slow)
- **Visual highlighting** of problematic queries

Open the HTML file in any browser for interactive analysis.

### JSON Output

```json
{
  "timestamp": "2026-01-15T14:30:00",
  "database": "exam_timetabling",
  "results": {
    "student_schedule": {
      "category": "Student Interface",
      "avg_time_ms": 45.32,
      "min_time_ms": 42.10,
      "max_time_ms": 51.20,
      "std_dev_ms": 3.45,
      "median_time_ms": 44.80,
      "row_count": 156
    }
  },
  "summary": {
    "total": 23,
    "successful": 23,
    "failed": 0,
    "avg_time_ms": 38.42,
    "total_time_ms": 883.66
  }
}
```

---

## 🔧 Query Optimization

### Step 1: Identify Slow Queries

Run the analyzer on specific queries:

```bash
python3 query_analyzer.py
```

### Step 2: Review EXPLAIN Output

The analyzer provides detailed execution plan analysis:

```
Issues Found:
  • Table 'planning_examens': Full table scan detected (5000 rows)
  • Table 'creneaux': Index available but not used
  • Table 'surveillances': Using filesort (slow for large datasets)

Recommendations:
  → Add index to table 'planning_examens' - no possible keys available
  → Consider adding composite index for ORDER BY columns in table 'surveillances'
  → Review query conditions for table 'creneaux' - possible keys: idx_creneaux_periode
```

### Step 3: Apply Optimizations

Based on recommendations, add indexes:

```sql
-- Add missing indexes
CREATE INDEX idx_planning_periode ON planning_examens(id_creneau);
CREATE INDEX idx_surveillances_prof_date ON surveillances(id_prof, id_planning);

-- Add composite indexes for common queries
CREATE INDEX idx_creneaux_periode_date ON creneaux(id_periode, date, heure_debut);
CREATE INDEX idx_planning_groupes_lookup ON planning_groupes(id_groupe, id_planning);
```

### Step 4: Re-run Benchmarks

```bash
python3 benchmark_queries.py
```

Compare before/after results to measure improvement.

### Common Optimization Patterns

#### Pattern 1: Missing Index on Foreign Keys

```sql
-- Before: Full table scan
SELECT * FROM planning_examens pe
WHERE pe.id_creneau IN (SELECT id_creneau FROM creneaux WHERE id_periode = 1);

-- Solution: Add index
CREATE INDEX idx_planning_creneau ON planning_examens(id_creneau);
```

#### Pattern 2: GROUP_CONCAT Performance

```sql
-- Before: Slow with many rows
SELECT GROUP_CONCAT(DISTINCT g.code_groupe SEPARATOR ', ')
FROM groupes g;

-- Better: Use application-level concatenation or limit results
```

#### Pattern 3: Date Function in WHERE Clause

```sql
-- Before: Prevents index usage
WHERE DATE_FORMAT(c.date, '%Y') = '2026'

-- Better: Use range
WHERE c.date BETWEEN '2026-01-01' AND '2026-12-31'
```

---

## 🔗 Integration with API

### Adding Benchmark Endpoint

Add to your `app_api.py`:

```python
from benchmark_queries import BenchmarkSuite

@app.get("/api/admin/benchmark")
def run_benchmark():
    """Run benchmark suite and return results"""
    suite = BenchmarkSuite()
    try:
        results = suite.run_all()
        # Return only summary for API response
        return jsonify({
            "ok": True,
            "timestamp": results['timestamp'],
            "summary": results['summary'],
            "slow_queries": [
                name for name, data in results['results'].items()
                if 'avg_time_ms' in data and data['avg_time_ms'] > 100
            ]
        })
    finally:
        suite.close()
```

### Real-time Query Monitoring

Add timing decorator to your API queries:

```python
import time
from functools import wraps

def time_query(func):
    """Decorator to measure query execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        duration = (time.perf_counter() - start) * 1000
        
        # Log slow queries
        if duration > 100:
            print(f"⚠️  Slow query in {func.__name__}: {duration:.2f}ms")
        
        return result
    return wrapper

# Usage
@time_query
def get_student_schedule(formation_id, annee, periode_id):
    return query_df("SELECT ...", params=[formation_id, annee, periode_id])
```

---

## 📈 Continuous Monitoring

### Setting Up Automated Benchmarks

Create a scheduled task to run benchmarks daily:

```bash
# Add to crontab (run daily at 2 AM)
0 2 * * * cd /path/to/project && python3 benchmark_queries.py >> benchmark.log 2>&1
```

### Tracking Performance Over Time

```python
import json
from datetime import datetime

# Load historical results
def load_benchmark_history():
    results = []
    for file in glob.glob("benchmark_results_*.json"):
        with open(file) as f:
            results.append(json.load(f))
    return sorted(results, key=lambda x: x['timestamp'])

# Compare performance trends
def analyze_trends(history):
    for query_name in history[0]['results'].keys():
        times = [r['results'][query_name]['avg_time_ms'] 
                for r in history if query_name in r['results']]
        
        if times[-1] > times[0] * 1.5:  # 50% slower
            print(f"⚠️  Performance degradation in {query_name}")
```

### Performance Regression Testing

```python
# Save baseline benchmark
baseline = suite.run_all()
with open('benchmark_baseline.json', 'w') as f:
    json.dump(baseline, f)

# Compare against baseline
current = suite.run_all()

for query, data in current['results'].items():
    baseline_time = baseline['results'][query]['avg_time_ms']
    current_time = data['avg_time_ms']
    
    if current_time > baseline_time * 1.2:  # 20% slower
        print(f"❌ Regression detected: {query}")
        print(f"   Baseline: {baseline_time:.2f}ms")
        print(f"   Current:  {current_time:.2f}ms")
```

---

## 🎯 Best Practices

### 1. Run Benchmarks Regularly

- Before and after major code changes
- Weekly during active development
- Monthly in production

### 2. Set Performance Budgets

Define maximum acceptable query times:

```python
PERFORMANCE_BUDGETS = {
    "student_schedule": 100,      # 100ms max
    "dashboard_kpis": 150,         # 150ms max
    "conflict_detection": 200      # 200ms max
}
```

### 3. Monitor Database Growth

Large tables affect performance:

```sql
-- Check table sizes
SELECT 
    table_name,
    table_rows,
    ROUND(data_length / 1024 / 1024, 2) AS 'Data Size (MB)',
    ROUND(index_length / 1024 / 1024, 2) AS 'Index Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'exam_timetabling'
ORDER BY data_length DESC;
```

### 4. Test with Realistic Data Volumes

Ensure your test database has representative data:

```sql
-- Add test data generator
INSERT INTO planning_examens (id_examen, id_creneau, id_lieu)
SELECT 
    e.id_examen,
    (SELECT id_creneau FROM creneaux ORDER BY RAND() LIMIT 1),
    (SELECT id_lieu FROM lieux_examen ORDER BY RAND() LIMIT 1)
FROM examens e
WHERE NOT EXISTS (SELECT 1 FROM planning_examens pe WHERE pe.id_examen = e.id_examen);
```

### 5. Document Performance Improvements

Keep a changelog of optimizations:

```markdown
## Performance Changelog

### 2026-01-15
- Added composite index on `planning_examens(id_creneau, id_lieu)`
- Result: `student_schedule` query improved from 145ms → 38ms (74% faster)

### 2026-01-10
- Rewrote `professor_conflicts` query to use JOIN instead of subquery
- Result: Query improved from 230ms → 85ms (63% faster)
```

---

## 🐛 Troubleshooting

### Issue: "No module named 'mysql.connector'"

```bash
pip install mysql-connector-python
```

### Issue: "Access denied for user"

Check database credentials in `benchmark_config.py` and ensure user has SELECT privileges.

### Issue: "No data in benchmark results"

Ensure your database has test data. Run the data generation script:

```bash
# Add sample data if needed
python3 generate_sample_data.py
```

### Issue: Benchmarks taking too long

Reduce iterations in `benchmark_config.py`:

```python
BENCHMARK_SETTINGS = {
    "iterations": 3,  # Reduced from 5
}
```

---

## 📞 Support

For issues or questions:
1. Check the terminal output for specific error messages
2. Review the `benchmark.log` file if running automated benchmarks
3. Verify database connectivity with `mysql -u root -p exam_timetabling`

---

## 📝 License

This benchmark system is part of the Exam Timetabling project.

---

**Last Updated:** January 15, 2026
**Version:** 1.0.0
