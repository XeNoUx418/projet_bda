#!/usr/bin/env python3
"""
Analyze Existing Benchmark Results
===================================

This script analyzes your benchmark results with indexes
and prepares you for the without-indexes test
"""

def analyze_current_results():
    """Analyze the benchmark results with indexes"""
    
    results = {
        'Reference Data': {
            'departments': 0.31,
            'formations': 0.30,
            'periods_with_planning': 0.31
        },
        'Student Interface': {
            'student_schedule': 1.70,
            'personal_student_schedule': 0.91
        },
        'Professor Interface': {
            'professor_schedule': 5.13
        },
        'Dashboard KPIs': {
            'total_planned': 3.25,
            'merged_count': 7.94,
            'split_count': 7.66,
            'room_distribution': 8.25,
            'top_rooms': 9.16,
            'professor_load': 19.66
        },
        'Conflict Detection': {
            'prof_conflicts': 51.22,
            'room_conflicts': 14.25
        },
        'Scheduler Algorithm': {
            'load_slots': 1.05,
            'load_rooms': 0.51,
            'load_groups': 3.71,
            'load_exams': 6.32,
            'group_conflict_check': 0.29
        }
    }
    
    print("=" * 80)
    print("CURRENT BENCHMARK ANALYSIS (WITH INDEXES)")
    print("=" * 80)
    print("\n📊 Performance Breakdown by Category")
    print("-" * 80)
    
    all_times = []
    category_stats = {}
    
    for category, queries in results.items():
        times = list(queries.values())
        all_times.extend(times)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        category_stats[category] = {
            'avg': avg_time,
            'max': max_time,
            'min': min_time,
            'count': len(times)
        }
        
        print(f"\n{category}:")
        print(f"  Queries: {len(times)}")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Range:   {min_time:.2f}ms - {max_time:.2f}ms")
        
        # Show individual queries
        for query, time_ms in sorted(queries.items(), key=lambda x: x[1], reverse=True):
            status = "🟢" if time_ms < 10 else "🟡" if time_ms < 50 else "🔴"
            print(f"    {status} {query:<30} {time_ms:>7.2f}ms")
    
    # Overall statistics
    print("\n" + "=" * 80)
    print("OVERALL STATISTICS")
    print("=" * 80)
    print(f"\nTotal queries: {len(all_times)}")
    print(f"Average time:  {sum(all_times)/len(all_times):.2f}ms")
    print(f"Fastest:       {min(all_times):.2f}ms")
    print(f"Slowest:       {max(all_times):.2f}ms")
    print(f"Total time:    {sum(all_times):.2f}ms")
    
    # Performance distribution
    fast = sum(1 for t in all_times if t < 10)
    medium = sum(1 for t in all_times if 10 <= t < 50)
    slow = sum(1 for t in all_times if t >= 50)
    
    print(f"\n📈 Performance Distribution:")
    print(f"  🟢 Fast (<10ms):     {fast:2d} queries ({fast/len(all_times)*100:.1f}%)")
    print(f"  🟡 Medium (10-50ms): {medium:2d} queries ({medium/len(all_times)*100:.1f}%)")
    print(f"  🔴 Slow (>50ms):     {slow:2d} queries ({slow/len(all_times)*100:.1f}%)")
    
    # Predictions for without indexes
    print("\n" + "=" * 80)
    print("PREDICTIONS FOR WITHOUT INDEXES")
    print("=" * 80)
    
    print("\n⚠️  Expected Performance Changes:\n")
    
    predictions = {
        'Reference Data': {
            'multiplier': 3,
            'reason': 'Small tables, minimal impact'
        },
        'Student Interface': {
            'multiplier': 50,
            'reason': 'Complex JOINs across 7+ tables'
        },
        'Professor Interface': {
            'multiplier': 40,
            'reason': 'GROUP_CONCAT with multiple JOINs'
        },
        'Dashboard KPIs': {
            'multiplier': 30,
            'reason': 'Aggregations and GROUP BY operations'
        },
        'Conflict Detection': {
            'multiplier': 100,
            'reason': 'Very complex queries with HAVING clauses'
        },
        'Scheduler Algorithm': {
            'multiplier': 20,
            'reason': 'Data loading queries with sorting'
        }
    }
    
    total_predicted = 0
    
    for category, info in predictions.items():
        current_avg = category_stats[category]['avg']
        predicted_avg = current_avg * info['multiplier']
        total_predicted += predicted_avg * category_stats[category]['count']
        
        print(f"{category}:")
        print(f"  Current avg:   {current_avg:>8.2f}ms")
        print(f"  Predicted avg: {predicted_avg:>8.2f}ms ({info['multiplier']}x slower)")
        print(f"  Reason: {info['reason']}")
        print()
    
    print(f"Total predicted time WITHOUT indexes: {total_predicted:.2f}ms")
    print(f"Current time WITH indexes:            {sum(all_times):.2f}ms")
    print(f"Expected slowdown:                    {total_predicted/sum(all_times):.1f}x\n")
    
    # Critical queries to watch
    print("=" * 80)
    print("⚠️  CRITICAL QUERIES TO WATCH")
    print("=" * 80)
    print("\nThese queries will likely see the biggest impact:\n")
    
    critical = [
        ('prof_conflicts', 51.22, 'Currently 51ms, could reach 5000ms+ (100x slower)'),
        ('professor_load', 19.66, 'Currently 20ms, could reach 600ms+ (30x slower)'),
        ('room_conflicts', 14.25, 'Currently 14ms, could reach 1400ms+ (100x slower)'),
        ('student_schedule', 1.70, 'Currently 2ms, could reach 85ms+ (50x slower)'),
        ('professor_schedule', 5.13, 'Currently 5ms, could reach 200ms+ (40x slower)')
    ]
    
    for query, current, prediction in critical:
        print(f"  🔥 {query}")
        print(f"     {prediction}")
        print()


def show_next_steps():
    """Show next steps for testing"""
    
    print("\n" + "=" * 80)
    print("NEXT STEPS - Testing Without Indexes")
    print("=" * 80)
    
    print("""
To complete your index comparison testing, you have 3 options:

OPTION 1: AUTOMATED FULL TEST (Recommended)
-------------------------------------------
Run the complete test cycle automatically:

    python3 index_testing.py test

This will:
  1. Backup all current indexes
  2. Run benchmark WITH indexes (done)
  3. Drop all indexes safely
  4. Run benchmark WITHOUT indexes
  5. Restore all indexes
  6. Generate comparison reports

Output files:
  • benchmark_WITH_indexes.json
  • benchmark_WITHOUT_indexes.json
  • benchmark_comparison.html
  • benchmark_comparison.txt


OPTION 2: INTERACTIVE MODE
---------------------------
Use the interactive tool:

    python3 index_testing.py

Then select option 5 (Full test cycle)


OPTION 3: MANUAL STEP-BY-STEP
------------------------------
1. Backup indexes:
   python3 index_testing.py backup

2. Drop indexes:
   python3 index_testing.py drop

3. Run benchmark:
   python3 benchmark_queries.py

4. Restore indexes:
   python3 index_testing.py restore index_backup_XXXXXX.json


⚠️  IMPORTANT NOTES:
-------------------
• The test will take 3-5 minutes total
• Your indexes will be safely backed up
• All indexes will be restored automatically
• The database will be safe throughout the process
• You can stop and restore at any time


🎯 EXPECTED RESULTS:
-------------------
Based on your current results, you should see:
• Overall: ~50x slower without indexes
• Simple queries: 3-5x slower
• Complex queries: 50-100x slower
• JOIN-heavy queries: Most impacted

This will clearly demonstrate the critical importance of proper indexing!
""")


def main():
    """Main entry point"""
    analyze_current_results()
    show_next_steps()


if __name__ == "__main__":
    main()
