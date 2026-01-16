#!/usr/bin/env python3
"""
Quick Start Script for SQL Benchmarking
========================================

This script helps you get started with benchmarking quickly
"""

import sys
import os

def check_dependencies():
    """Check if required packages are installed"""
    print("Checking dependencies...")
    
    required = {
        'mysql.connector': 'mysql-connector-python',
        'pandas': 'pandas',
        'flask': 'flask',
        'flask_cors': 'flask-cors'
    }
    
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages. Install with:")
        print(f"pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies installed\n")
    return True


def check_database_connection():
    """Verify database connection"""
    print("Checking database connection...")
    
    try:
        import mysql.connector
        from benchmark_config import DB_CONFIG
        
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM planning_examens")
        result = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        print(f"✅ Connected to database: {DB_CONFIG['database']}")
        print(f"   Found {result[0]} records in planning_examens\n")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\nPlease update benchmark_config.py with correct database credentials\n")
        return False


def run_quick_benchmark():
    """Run a quick benchmark with essential queries only"""
    print("Running quick benchmark (essential queries only)...")
    print("=" * 70)
    
    try:
        from benchmark_queries import BenchmarkSuite
        
        suite = BenchmarkSuite()
        suite.setup_test_data()
        
        # Run only a few critical queries
        essential_benchmarks = {
            'student_schedule': ('Quick Test', suite.bench_student_schedule),
            'professor_schedule': ('Quick Test', suite.bench_professor_schedule),
            'prof_conflicts': ('Quick Test', suite.bench_professor_conflicts),
            'total_planned': ('Quick Test', suite.bench_total_planned_exams),
        }
        
        print("\n  Essential Queries Benchmark")
        print("─" * 70)
        
        results = {}
        for name, (category, func) in essential_benchmarks.items():
            try:
                result = func()
                results[name] = result
                
                print(f"  ✓ {name:25s} │ "
                      f"Avg: {result['avg_time_ms']:7.2f}ms │ "
                      f"Rows: {result['row_count']:5d}")
                
            except Exception as e:
                print(f"  ✗ {name:25s} │ ERROR: {str(e)}")
        
        suite.close()
        
        print("\n" + "=" * 70)
        print("✅ Quick benchmark completed!")
        print("\nNext steps:")
        print("  1. Run full benchmark: python3 benchmark_queries.py")
        print("  2. Start API server: python3 benchmark_api.py")
        print("  3. View dashboard: http://localhost:5001/benchmark/dashboard")
        print("=" * 70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_menu():
    """Show interactive menu"""
    print("\n" + "=" * 70)
    print("  SQL QUERY BENCHMARK - QUICK START")
    print("=" * 70)
    print("\nWhat would you like to do?")
    print("  1. Check dependencies and database connection")
    print("  2. Run quick benchmark (4 essential queries)")
    print("  3. Run full benchmark suite (all queries)")
    print("  4. Start benchmark API server")
    print("  5. Analyze database indexes")
    print("  6. Exit")
    print()
    
    choice = input("Enter your choice (1-6): ").strip()
    return choice


def main():
    """Main entry point"""
    
    while True:
        choice = show_menu()
        
        if choice == '1':
            print("\n" + "=" * 70)
            deps_ok = check_dependencies()
            if deps_ok:
                check_database_connection()
            print("=" * 70)
            input("\nPress Enter to continue...")
            
        elif choice == '2':
            print("\n" + "=" * 70)
            if not check_dependencies():
                print("=" * 70)
                input("\nPress Enter to continue...")
                continue
            
            if not check_database_connection():
                print("=" * 70)
                input("\nPress Enter to continue...")
                continue
            
            run_quick_benchmark()
            input("\nPress Enter to continue...")
            
        elif choice == '3':
            print("\nRunning full benchmark suite...")
            print("This will take 2-3 minutes.\n")
            
            try:
                from benchmark_queries import BenchmarkSuite
                
                suite = BenchmarkSuite()
                results = suite.run_all()
                suite.save_results(results)
                suite.save_report(results)
                suite.close()
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            input("\nPress Enter to continue...")
            
        elif choice == '4':
            print("\nStarting benchmark API server...")
            print("Server will run on http://localhost:5001")
            print("Dashboard: http://localhost:5001/benchmark/dashboard")
            print("\nPress Ctrl+C to stop the server\n")
            
            try:
                import benchmark_api
            except KeyboardInterrupt:
                print("\n\nServer stopped.")
            
            input("\nPress Enter to continue...")
            
        elif choice == '5':
            print("\nAnalyzing database indexes...")
            print("=" * 70)
            
            try:
                from query_analyzer import QueryAnalyzer
                
                analyzer = QueryAnalyzer()
                index_report = analyzer.analyze_all_indexes()
                analyzer.close()
                
                print("\nDatabase Index Analysis")
                print("─" * 70)
                
                for table, info in index_report.items():
                    print(f"\n{table}:")
                    print(f"  Rows: {info['row_count']:,}")
                    print(f"  Indexes: {len(info['indexes'])}")
                    
                    if info['recommendations']:
                        print("  Recommendations:")
                        for rec in info['recommendations']:
                            print(f"    {rec}")
                
                print("\n" + "=" * 70)
                
            except Exception as e:
                print(f"❌ Error: {e}")
            
            input("\nPress Enter to continue...")
            
        elif choice == '6':
            print("\nGoodbye! 👋")
            break
            
        else:
            print("\n❌ Invalid choice. Please enter 1-6.")
            input("\nPress Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted. Goodbye! 👋")
        sys.exit(0)
