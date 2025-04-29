import psycopg2
import time
from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np

# Database connection settings
DB_CONFIG = {
    "dbname": "postgres",
    "user": "carterrobinson",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

def connect_db():
    return psycopg2.connect(**DB_CONFIG)

def analyze_query_performance(conn, query, params=None, iterations=10):
    """Analyze query performance with EXPLAIN ANALYZE"""
    cur = conn.cursor()
    
    # Get execution plan
    cur.execute(f"EXPLAIN ANALYZE {query}", params or ())
    plan = cur.fetchall()
    
    # Measure execution time
    times = []
    for _ in range(iterations):
        start = time.time()
        cur.execute(query, params or ())
        cur.fetchall()
        times.append(time.time() - start)
    
    return {
        "plan": plan,
        "avg_time": sum(times) / len(times),
        "min_time": min(times),
        "max_time": max(times)
    }

def analyze_index_usage(conn):
    """Analyze index usage statistics"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            schemaname, 
            relname as tablename, 
            indexrelname as indexname, 
            idx_scan, 
            idx_tup_read, 
            idx_tup_fetch
        FROM pg_stat_user_indexes
        ORDER BY idx_scan DESC;
    """)
    return cur.fetchall()

def suggest_indexes(conn):
    """Suggest potential indexes based on query patterns"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            schemaname, 
            tablename, 
            attname, 
            n_distinct, 
            correlation
        FROM pg_stats
        WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
        ORDER BY n_distinct DESC;
    """)
    return cur.fetchall()

def analyze_table_statistics(conn):
    """Analyze table statistics"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            schemaname, 
            relname as tablename, 
            n_live_tup, 
            n_dead_tup,
            last_vacuum,
            last_analyze
        FROM pg_stat_user_tables
        ORDER BY n_live_tup DESC;
    """)
    return cur.fetchall()

def analyze_long_running_queries(conn):
    """Find long-running queries"""
    cur = conn.cursor()
    cur.execute("""
        SELECT 
            pid,
            query,
            age(clock_timestamp(), query_start) as duration
        FROM pg_stat_activity
        WHERE state = 'active'
        AND query != '<IDLE>'
        ORDER BY duration DESC;
    """)
    return cur.fetchall()

def generate_performance_report():
    conn = connect_db()
    
    print("\n=== Database Performance Analysis Report ===\n")
    
    # 1. Analyze Key Queries
    print("\n1. Key Query Performance Analysis:")
    queries = [
        {
            "name": "Top Selling Products",
            "query": """
                SELECT p.name, SUM(oi.quantity) as total_sold
                FROM order_items oi
                JOIN products p ON oi.product_id = p.product_id
                GROUP BY p.product_id, p.name
                ORDER BY total_sold DESC
                LIMIT 10;
            """
        },
        {
            "name": "Customer Order History",
            "query": """
                SELECT u.name, COUNT(o.order_id) as order_count, SUM(o.total_amount) as total_spent
                FROM users u
                JOIN orders o ON u.user_id = o.user_id
                GROUP BY u.user_id, u.name
                ORDER BY total_spent DESC
                LIMIT 10;
            """
        },
        {
            "name": "Product Reviews Analysis",
            "query": """
                SELECT p.name, AVG(r.rating) as avg_rating, COUNT(r.review_id) as review_count
                FROM products p
                JOIN reviews r ON p.product_id = r.product_id
                GROUP BY p.product_id, p.name
                ORDER BY avg_rating DESC
                LIMIT 10;
            """
        }
    ]
    
    query_results = []
    for q in queries:
        result = analyze_query_performance(conn, q["query"])
        query_results.append([
            q["name"],
            f"{result['avg_time']:.4f}s",
            f"{result['min_time']:.4f}s",
            f"{result['max_time']:.4f}s"
        ])
    
    print(tabulate(query_results, 
                  headers=["Query", "Avg Time", "Min Time", "Max Time"],
                  tablefmt="grid"))
    
    # 2. Index Analysis
    print("\n2. Index Usage Analysis:")
    index_usage = analyze_index_usage(conn)
    print(tabulate(index_usage,
                  headers=["Schema", "Table", "Index", "Scans", "Tuples Read", "Tuples Fetched"],
                  tablefmt="grid"))
    
    # 3. Suggested Indexes
    print("\n3. Suggested Indexes:")
    suggested_indexes = suggest_indexes(conn)
    print(tabulate(suggested_indexes,
                  headers=["Schema", "Table", "Column", "Distinct Values", "Correlation"],
                  tablefmt="grid"))
    
    # 4. Table Statistics
    print("\n4. Table Statistics:")
    table_stats = analyze_table_statistics(conn)
    print(tabulate(table_stats,
                  headers=["Schema", "Table", "Live Tuples", "Dead Tuples", "Last Vacuum", "Last Analyze"],
                  tablefmt="grid"))
    
    # 5. Long Running Queries
    print("\n5. Long Running Queries:")
    long_queries = analyze_long_running_queries(conn)
    if long_queries:
        print(tabulate(long_queries,
                      headers=["PID", "Query", "Duration"],
                      tablefmt="grid"))
    else:
        print("No long-running queries found.")
    
    # Generate Recommendations
    print("\n=== Performance Recommendations ===")
    print("\n1. Index Optimization:")
    print("- Consider adding indexes on frequently joined columns")
    print("- Review and potentially remove unused indexes")
    print("- Create composite indexes for common query patterns")
    
    print("\n2. Query Optimization:")
    print("- Optimize complex joins in the top-selling products query")
    print("- Consider materialized views for frequently accessed data")
    print("- Add appropriate WHERE clauses to limit result sets")
    
    print("\n3. Maintenance Recommendations:")
    print("- Schedule regular VACUUM operations")
    print("- Update statistics with ANALYZE")
    print("- Consider partitioning large tables")
    
    conn.close()

if __name__ == "__main__":
    generate_performance_report() 