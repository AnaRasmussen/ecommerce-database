import psycopg2
from pymongo import MongoClient
from tabulate import tabulate
import time

# Database connection settings
POSTGRES_CONFIG = {
    "dbname": "postgres",
    "user": "carterrobinson",
    "password": "",
    "host": "localhost",
    "port": "5432"
}

MONGO_CONFIG = {
    "host": "localhost",
    "port": 27017,
    "dbname": "ecommerce_mongodb"
}

def connect_postgres():
    return psycopg2.connect(**POSTGRES_CONFIG)

def connect_mongo():
    client = MongoClient(f"mongodb://{MONGO_CONFIG['host']}:{MONGO_CONFIG['port']}/")
    return client[MONGO_CONFIG['dbname']]

def print_table(title, headers, data):
    print(f"\n{title}")
    print("=" * 80)
    print(tabulate(data, headers=headers, tablefmt="grid"))
    print("=" * 80)

def visualize_data():
    print("🔍 Visualizing Data Migration")
    print("=" * 80)
    
    # Connect to both databases
    pg_conn = connect_postgres()
    mongo_db = connect_mongo()
    
    try:
        # 1. Users
        print("\n👥 Users")
        print("-" * 40)
        
        # PostgreSQL Users
        cur = pg_conn.cursor()
        cur.execute("SELECT user_id, name, email, signup_source FROM users LIMIT 5")
        pg_users = cur.fetchall()
        print_table("PostgreSQL Users", ["ID", "Name", "Email", "Signup Source"], pg_users)
        
        # MongoDB Users
        mongo_users = list(mongo_db.users.find({}, {"_id": 1, "name": 1, "email": 1, "signup_source": 1}).limit(5))
        mongo_users_data = [(u["_id"], u["name"], u["email"], u.get("signup_source", "")) for u in mongo_users]
        print_table("MongoDB Users", ["ID", "Name", "Email", "Signup Source"], mongo_users_data)
        
        # 2. Products
        print("\n🛍️ Products")
        print("-" * 40)
        
        # PostgreSQL Products
        cur.execute("SELECT product_id, name, category, price FROM products LIMIT 5")
        pg_products = cur.fetchall()
        print_table("PostgreSQL Products", ["ID", "Name", "Category", "Price"], pg_products)
        
        # MongoDB Products
        mongo_products = list(mongo_db.products.find({}, {"_id": 1, "name": 1, "category": 1, "price": 1}).limit(5))
        mongo_products_data = [(p["_id"], p["name"], p["category"], p["price"]) for p in mongo_products]
        print_table("MongoDB Products", ["ID", "Name", "Category", "Price"], mongo_products_data)
        
        # 3. Orders
        print("\n📦 Orders")
        print("-" * 40)
        
        # PostgreSQL Orders
        cur.execute("""
            SELECT o.order_id, u.name, o.order_date, o.total_amount 
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            LIMIT 5
        """)
        pg_orders = cur.fetchall()
        print_table("PostgreSQL Orders", ["ID", "User", "Date", "Total"], pg_orders)
        
        # MongoDB Orders
        mongo_orders = list(mongo_db.orders.find({}, {"_id": 1, "user_id": 1, "order_date": 1, "total_amount": 1}).limit(5))
        mongo_orders_data = []
        for order in mongo_orders:
            user = mongo_db.users.find_one({"_id": order["user_id"]})
            mongo_orders_data.append((
                order["_id"],
                user["name"] if user else "Unknown",
                order["order_date"],
                order["total_amount"]
            ))
        print_table("MongoDB Orders", ["ID", "User", "Date", "Total"], mongo_orders_data)
        
        # 4. Statistics
        print("\n📊 Database Statistics")
        print("-" * 40)
        
        # PostgreSQL Stats
        cur.execute("SELECT COUNT(*) FROM users")
        pg_user_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products")
        pg_product_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders")
        pg_order_count = cur.fetchone()[0]
        
        # MongoDB Stats
        mongo_user_count = mongo_db.users.count_documents({})
        mongo_product_count = mongo_db.products.count_documents({})
        mongo_order_count = mongo_db.orders.count_documents({})
        
        stats_data = [
            ["Users", pg_user_count, mongo_user_count],
            ["Products", pg_product_count, mongo_product_count],
            ["Orders", pg_order_count, mongo_order_count]
        ]
        print_table("Record Counts", ["Collection", "PostgreSQL", "MongoDB"], stats_data)
        
    finally:
        pg_conn.close()

if __name__ == "__main__":
    visualize_data() 