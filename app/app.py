from flask import Flask, render_template, redirect, url_for, request, flash, session
from datetime import datetime
import uuid
import psycopg2

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Needed for flash messages and sessions

# === Database connection settings ===
DB_NAME = "postgres"
DB_USER = "analiese_rasmussen"
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
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT product_id, name, price, category
        FROM products
        WHERE is_active = TRUE
        ORDER BY created_at DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('products.html', products=rows)

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
        SELECT p.name, SUM(oi.quantity) as total_sold
        FROM order_items oi
        JOIN orders o ON oi.order_id = o.order_id
        JOIN products p ON oi.product_id = p.product_id
        WHERE DATE_TRUNC('quarter', o.order_date) = DATE_TRUNC('quarter', CURRENT_DATE)
        GROUP BY p.product_id
        ORDER BY total_sold DESC
        LIMIT 10;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('top_selling.html', products=rows)

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
        SELECT p.name, COUNT(DISTINCT ci.cart_id) as abandoned_count
        FROM cart_items ci
        JOIN carts c ON ci.cart_id = c.cart_id
        JOIN products p ON ci.product_id = p.product_id
        WHERE c.status = 'abandoned'
        GROUP BY p.product_id
        ORDER BY abandoned_count DESC
        LIMIT 5;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return render_template('abandoned.html', products=rows)

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


# === End of app ===

if __name__ == "__main__":
    app.run(debug=True)
