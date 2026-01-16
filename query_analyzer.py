#!/usr/bin/env python3
"""
Advanced SQL Query Analyzer
============================

Analyzes query execution plans and provides optimization recommendations
"""

import mysql.connector
from typing import Dict, List, Any
import json
from benchmark_config import DB_CONFIG, OPTIMIZATION_TIPS


class QueryAnalyzer:
    """Analyzes query execution plans and suggests optimizations"""
    
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)
    
    def analyze_query(self, query: str, params: tuple = None) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a query
        
        Returns detailed execution plan analysis and recommendations
        """
        analysis = {
            'query': query[:200] + '...' if len(query) > 200 else query,
            'explain_output': [],
            'issues': [],
            'recommendations': [],
            'index_usage': {},
            'estimated_rows': 0,
            'performance_score': 100  # Start at 100, deduct for issues
        }
        
        # Get EXPLAIN output
        try:
            self.cursor.execute(f"EXPLAIN {query}", params or ())
            explain = self.cursor.fetchall()
            analysis['explain_output'] = explain
            
            # Analyze each table in the execution plan
            for row in explain:
                self._analyze_explain_row(row, analysis)
            
        except Exception as e:
            analysis['issues'].append(f"Failed to analyze query: {str(e)}")
            analysis['performance_score'] = 0
        
        # Generate overall recommendations
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _analyze_explain_row(self, row: Dict, analysis: Dict):
        """Analyze a single row from EXPLAIN output"""
        
        table = row.get('table', 'unknown')
        select_type = row.get('select_type', '')
        type_ = row.get('type', '')
        possible_keys = row.get('possible_keys')
        key = row.get('key')
        rows = row.get('rows', 0)
        extra = row.get('Extra', '')
        
        # Track estimated rows
        analysis['estimated_rows'] += rows or 0
        
        # Check for full table scans
        if type_ == 'ALL':
            analysis['issues'].append(
                f"Table '{table}': Full table scan detected ({rows} rows)"
            )
            analysis['performance_score'] -= 20
            
            if not possible_keys:
                analysis['recommendations'].append(
                    f"Add index to table '{table}' - no possible keys available"
                )
        
        # Check for missing index usage
        if possible_keys and not key:
            analysis['issues'].append(
                f"Table '{table}': Index available but not used"
            )
            analysis['performance_score'] -= 10
            analysis['recommendations'].append(
                f"Review query conditions for table '{table}' - possible keys: {possible_keys}"
            )
        
        # Track index usage
        if key:
            analysis['index_usage'][table] = key
        
        # Check for filesort (slow)
        if 'Using filesort' in extra:
            analysis['issues'].append(
                f"Table '{table}': Using filesort (slow for large datasets)"
            )
            analysis['performance_score'] -= 15
            analysis['recommendations'].append(
                f"Consider adding composite index for ORDER BY columns in table '{table}'"
            )
        
        # Check for temporary table
        if 'Using temporary' in extra:
            analysis['issues'].append(
                f"Table '{table}': Using temporary table"
            )
            analysis['performance_score'] -= 10
            analysis['recommendations'].append(
                f"Query creates temporary table - consider restructuring joins or GROUP BY"
            )
        
        # Check for large row scans
        if rows and rows > 10000:
            analysis['issues'].append(
                f"Table '{table}': Scanning {rows} rows"
            )
            analysis['performance_score'] -= 15
            analysis['recommendations'].append(
                f"Table '{table}' scans many rows - add more selective WHERE conditions or indexes"
            )
        
        # Check for subqueries
        if select_type in ['DEPENDENT SUBQUERY', 'UNCACHEABLE SUBQUERY']:
            analysis['issues'].append(
                f"Table '{table}': Dependent subquery detected (can be slow)"
            )
            analysis['performance_score'] -= 20
            analysis['recommendations'].append(
                f"Consider rewriting subquery as JOIN for table '{table}'"
            )
    
    def _generate_recommendations(self, analysis: Dict):
        """Generate overall optimization recommendations"""
        
        # High row count recommendation
        if analysis['estimated_rows'] > 50000:
            analysis['recommendations'].append(
                "⚠️  High total row scan detected - consider adding WHERE filters or pagination"
            )
        
        # Index coverage recommendation
        if len(analysis['index_usage']) < len(analysis['explain_output']):
            analysis['recommendations'].append(
                "💡 Not all tables use indexes - review indexing strategy"
            )
        
        # Performance score summary
        score = analysis['performance_score']
        if score >= 80:
            analysis['summary'] = "✅ Query is well-optimized"
        elif score >= 60:
            analysis['summary'] = "⚠️  Query has minor performance issues"
        elif score >= 40:
            analysis['summary'] = "⚠️  Query needs optimization"
        else:
            analysis['summary'] = "❌ Query has serious performance issues"
    
    def analyze_all_indexes(self) -> Dict[str, Any]:
        """Analyze all indexes in the database"""
        
        # Get all tables
        self.cursor.execute("SHOW TABLES")
        tables = [row[f'Tables_in_{DB_CONFIG["database"]}'] for row in self.cursor.fetchall()]
        
        index_report = {}
        
        for table in tables:
            # Get indexes for this table
            self.cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = self.cursor.fetchall()
            
            # Get table statistics
            self.cursor.execute(f"SHOW TABLE STATUS LIKE '{table}'")
            stats = self.cursor.fetchone()
            
            index_report[table] = {
                'indexes': {},
                'row_count': stats.get('Rows', 0),
                'data_length': stats.get('Data_length', 0),
                'index_length': stats.get('Index_length', 0),
                'recommendations': []
            }
            
            # Group indexes by name
            for idx in indexes:
                idx_name = idx['Key_name']
                if idx_name not in index_report[table]['indexes']:
                    index_report[table]['indexes'][idx_name] = {
                        'columns': [],
                        'type': idx['Index_type'],
                        'unique': idx['Non_unique'] == 0
                    }
                index_report[table]['indexes'][idx_name]['columns'].append(idx['Column_name'])
            
            # Check for missing recommended indexes
            if table == 'planning_examens' and 'idx_planning_examen' not in index_report[table]['indexes']:
                index_report[table]['recommendations'].append(
                    "Consider adding index on id_examen for faster lookups"
                )
            
            # Check for large tables without indexes (except PRIMARY)
            if stats.get('Rows', 0) > 1000 and len(index_report[table]['indexes']) <= 1:
                index_report[table]['recommendations'].append(
                    f"⚠️  Large table ({stats['Rows']} rows) with minimal indexing"
                )
        
        return index_report
    
    def suggest_missing_indexes(self, query: str, params: tuple = None) -> List[str]:
        """Suggest indexes that could improve query performance"""
        
        suggestions = []
        
        # Analyze the query
        analysis = self.analyze_query(query, params)
        
        # Look for WHERE clauses without indexes
        for row in analysis['explain_output']:
            table = row.get('table')
            type_ = row.get('type')
            possible_keys = row.get('possible_keys')
            key = row.get('key')
            
            if type_ == 'ALL' and not key:
                # Suggest index based on query structure
                # This is a simplified heuristic - would need query parsing for accuracy
                suggestions.append(
                    f"CREATE INDEX idx_{table}_filter ON {table}(<filtered_column>);"
                )
        
        return suggestions
    
    def compare_queries(self, query1: str, query2: str, params1=None, params2=None) -> Dict:
        """Compare two queries and determine which is more efficient"""
        
        analysis1 = self.analyze_query(query1, params1)
        analysis2 = self.analyze_query(query2, params2)
        
        return {
            'query1': {
                'score': analysis1['performance_score'],
                'estimated_rows': analysis1['estimated_rows'],
                'issues': len(analysis1['issues'])
            },
            'query2': {
                'score': analysis2['performance_score'],
                'estimated_rows': analysis2['estimated_rows'],
                'issues': len(analysis2['issues'])
            },
            'winner': 'query1' if analysis1['performance_score'] > analysis2['performance_score'] else 'query2',
            'recommendation': 'Query 1 is more efficient' if analysis1['performance_score'] > analysis2['performance_score'] else 'Query 2 is more efficient'
        }
    
    def generate_optimization_report(self, queries: Dict[str, str]) -> str:
        """Generate a comprehensive optimization report for multiple queries"""
        
        report = []
        report.append("=" * 80)
        report.append("QUERY OPTIMIZATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        for name, query in queries.items():
            analysis = self.analyze_query(query)
            
            report.append(f"Query: {name}")
            report.append("-" * 80)
            report.append(f"Performance Score: {analysis['performance_score']}/100")
            report.append(f"Summary: {analysis['summary']}")
            report.append(f"Estimated Rows Scanned: {analysis['estimated_rows']}")
            report.append("")
            
            if analysis['issues']:
                report.append("Issues Found:")
                for issue in analysis['issues']:
                    report.append(f"  • {issue}")
                report.append("")
            
            if analysis['recommendations']:
                report.append("Recommendations:")
                for rec in analysis['recommendations']:
                    report.append(f"  → {rec}")
                report.append("")
            
            if analysis['index_usage']:
                report.append("Indexes Used:")
                for table, idx in analysis['index_usage'].items():
                    report.append(f"  ✓ {table}: {idx}")
                report.append("")
            
            report.append("=" * 80)
            report.append("")
        
        return "\n".join(report)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


# ==========================================
# EXAMPLE USAGE
# ==========================================

if __name__ == "__main__":
    analyzer = QueryAnalyzer()
    
    try:
        # Example: Analyze a complex query
        complex_query = """
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
        
        print("Analyzing professor schedule query...")
        analysis = analyzer.analyze_query(complex_query, (1, '2026-01-06', '2026-01-26'))
        
        print(f"\nPerformance Score: {analysis['performance_score']}/100")
        print(f"Summary: {analysis['summary']}")
        print(f"Estimated Rows: {analysis['estimated_rows']}")
        
        if analysis['issues']:
            print("\nIssues:")
            for issue in analysis['issues']:
                print(f"  • {issue}")
        
        if analysis['recommendations']:
            print("\nRecommendations:")
            for rec in analysis['recommendations']:
                print(f"  → {rec}")
        
        # Analyze all database indexes
        print("\n" + "=" * 80)
        print("DATABASE INDEX ANALYSIS")
        print("=" * 80)
        
        index_report = analyzer.analyze_all_indexes()
        
        for table, info in index_report.items():
            if info['recommendations']:
                print(f"\n{table}:")
                print(f"  Rows: {info['row_count']}")
                print(f"  Indexes: {len(info['indexes'])}")
                for rec in info['recommendations']:
                    print(f"  {rec}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        analyzer.close()
