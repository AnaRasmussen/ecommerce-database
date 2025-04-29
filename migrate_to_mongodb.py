import psycopg2
from pymongo import MongoClient
from datetime import datetime
import json
from bson import ObjectId
import time
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# PostgreSQL connection settings
PG_DB_NAME = "postgres"
PG_USER = "carterrobinson"
PG_PASSWORD = ""
PG_HOST = "localhost"
PG_PORT = "5432"

# MongoDB connection settings
MONGO_URI = "mongodb://localhost:27017/"
MONGO_DB_NAME = "ecommerce_mongodb"

def check_mongodb_connection():
    """Check if MongoDB is running and accessible"""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        client.server_info()  # will throw an exception if cannot connect
        return True
    except Exception as e:
        print(f"\nError: MongoDB is not running or not accessible.")
        print("Please ensure MongoDB is installed and running.")
        print("On macOS, you can start MongoDB with: brew services start mongodb-community")
        print("On Linux: sudo systemctl start mongod")
        print("On Windows: net start MongoDB")
        return False

def get_postgres_connection():
    logger.info("Connecting to PostgreSQL...")
    return psycopg2.connect(
        dbname=PG_DB_NAME,
        user=PG_USER,
        password=PG_PASSWORD,
        host=PG_HOST,
        port=PG_PORT
    )

def get_mongo_connection():
    logger.info("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB_NAME]

def migrate_users(pg_conn, mongo_db):
    logger.info("Starting user migration...")
    cur = pg_conn.cursor()
    cur.execute("SELECT user_id, name, email, signup_source FROM users")
    users = cur.fetchall()
    logger.info(f"Found {len(users)} users in PostgreSQL")
    
    mongo_users = mongo_db.users
    mongo_users.delete_many({})  # Clear existing data
    logger.info("Cleared existing MongoDB users collection")
    
    for user in users:
        user_doc = {
            "_id": user[0],
            "name": user[1],
            "email": user[2],
            "signup_source": user[3]
        }
        mongo_users.insert_one(user_doc)
    logger.info(f"Successfully migrated {len(users)} users to MongoDB")

def migrate_products(pg_conn, mongo_db):
    logger.info("Starting product migration...")
    cur = pg_conn.cursor()
    cur.execute("SELECT product_id, name, category, price, created_at, is_active FROM products")
    products = cur.fetchall()
    logger.info(f"Found {len(products)} products in PostgreSQL")
    
    mongo_products = mongo_db.products
    mongo_products.delete_many({})  # Clear existing data
    logger.info("Cleared existing MongoDB products collection")
    
    for product in products:
        product_doc = {
            "_id": product[0],
            "name": product[1],
            "category": product[2],
            "price": float(product[3]),  # Convert Decimal to float
            "created_at": product[4],
            "is_active": product[5]
        }
        mongo_products.insert_one(product_doc)
    logger.info(f"Successfully migrated {len(products)} products to MongoDB")

def migrate_orders(pg_conn, mongo_db):
    logger.info("Starting order migration...")
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT o.order_id, o.user_id, o.order_date, o.status, o.total_amount
        FROM orders o
    """)
    orders = cur.fetchall()
    logger.info(f"Found {len(orders)} orders in PostgreSQL")
    
    mongo_orders = mongo_db.orders
    mongo_orders.delete_many({})  # Clear existing data
    logger.info("Cleared existing MongoDB orders collection")
    
    for order in orders:
        order_doc = {
            "_id": order[0],
            "user_id": order[1],
            "order_date": order[2],
            "status": order[3],
            "total_amount": float(order[4])  # Convert Decimal to float
        }
        mongo_orders.insert_one(order_doc)
    logger.info(f"Successfully migrated {len(orders)} orders to MongoDB")

def migrate_reviews(pg_conn, mongo_db):
    logger.info("Starting review migration...")
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT review_id, user_id, product_id, rating, comment, review_date
        FROM reviews
    """)
    reviews = cur.fetchall()
    logger.info(f"Found {len(reviews)} reviews in PostgreSQL")
    
    mongo_reviews = mongo_db.reviews
    mongo_reviews.delete_many({})  # Clear existing data
    logger.info("Cleared existing MongoDB reviews collection")
    
    for review in reviews:
        review_doc = {
            "_id": review[0],
            "user_id": review[1],
            "product_id": review[2],
            "rating": review[3],
            "comment": review[4],
            "review_date": review[5]
        }
        mongo_reviews.insert_one(review_doc)
    logger.info(f"Successfully migrated {len(reviews)} reviews to MongoDB")

def migrate_carts(pg_conn, mongo_db):
    logger.info("Starting cart migration...")
    cur = pg_conn.cursor()
    cur.execute("""
        SELECT cart_id, user_id, created_at, status
        FROM carts
    """)
    carts = cur.fetchall()
    logger.info(f"Found {len(carts)} carts in PostgreSQL")
    
    mongo_carts = mongo_db.carts
    mongo_carts.delete_many({})  # Clear existing data
    logger.info("Cleared existing MongoDB carts collection")
    
    for cart in carts:
        cart_doc = {
            "_id": cart[0],
            "user_id": cart[1],
            "created_at": cart[2],
            "status": cart[3]
        }
        mongo_carts.insert_one(cart_doc)
    logger.info(f"Successfully migrated {len(carts)} carts to MongoDB")

def main():
    # Check MongoDB connection first
    if not check_mongodb_connection():
        sys.exit(1)
    
    start_time = time.time()
    
    pg_conn = None
    try:
        pg_conn = get_postgres_connection()
        mongo_db = get_mongo_connection()
        
        logger.info("Starting migration process...")
        
        migrate_users(pg_conn, mongo_db)
        migrate_products(pg_conn, mongo_db)
        migrate_orders(pg_conn, mongo_db)
        migrate_reviews(pg_conn, mongo_db)
        migrate_carts(pg_conn, mongo_db)
        
        # Create indexes
        print("\nCreating indexes...")
        mongo_db.users.create_index("email")
        mongo_db.products.create_index("category")
        mongo_db.orders.create_index("user_id")
        mongo_db.orders.create_index("order_date")
        mongo_db.reviews.create_index([("product_id", 1), ("rating", 1)])
        mongo_db.carts.create_index("user_id")
        
        # Verify data
        print("\nVerification:")
        print(f"Users: {mongo_db.users.count_documents({})}")
        print(f"Products: {mongo_db.products.count_documents({})}")
        print(f"Orders: {mongo_db.orders.count_documents({})}")
        print(f"Reviews: {mongo_db.reviews.count_documents({})}")
        print(f"Carts: {mongo_db.carts.count_documents({})}")
        
        print(f"\nMigration completed in {time.time() - start_time:.2f} seconds")
        
        logger.info("Migration completed successfully!")
        
    except Exception as e:
        logger.error(f"Error during migration: {str(e)}")
        raise
    finally:
        if pg_conn:
            pg_conn.close()
            logger.info("PostgreSQL connection closed")

if __name__ == "__main__":
    main() 