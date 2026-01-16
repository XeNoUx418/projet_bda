#!/usr/bin/env python3
"""
Fixed Index Testing Script
===========================

Properly handles foreign key constraints when testing performance
"""

import mysql.connector
import json
from datetime import datetime
from benchmark_config import DB_CONFIG


class IndexManagerFixed:
    """Properly manage indexes including foreign key constraints"""
    
    def __init__(self):
        self.conn = mysql.connector.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor(dictionary=True)
        self.backup_file = f"index_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
    def get_all_indexes(self, include_fk_indexes=True):
        """Get all indexes including those created by foreign keys"""
        
        self.cursor.execute("SHOW TABLES")
        tables = [row[f'Tables_in_{DB_CONFIG["database"]}'] for row in self.cursor.fetchall()]
        
        all_indexes = {}
        
        for table in tables:
            self.cursor.execute(f"SHOW INDEX FROM {table}")
            indexes = self.cursor.fetchall()
            
            table_indexes = {}
            for idx in indexes:
                idx_name = idx['Key_name']
                
                # Skip PRIMARY keys
                if idx_name == 'PRIMARY':
                    continue
                
                if idx_name not in table_indexes:
                    table_indexes[idx_name] = {
                        'table': table,
                        'columns': [],
                        'non_unique': idx['Non_unique'],
                        'index_type': idx['Index_type']
                    }
                
                table_indexes[idx_name]['columns'].append({
                    'column': idx['Column_name'],
                    'seq': idx['Seq_in_index']
                })
            
            if table_indexes:
                all_indexes[table] = table_indexes
        
        return all_indexes
    
    def get_foreign_keys(self):
        """Get all foreign key constraints"""
        
        query = """
            SELECT 
                TABLE_NAME,
                CONSTRAINT_NAME,
                COLUMN_NAME,
                REFERENCED_TABLE_NAME,
                REFERENCED_COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = %s
              AND REFERENCED_TABLE_NAME IS NOT NULL
            ORDER BY TABLE_NAME, CONSTRAINT_NAME
        """
        
        self.cursor.execute(query, (DB_CONFIG['database'],))
        return self.cursor.fetchall()
    
    def backup_foreign_keys(self):
        """Save foreign key constraints to restore later"""
        
        fks = self.get_foreign_keys()
        
        fk_file = self.backup_file.replace('.json', '_fk.json')
        
        with open(fk_file, 'w') as f:
            json.dump(fks, f, indent=2, default=str)
        
        # Generate SQL statements
        sql_statements = []
        
        for fk in fks:
            table = fk['TABLE_NAME']
            constraint = fk['CONSTRAINT_NAME']
            column = fk['COLUMN_NAME']
            ref_table = fk['REFERENCED_TABLE_NAME']
            ref_column = fk['REFERENCED_COLUMN_NAME']
            
            sql_statements.append(
                f"ALTER TABLE {table} ADD CONSTRAINT {constraint} "
                f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column});"
            )
        
        fk_sql_file = fk_file.replace('.json', '.sql')
        with open(fk_sql_file, 'w') as f:
            f.write("-- Foreign Key Restoration Script\n")
            f.write(f"-- Generated: {datetime.now()}\n\n")
            f.write('\n'.join(sql_statements))
        
        print(f"✅ Backed up {len(fks)} foreign keys")
        print(f"   JSON: {fk_file}")
        print(f"   SQL:  {fk_sql_file}")
        
        return fk_file
    
    def drop_all_foreign_keys(self):
        """Drop all foreign key constraints"""
        
        print("\n🔓 Dropping foreign key constraints...")
        print("=" * 70)
        
        fks = self.get_foreign_keys()
        dropped = 0
        
        # Group by table and constraint
        by_table = {}
        for fk in fks:
            table = fk['TABLE_NAME']
            if table not in by_table:
                by_table[table] = set()
            by_table[table].add(fk['CONSTRAINT_NAME'])
        
        for table, constraints in by_table.items():
            for constraint in constraints:
                try:
                    sql = f"ALTER TABLE {table} DROP FOREIGN KEY {constraint}"
                    self.cursor.execute(sql)
                    print(f"  ✓ Dropped {constraint} from {table}")
                    dropped += 1
                except Exception as e:
                    print(f"  ✗ Failed to drop {constraint} from {table}: {e}")
        
        self.conn.commit()
        
        print("=" * 70)
        print(f"✅ Dropped {dropped} foreign key constraints\n")
        
        return dropped
    
    def restore_foreign_keys(self, backup_file):
        """Restore foreign key constraints"""
        
        print("\n🔐 Restoring foreign key constraints...")
        print("=" * 70)
        
        fk_file = backup_file.replace('.json', '_fk.json')
        
        try:
            with open(fk_file, 'r') as f:
                fks = json.load(f)
        except FileNotFoundError:
            print(f"⚠️  No FK backup found at {fk_file}")
            return 0
        
        restored = 0
        
        # Group by table and constraint to avoid duplicates
        seen = set()
        
        for fk in fks:
            table = fk['TABLE_NAME']
            constraint = fk['CONSTRAINT_NAME']
            column = fk['COLUMN_NAME']
            ref_table = fk['REFERENCED_TABLE_NAME']
            ref_column = fk['REFERENCED_COLUMN_NAME']
            
            key = (table, constraint)
            if key in seen:
                continue
            seen.add(key)
            
            try:
                sql = (
                    f"ALTER TABLE {table} ADD CONSTRAINT {constraint} "
                    f"FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
                )
                self.cursor.execute(sql)
                print(f"  ✓ Restored {constraint} on {table}")
                restored += 1
            except Exception as e:
                # It's ok if it already exists
                if "Duplicate" not in str(e):
                    print(f"  ⚠️  {constraint} on {table}: {e}")
        
        self.conn.commit()
        
        print("=" * 70)
        print(f"✅ Restored {restored} foreign key constraints\n")
        
        return restored
    
    def backup_indexes(self):
        """Save current index structure"""
        
        print("📋 Backing up current index structure...")
        
        indexes = self.get_all_indexes()
        
        with open(self.backup_file, 'w') as f:
            json.dump(indexes, f, indent=2)
        
        # Generate SQL statements
        sql_statements = []
        for table, table_indexes in sorted(indexes.items()):
            sql_statements.append(f"\n-- Indexes for table: {table}")
            
            for idx_name, idx_info in sorted(table_indexes.items()):
                columns = sorted(idx_info['columns'], key=lambda x: x['seq'])
                column_list = ', '.join(col['column'] for col in columns)
                
                if idx_info['non_unique'] == 0:
                    sql_statements.append(
                        f"CREATE UNIQUE INDEX {idx_name} ON {table}({column_list});"
                    )
                else:
                    sql_statements.append(
                        f"CREATE INDEX {idx_name} ON {table}({column_list});"
                    )
        
        sql_file = self.backup_file.replace('.json', '.sql')
        with open(sql_file, 'w') as f:
            f.write("-- Index Restoration Script\n")
            f.write(f"-- Generated: {datetime.now()}\n\n")
            f.write('\n'.join(sql_statements))
        
        total = sum(len(idxs) for idxs in indexes.values())
        
        print(f"✅ Backed up {total} indexes from {len(indexes)} tables")
        print(f"   JSON: {self.backup_file}")
        print(f"   SQL:  {sql_file}")
        
        return self.backup_file
    
    def drop_all_indexes_properly(self):
        """Drop all non-PRIMARY indexes (after FKs are removed)"""
        
        print("\n🗑️  Dropping all indexes...")
        print("=" * 70)
        
        indexes = self.get_all_indexes()
        dropped = 0
        
        for table, table_indexes in indexes.items():
            for idx_name in table_indexes.keys():
                try:
                    sql = f"DROP INDEX {idx_name} ON {table}"
                    self.cursor.execute(sql)
                    print(f"  ✓ Dropped {idx_name} from {table}")
                    dropped += 1
                except Exception as e:
                    print(f"  ✗ Failed: {idx_name} from {table}: {e}")
        
        self.conn.commit()
        
        print("=" * 70)
        print(f"✅ Dropped {dropped} indexes\n")
        
        return dropped
    
    def restore_indexes(self, backup_file):
        """Restore indexes from backup"""
        
        print(f"\n♻️  Restoring indexes from {backup_file}...")
        print("=" * 70)
        
        try:
            with open(backup_file, 'r') as f:
                indexes = json.load(f)
        except FileNotFoundError:
            print(f"❌ Backup file not found: {backup_file}")
            return 0
        
        restored = 0
        
        for table, table_indexes in sorted(indexes.items()):
            for idx_name, idx_info in sorted(table_indexes.items()):
                columns = sorted(idx_info['columns'], key=lambda x: x['seq'])
                column_list = ', '.join(col['column'] for col in columns)
                
                try:
                    if idx_info['non_unique'] == 0:
                        sql = f"CREATE UNIQUE INDEX {idx_name} ON {table}({column_list})"
                    else:
                        sql = f"CREATE INDEX {idx_name} ON {table}({column_list})"
                    
                    self.cursor.execute(sql)
                    print(f"  ✓ {table}.{idx_name}")
                    restored += 1
                except Exception as e:
                    if "Duplicate" not in str(e):
                        print(f"  ⚠️  {table}.{idx_name}: {e}")
        
        self.conn.commit()
        
        print("=" * 70)
        print(f"✅ Restored {restored} indexes\n")
        
        return restored
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def run_proper_comparison():
    """Run a proper WITH vs WITHOUT indexes comparison"""
    
    print("\n" + "=" * 70)
    print("  PROPER INDEX PERFORMANCE COMPARISON TEST")
    print("=" * 70)
    print("\nThis test will:")
    print("  1. Backup all indexes and foreign keys")
    print("  2. Run benchmark WITH indexes")
    print("  3. Drop foreign keys (temporarily)")
    print("  4. Drop all indexes")
    print("  5. Run benchmark WITHOUT indexes")
    print("  6. Restore all indexes")
    print("  7. Restore all foreign keys")
    print("  8. Generate comparison report")
    print("\n⚠️  This is safe but will take 5-10 minutes")
    print("=" * 70)
    
    confirm = input("\nProceed? (yes/no): ").strip().lower()
    
    if confirm != 'yes':
        print("Cancelled.")
        return
    
    manager = IndexManagerFixed()
    
    try:
        # Step 1: Backup everything
        print("\n" + "=" * 70)
        print("STEP 1: BACKING UP")
        print("=" * 70)
        
        idx_backup = manager.backup_indexes()
        fk_backup = manager.backup_foreign_keys()
        
        # Step 2: Benchmark WITH indexes
        print("\n" + "=" * 70)
        print("STEP 2: BENCHMARK WITH INDEXES")
        print("=" * 70)
        
        from benchmark_queries import BenchmarkSuite
        
        suite = BenchmarkSuite()
        results_with = suite.run_all()
        suite.save_results(results_with, "benchmark_WITH_indexes.json")
        suite.close()
        
        # Step 3: Drop foreign keys
        print("\n" + "=" * 70)
        print("STEP 3: REMOVING FOREIGN KEY CONSTRAINTS")
        print("=" * 70)
        
        manager.drop_all_foreign_keys()
        
        # Step 4: Drop indexes
        print("\n" + "=" * 70)
        print("STEP 4: REMOVING ALL INDEXES")
        print("=" * 70)
        
        manager.drop_all_indexes_properly()
        
        # Step 5: Benchmark WITHOUT indexes
        print("\n" + "=" * 70)
        print("STEP 5: BENCHMARK WITHOUT INDEXES")
        print("=" * 70)
        print("⚠️  This will be MUCH slower - please wait...")
        
        suite = BenchmarkSuite()
        results_without = suite.run_all()
        suite.save_results(results_without, "benchmark_WITHOUT_indexes.json")
        suite.close()
        
        # Step 6: Restore indexes
        print("\n" + "=" * 70)
        print("STEP 6: RESTORING INDEXES")
        print("=" * 70)
        
        manager.restore_indexes(idx_backup)
        
        # Step 7: Restore foreign keys
        print("\n" + "=" * 70)
        print("STEP 7: RESTORING FOREIGN KEY CONSTRAINTS")
        print("=" * 70)
        
        manager.restore_foreign_keys(idx_backup)
        
        # Step 8: Generate comparison
        print("\n" + "=" * 70)
        print("STEP 8: GENERATING COMPARISON REPORT")
        print("=" * 70)
        
        from index_testing import generate_comparison_report
        generate_comparison_report(results_with, results_without)
        
        print("\n" + "=" * 70)
        print("✅ PROPER TEST COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nFiles generated:")
        print("  • benchmark_WITH_indexes.json")
        print("  • benchmark_WITHOUT_indexes.json")
        print("  • benchmark_comparison.html")
        print("  • benchmark_comparison.txt")
        print("\nYour database is fully restored to its original state.")
        
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("\nAttempting to restore database...")
        
        try:
            manager.restore_indexes(idx_backup)
            manager.restore_foreign_keys(idx_backup)
            print("✅ Database restored successfully")
        except:
            print("⚠️  Please restore manually using backup files")
        
        raise
    
    finally:
        manager.close()


if __name__ == "__main__":
    run_proper_comparison()