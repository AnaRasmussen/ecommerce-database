from flask import Flask, render_template, redirect, url_for, request, flash, session
from datetime import datetime
import uuid
import psycopg2
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages and sessions

# === Database connection settings ===
DB_NAME = "postgres"
DB_USER = "carterrobinson"
DB_PASSWORD = ""
DB_HOST = "localhost"
DB_PORT = "5432"

def get_connection():
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )

def random_user_id(conn):
    """ Helper to pick a random user from database """
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users ORDER BY RANDOM() LIMIT 1;")
    user_id = cur.fetchone()[0]
    cur.close()
    return user_id

# === ROUTES ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/products')
def products():
    # Get sort parameter from URL, default to 'newest'
    sort = request.args.get('sort', 'newest')
    
    conn = get_connection()
    cur = conn.cursor()
    
    # Base query
    query = """
        SELECT product_id, name, price, category
        FROM products
        WHERE is_active = TRUE
    """
    
    # Add sorting based on the sort parameter
    if sort == 'price_low':
        query += " ORDER BY price ASC"
    elif sort == 'price_high':
        query += " ORDER BY price DESC"
    else:  # default to newest
        query += " ORDER BY created_at DESC"
    
    query += ";"
    
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('products.html', products=rows, sort=sort)

@app.route('/add-to-cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart_id = session.get('cart_id')

    conn = get_connection()
    cur = conn.cursor()

    # If no cart yet, create one
    if not cart_id:
        cart_id = str(uuid.uuid4())
        user_id = random_user_id(conn)
        created_at = datetime.now()
        status = 'active'

        cur.execute("""
            INSERT INTO carts (cart_id, user_id, created_at, status)
            VALUES (%s, %s, %s, %s)
        """, (cart_id, user_id, created_at, status))
        session['cart_id'] = cart_id

    # Add item to cart_items table
    cart_item_id = str(uuid.uuid4())
    added_at = datetime.now()

    cur.execute("""
        INSERT INTO cart_items (cart_item_id, cart_id, product_id, added_at, removed_at)
        VALUES (%s, %s, %s, %s, NULL)
    """, (cart_item_id, cart_id, product_id, added_at))

    conn.commit()
    cur.close()
    conn.close()

    flash('Item added to cart!')
    return redirect(url_for('products'))


@app.route('/cart')
def view_cart():
    cart_id = session.get('cart_id')
    if not cart_id:
        return render_template('cart.html', products=[])

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.product_id, p.name, p.price
        FROM cart_items ci
        JOIN products p ON ci.product_id = p.product_id
        WHERE ci.cart_id = %s
        AND ci.removed_at IS NULL
    """, (cart_id,))
    products = cur.fetchall()
    cur.close()
    conn.close()

    return render_template('cart.html', products=products)


@app.route('/checkout', methods=['POST'])
def checkout():
    cart_id = session.get('cart_id')
    if not cart_id:
        flash('Your cart is empty.')
        return redirect(url_for('view_cart'))

    conn = get_connection()
    cur = conn.cursor()

    # Create Order
    order_id = str(uuid.uuid4())
    user_id = random_user_id(conn)
    order_date = datetime.now()
    status = 'completed'

    # Calculate total (example: 20.0 per item)
    cur.execute("""
        SELECT COUNT(*)
        FROM cart_items
        WHERE cart_id = %s AND removed_at IS NULL
    """, (cart_id,))
    item_count = cur.fetchone()[0]
    total_amount = item_count * 20.0

    cur.execute("""
        INSERT INTO orders (order_id, user_id, order_date, status, total_amount)
        VALUES (%s, %s, %s, %s, %s)
    """, (order_id, user_id, order_date, status, total_amount))

    # Create order items
    cur.execute("""
        SELECT product_id
        FROM cart_items
        WHERE cart_id = %s AND removed_at IS NULL
    """, (cart_id,))
    products = cur.fetchall()

    for (product_id,) in products:
        order_item_id = str(uuid.uuid4())
        quantity = 1
        unit_price = 20.0
        cur.execute("""
            INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price)
            VALUES (%s, %s, %s, %s, %s)
        """, (order_item_id, order_id, product_id, quantity, unit_price))

    # Delete cart (optional) or mark abandoned / completed
    cur.execute("""
        UPDATE carts SET status = 'converted' WHERE cart_id = %s
    """, (cart_id,))

    conn.commit()
    cur.close()
    conn.close()

    session.pop('cart_id', None)

    flash('Purchase completed successfully!')
    return redirect(url_for('products'))

@app.route('/top-rated')
def top_rated():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.name, ROUND(AVG(r.rating),2) as avg_rating, COUNT(r.review_id) as num_reviews
        FROM products p
        JOIN reviews r ON p.product_id = r.product_id
        WHERE p.is_active = TRUE
        GROUP BY p.product_id
        ORDER BY avg_rating DESC, num_reviews DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('top_rated.html', products=rows)


@app.route('/top-selling')
def top_selling():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.name, 
               COUNT(oi.order_id) as total_orders,
               SUM(oi.quantity) as total_quantity,
               SUM(oi.quantity * oi.unit_price) as total_revenue
        FROM products p
        JOIN order_items oi ON p.product_id = oi.product_id
        JOIN orders o ON oi.order_id = o.order_id
        WHERE o.status = 'completed'
        GROUP BY p.product_id
        ORDER BY total_quantity DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('top_selling.html', top_selling=rows)

@app.route('/repeat-customers')
def repeat_customers():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        WITH monthly_orders AS (
            SELECT user_id, DATE_TRUNC('month', order_date) AS month, COUNT(order_id) AS orders_count
            FROM orders
            GROUP BY user_id, month
        )
        SELECT TO_CHAR(month, 'Month YYYY') as month_text, COUNT(user_id) as repeat_customers
        FROM monthly_orders
        WHERE orders_count > 1
        GROUP BY month
        ORDER BY month;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('repeat_customers.html', stats=rows)

@app.route('/abandoned')
def abandoned():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.name, COUNT(ci.cart_id) as abandoned_count
        FROM products p
        JOIN cart_items ci ON p.product_id = ci.product_id
        JOIN carts c ON ci.cart_id = c.cart_id
        WHERE c.status = 'abandoned'
        GROUP BY p.product_id
        ORDER BY abandoned_count DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('abandoned_products.html', abandoned_products=rows)

@app.route('/rate/<product_id>', methods=['POST'])
def rate_product(product_id):
    rating = int(request.form['rating'])
    comment = "Rated from frontend"  # Could allow comment too if you want later

    conn = get_connection()
    cur = conn.cursor()

    review_id = str(uuid.uuid4())
    user_id = random_user_id(conn)
    review_date = datetime.now()

    cur.execute("""
        INSERT INTO reviews (review_id, user_id, product_id, rating, comment, review_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (review_id, user_id, product_id, rating, comment, review_date))

    conn.commit()
    cur.close()
    conn.close()

    flash('Thank you for rating!')
    return redirect(url_for('products'))

@app.route('/abandon-cart', methods=['POST'])
def abandon_cart():
    cart_id = session.get('cart_id')
    if not cart_id:
        flash('No active cart to abandon.')
        return redirect(url_for('products'))

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE carts
        SET status = 'abandoned'
        WHERE cart_id = %s
    """, (cart_id,))
    conn.commit()
    cur.close()
    conn.close()

    session.pop('cart_id', None)  # Clear cart session
    flash('You abandoned your cart.')
    return redirect(url_for('products'))

@app.route('/product_affinity')
def product_affinity():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        WITH order_pairs AS (
            SELECT oi1.order_id, oi1.product_id as product1_id, oi2.product_id as product2_id
            FROM order_items oi1
            JOIN order_items oi2 ON oi1.order_id = oi2.order_id
            WHERE oi1.product_id < oi2.product_id
        ),
        pair_counts AS (
            SELECT 
                p1.name as product1_name,
                p2.name as product2_name,
                COUNT(DISTINCT op.order_id) as times_bought_together,
                ROUND(COUNT(DISTINCT op.order_id) * 100.0 / (
                    SELECT COUNT(DISTINCT order_id) 
                    FROM order_pairs
                ), 2) as affinity_percentage
            FROM order_pairs op
            JOIN products p1 ON op.product1_id = p1.product_id
            JOIN products p2 ON op.product2_id = p2.product_id
            GROUP BY p1.name, p2.name
        )
        SELECT 
            product1_name,
            product2_name,
            times_bought_together,
            affinity_percentage
        FROM pair_counts
        ORDER BY times_bought_together DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('product_affinity.html', product_pairs=rows)

@app.route('/data-overview')
def data_overview():
    conn = get_connection()
    cur = conn.cursor()
    
    # Get total number of products
    cur.execute("SELECT COUNT(*) FROM products WHERE is_active = TRUE;")
    total_products = cur.fetchone()[0]
    
    # Get total number of orders
    cur.execute("SELECT COUNT(*) FROM orders;")
    total_orders = cur.fetchone()[0]
    
    # Get total revenue
    cur.execute("SELECT COALESCE(SUM(total_amount), 0) FROM orders;")
    total_revenue = cur.fetchone()[0]
    
    # Get average order value
    cur.execute("SELECT COALESCE(AVG(total_amount), 0) FROM orders;")
    avg_order_value = cur.fetchone()[0]
    
    # Get total number of users
    cur.execute("SELECT COUNT(*) FROM users;")
    total_users = cur.fetchone()[0]
    
    # Get total number of reviews
    cur.execute("SELECT COUNT(*) FROM reviews;")
    total_reviews = cur.fetchone()[0]
    
    # Get average rating
    cur.execute("SELECT COALESCE(AVG(rating), 0) FROM reviews;")
    avg_rating = cur.fetchone()[0]
    
    # Get cart abandonment rate
    cur.execute("""
        SELECT 
            COUNT(*) FILTER (WHERE status = 'abandoned')::float / 
            NULLIF(COUNT(*), 0) * 100 as abandonment_rate
        FROM carts;
    """)
    abandonment_rate = cur.fetchone()[0]
    
    # Get recent orders
    cur.execute("""
        SELECT o.order_id, u.name, o.order_date, o.total_amount, o.status
        FROM orders o
        JOIN users u ON o.user_id = u.user_id
        ORDER BY o.order_date DESC
        LIMIT 10;
    """)
    recent_orders = cur.fetchall()
    
    # Get top products by revenue
    cur.execute("""
        SELECT p.name, SUM(oi.quantity * oi.unit_price) as revenue
        FROM order_items oi
        JOIN products p ON oi.product_id = p.product_id
        GROUP BY p.product_id, p.name
        ORDER BY revenue DESC
        LIMIT 10;
    """)
    top_products = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return render_template('data_overview.html',
                         total_products=total_products,
                         total_orders=total_orders,
                         total_revenue=total_revenue,
                         avg_order_value=avg_order_value,
                         total_users=total_users,
                         total_reviews=total_reviews,
                         avg_rating=avg_rating,
                         abandonment_rate=abandonment_rate,
                         recent_orders=recent_orders,
                         top_products=top_products)

@app.route('/database-visualization')
def database_visualization():
    # Connect to both databases
    pg_conn = get_connection()
    mongo_client = MongoClient('mongodb://localhost:27017/')
    mongo_db = mongo_client['ecommerce_mongodb']
    
    try:
        # Get sample data from PostgreSQL
        cur = pg_conn.cursor()
        
        # Users
        cur.execute("SELECT user_id, name, email, signup_source FROM users LIMIT 5")
        pg_users = cur.fetchall()
        
        # Products
        cur.execute("SELECT product_id, name, category, price FROM products LIMIT 5")
        pg_products = cur.fetchall()
        
        # Orders
        cur.execute("""
            SELECT o.order_id, u.name, o.order_date, o.total_amount 
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            LIMIT 5
        """)
        pg_orders = cur.fetchall()
        
        # Get counts
        cur.execute("SELECT COUNT(*) FROM users")
        pg_user_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM products")
        pg_product_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM orders")
        pg_order_count = cur.fetchone()[0]
        
        # Get MongoDB data
        mongo_users = list(mongo_db.users.find({}, {"_id": 1, "name": 1, "email": 1, "signup_source": 1}).limit(5))
        mongo_products = list(mongo_db.products.find({}, {"_id": 1, "name": 1, "category": 1, "price": 1}).limit(5))
        mongo_orders = list(mongo_db.orders.find({}, {"_id": 1, "user_id": 1, "order_date": 1, "total_amount": 1}).limit(5))
        
        # Get MongoDB counts
        mongo_user_count = mongo_db.users.count_documents({})
        mongo_product_count = mongo_db.products.count_documents({})
        mongo_order_count = mongo_db.orders.count_documents({})
        
        # Format MongoDB orders with user names
        mongo_orders_with_users = []
        for order in mongo_orders:
            user = mongo_db.users.find_one({"_id": order["user_id"]})
            mongo_orders_with_users.append({
                "id": order["_id"],
                "user": user["name"] if user else "Unknown",
                "date": order["order_date"],
                "total": order["total_amount"]
            })
        
        return render_template('database_visualization.html',
            pg_users=pg_users,
            pg_products=pg_products,
            pg_orders=pg_orders,
            pg_user_count=pg_user_count,
            pg_product_count=pg_product_count,
            pg_order_count=pg_order_count,
            mongo_users=mongo_users,
            mongo_products=mongo_products,
            mongo_orders=mongo_orders_with_users,
            mongo_user_count=mongo_user_count,
            mongo_product_count=mongo_product_count,
            mongo_order_count=mongo_order_count
        )
        
    finally:
        pg_conn.close()
        mongo_client.close()

@app.route('/database_comparison')
def database_comparison():
    try:
        print("=== Database Comparison Route Hit ===")
        print(f"Request method: {request.method}")
        print(f"Request path: {request.path}")
        print(f"Request headers: {dict(request.headers)}")
        
        pg_error = None
        mongo_error = None
        pg_complex_query = []
        pg_aggregation = None
        mongo_complex_query = []
        mongo_aggregation = None

        # Try PostgreSQL connection first
        try:
            print("Attempting PostgreSQL connection...")
            pg_conn = get_connection()
            pg_cur = pg_conn.cursor()
            
            # Example 1: Complex JOIN query
            print("Executing PostgreSQL complex query...")
            pg_cur.execute("""
                SELECT u.name, COUNT(o.order_id) as order_count, 
                       SUM(o.total_amount) as total_spent,
                       AVG(r.rating) as avg_rating
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                LEFT JOIN reviews r ON u.user_id = r.user_id
                GROUP BY u.name
                ORDER BY total_spent DESC
                LIMIT 5
            """)
            pg_complex_query = pg_cur.fetchall()
            
            # Example 2: Transaction example
            print("Executing PostgreSQL aggregation query...")
            pg_cur.execute("""
                SELECT COUNT(*) as total_products,
                       AVG(price) as avg_price,
                       MIN(price) as min_price,
                       MAX(price) as max_price
                FROM products
            """)
            pg_aggregation = pg_cur.fetchone()
            
            pg_conn.close()
            print("PostgreSQL queries completed successfully")
            
        except Exception as e:
            print(f"PostgreSQL error: {str(e)}")
            pg_error = f"PostgreSQL connection error: {str(e)}"
        
        # Try MongoDB connection
        try:
            print("Attempting MongoDB connection...")
            mongo_client = MongoClient('mongodb://localhost:27017/')
            mongo_db = mongo_client['ecommerce_mongodb']
            
            # Example 1: Complex aggregation
            print("Executing MongoDB complex query...")
            mongo_complex_query = list(mongo_db.users.aggregate([
                {
                    "$lookup": {
                        "from": "orders",
                        "localField": "_id",
                        "foreignField": "user_id",
                        "as": "orders"
                    }
                },
                {
                    "$lookup": {
                        "from": "reviews",
                        "localField": "_id",
                        "foreignField": "user_id",
                        "as": "reviews"
                    }
                },
                {
                    "$project": {
                        "name": 1,
                        "order_count": {"$size": "$orders"},
                        "total_spent": {"$sum": "$orders.total_amount"},
                        "avg_rating": {"$avg": "$reviews.rating"}
                    }
                },
                {"$sort": {"total_spent": -1}},
                {"$limit": 5}
            ]))
            
            # Example 2: Aggregation example
            print("Executing MongoDB aggregation query...")
            mongo_aggregation = list(mongo_db.products.aggregate([
                {
                    "$group": {
                        "_id": None,
                        "total_products": {"$sum": 1},
                        "avg_price": {"$avg": "$price"},
                        "min_price": {"$min": "$price"},
                        "max_price": {"$max": "$price"}
                    }
                }
            ]))[0]
            
            mongo_client.close()
            print("MongoDB queries completed successfully")
            
        except Exception as e:
            print(f"MongoDB error: {str(e)}")
            mongo_error = f"MongoDB connection error: {str(e)}"
        
        print("=== Rendering Template ===")
        # Render template with all data and any errors
        return render_template('database_comparison.html',
                             pg_complex_query=pg_complex_query,
                             pg_aggregation=pg_aggregation,
                             mongo_complex_query=mongo_complex_query,
                             mongo_aggregation=mongo_aggregation,
                             pg_error=pg_error,
                             mongo_error=mongo_error)
        
    except Exception as e:
        print(f"Unexpected error in database_comparison route: {str(e)}")
        return render_template('error.html', error=str(e))

@app.route('/customer-behavior')
def customer_behavior():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        WITH customer_segments AS (
            -- Segment customers based on their spending and order frequency
            SELECT 
                u.user_id,
                u.name,
                COUNT(DISTINCT o.order_id) as total_orders,
                SUM(o.total_amount) as total_spent,
                CASE 
                    WHEN COUNT(DISTINCT o.order_id) >= 5 AND SUM(o.total_amount) >= 1000 THEN 'VIP'
                    WHEN COUNT(DISTINCT o.order_id) >= 3 AND SUM(o.total_amount) >= 500 THEN 'Regular'
                    ELSE 'Casual'
                END as customer_segment,
                -- Calculate average days between orders
                EXTRACT(DAY FROM (MAX(o.order_date) - MIN(o.order_date))) / 
                    NULLIF(COUNT(DISTINCT o.order_id) - 1, 0) as avg_days_between_orders
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
            GROUP BY u.user_id, u.name
        ),
        product_performance AS (
            -- Analyze product performance across different time periods
            SELECT 
                p.product_id,
                p.name,
                p.category,
                COUNT(DISTINCT oi.order_id) as total_orders,
                SUM(oi.quantity) as total_quantity,
                SUM(oi.quantity * oi.unit_price) as total_revenue,
                -- Calculate monthly growth rate
                ROUND(
                    (COUNT(DISTINCT oi.order_id) * 100.0 / 
                    LAG(COUNT(DISTINCT oi.order_id)) OVER (PARTITION BY p.product_id ORDER BY DATE_TRUNC('month', o.order_date)) - 100),
                    2
                ) as monthly_growth_rate
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            GROUP BY p.product_id, p.name, p.category, DATE_TRUNC('month', o.order_date)
        ),
        category_analysis AS (
            -- Analyze category performance and customer preferences
            SELECT 
                p.category,
                COUNT(DISTINCT o.order_id) as total_orders,
                SUM(oi.quantity * oi.unit_price) as total_revenue,
                COUNT(DISTINCT o.user_id) as unique_customers,
                -- Calculate average order value per category
                ROUND(SUM(oi.quantity * oi.unit_price) / COUNT(DISTINCT o.order_id), 2) as avg_order_value
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            GROUP BY p.category
        ),
        repeat_customers AS (
            -- Calculate repeat customers per category
            SELECT 
                p.category,
                COUNT(DISTINCT o.user_id) as repeat_customers
            FROM products p
            JOIN order_items oi ON p.product_id = oi.product_id
            JOIN orders o ON oi.order_id = o.order_id
            GROUP BY p.category, o.user_id
            HAVING COUNT(DISTINCT o.order_id) > 1
        ),
        time_analysis AS (
            -- Analyze purchasing patterns across different times
            SELECT 
                EXTRACT(HOUR FROM o.order_date) as hour_of_day,
                EXTRACT(DOW FROM o.order_date) as day_of_week,
                COUNT(DISTINCT o.order_id) as order_count,
                SUM(o.total_amount) as total_revenue,
                COUNT(DISTINCT o.user_id) as unique_customers
            FROM orders o
            GROUP BY hour_of_day, day_of_week
        )
        SELECT 
            -- Customer Segment Analysis
            (SELECT COUNT(*) FROM customer_segments WHERE customer_segment = 'VIP') as vip_customers,
            (SELECT COUNT(*) FROM customer_segments WHERE customer_segment = 'Regular') as regular_customers,
            (SELECT COUNT(*) FROM customer_segments WHERE customer_segment = 'Casual') as casual_customers,
            -- Product Performance
            (SELECT COUNT(*) FROM product_performance WHERE monthly_growth_rate > 0) as growing_products,
            (SELECT COUNT(*) FROM product_performance WHERE monthly_growth_rate < 0) as declining_products,
            -- Category Analysis
            (SELECT category FROM category_analysis ORDER BY total_revenue DESC LIMIT 1) as top_category,
            (SELECT ROUND(AVG(rc.repeat_customers * 100.0 / ca.unique_customers), 2)
             FROM category_analysis ca
             JOIN repeat_customers rc ON ca.category = rc.category) as avg_category_retention,
            -- Time Analysis
            (SELECT hour_of_day FROM time_analysis ORDER BY order_count DESC LIMIT 1) as peak_hour,
            (SELECT day_of_week FROM time_analysis ORDER BY order_count DESC LIMIT 1) as peak_day
    """)
    results = cur.fetchone()
    cur.close()
    conn.close()
    
    # Format the results into a more readable structure
    analysis = {
        'customer_segments': {
            'vip': results[0],
            'regular': results[1],
            'casual': results[2]
        },
        'product_performance': {
            'growing': results[3],
            'declining': results[4]
        },
        'category_analysis': {
            'top_category': results[5],
            'avg_retention': results[6]
        },
        'time_analysis': {
            'peak_hour': int(results[7]),
            'peak_day': int(results[8])
        }
    }
    
    return render_template('customer_behavior.html', analysis=analysis)

@app.errorhandler(Exception)
def handle_error(error):
    """Global error handler that shows our custom error page"""
    print(f"=== Error occurred: {str(error)} ===")
    return render_template('error.html', error=str(error)), 500

@app.route('/test-error')
def test_error():
    """Test route that intentionally raises an exception to test error handling"""
    print("=== Test Error Route Hit ===")
    raise Exception("This is a test error to verify error page functionality")

# === End of app ===

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='0.0.0.0', port=5001, debug=True)
