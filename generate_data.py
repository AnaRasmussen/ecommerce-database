import uuid
import random
from datetime import datetime, timedelta
from faker import Faker

faker = Faker()

# === Settings ===
NUM_USERS = 50
NUM_PRODUCTS = 30
NUM_ORDERS = 100
NUM_REVIEWS = 70
NUM_CARTS = 50
NUM_SESSIONS = 80

def random_uuid():
    return str(uuid.uuid4())

# === Generate functions ===

def generate_users():
    users = []
    signup_sources = ['organic', 'ad', 'referral']
    for _ in range(NUM_USERS):
        user_id = random_uuid()
        name = faker.name().replace("'", "''")
        email = faker.unique.email()
        source = random.choice(signup_sources)
        users.append((user_id, name, email, source))
    return users

def generate_products():
    products = []
    categories = ['Electronics', 'Apparel', 'Home', 'Beauty', 'Toys']
    for _ in range(NUM_PRODUCTS):
        product_id = random_uuid()
        name = (faker.word().capitalize() + " " + random.choice(["Pro", "Max", "Lite", "XL", "Mini"])).replace("'", "''")
        category = random.choice(categories)
        price = round(random.uniform(10, 1000), 2)
        created_at = faker.date_time_between(start_date='-6M', end_date='now')
        products.append((product_id, name, category, price, created_at))
    return products

def generate_orders(valid_user_ids):
    orders = []
    for _ in range(NUM_ORDERS):
        order_id = random_uuid()
        user_id = random.choice(valid_user_ids)
        order_date = faker.date_time_between(start_date='-3M', end_date='now')
        status = random.choice(['pending', 'completed'])
        total_amount = round(random.uniform(20, 500), 2)
        orders.append((order_id, user_id, order_date, status, total_amount))
    return orders

def generate_order_items(order_list, product_ids):
    items = []
    for order_id, _, _, _, _ in order_list:
        for _ in range(random.randint(1, 5)):
            order_item_id = random_uuid()
            product_id = random.choice(product_ids)
            quantity = random.randint(1, 3)
            unit_price = round(random.uniform(10, 500), 2)
            items.append((order_item_id, order_id, product_id, quantity, unit_price))
    return items

def generate_reviews(valid_user_ids, product_ids):
    reviews = []
    for _ in range(NUM_REVIEWS):
        review_id = random_uuid()
        user_id = random.choice(valid_user_ids)
        product_id = random.choice(product_ids)
        rating = random.randint(1, 5)
        comment = faker.sentence().replace("'", "''")
        review_date = faker.date_time_between(start_date='-6M', end_date='now')
        reviews.append((review_id, user_id, product_id, rating, comment, review_date))
    return reviews

def generate_carts(valid_user_ids):
    carts = []
    statuses = ['active', 'abandoned', 'converted']
    for _ in range(NUM_CARTS):
        cart_id = random_uuid()
        user_id = random.choice(valid_user_ids)
        created_at = faker.date_time_between(start_date='-3M', end_date='now')
        status = random.choice(statuses)
        carts.append((cart_id, user_id, created_at, status))
    return carts

def generate_cart_items(cart_list, product_ids):
    cart_items = []
    for cart_id, _, cart_created_at, _ in cart_list:
        for _ in range(random.randint(1, 4)):
            cart_item_id = random_uuid()
            product_id = random.choice(product_ids)
            added_at = faker.date_time_between(start_date=cart_created_at, end_date='now')
            removed_at = faker.date_time_between(start_date=added_at, end_date='now') if random.random() < 0.5 else None
            cart_items.append((cart_item_id, cart_id, product_id, added_at, removed_at))
    return cart_items

def generate_sessions(valid_user_ids):
    sessions = []
    traffic_sources = ['Google Ads', 'Organic', 'Email Campaign', 'Direct']
    for _ in range(NUM_SESSIONS):
        session_id = random_uuid()
        user_id = random.choice(valid_user_ids) if random.random() < 0.8 else None
        source = random.choice(traffic_sources)
        session_start = faker.date_time_between(start_date='-2M', end_date='now')
        session_end = session_start + timedelta(minutes=random.randint(5, 120))
        made_purchase = True if random.random() < 0.4 else False
        sessions.append((session_id, user_id, source, session_start, session_end, made_purchase))
    return sessions

# === Main generation ===

def main():
    print("🚀 Generating dummy data...")
    
    # === Generate users and products first ===
    user_list = generate_users()
    product_list = generate_products()

    # === Extract user_ids and product_ids ===
    user_ids = [u[0] for u in user_list]
    product_ids = [p[0] for p in product_list]

    # === Now generate things using valid IDs ===
    order_list = generate_orders(user_ids)
    order_items_list = generate_order_items(order_list, product_ids)
    review_list = generate_reviews(user_ids, product_ids)
    cart_list = generate_carts(user_ids)
    cart_items_list = generate_cart_items(cart_list, product_ids)
    session_list = generate_sessions(user_ids)

    # === Write to dummy_data.sql ===
    with open('database/dummy_data.sql', 'w') as f:
        # Users
        f.write("-- Users\n")
        f.write("INSERT INTO users (user_id, name, email, signup_source) VALUES\n")
        f.write(",\n".join(f"('{u[0]}', '{u[1]}', '{u[2]}', '{u[3]}')" for u in user_list) + ";\n\n")

        # Products
        f.write("-- Products\n")
        f.write("INSERT INTO products (product_id, name, category, price, created_at, is_active) VALUES\n")
        f.write(",\n".join(f"('{p[0]}', '{p[1]}', '{p[2]}', {p[3]}, '{p[4]}', TRUE)" for p in product_list) + ";\n\n")

        # Orders
        f.write("-- Orders\n")
        f.write("INSERT INTO orders (order_id, user_id, order_date, status, total_amount) VALUES\n")
        f.write(",\n".join(f"('{o[0]}', '{o[1]}', '{o[2]}', '{o[3]}', {o[4]})" for o in order_list) + ";\n\n")

        # Order Items
        f.write("-- Order Items\n")
        f.write("INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price) VALUES\n")
        f.write(",\n".join(f"('{oi[0]}', '{oi[1]}', '{oi[2]}', {oi[3]}, {oi[4]})" for oi in order_items_list) + ";\n\n")

        # Reviews
        f.write("-- Reviews\n")
        f.write("INSERT INTO reviews (review_id, user_id, product_id, rating, comment, review_date) VALUES\n")
        f.write(",\n".join(f"('{r[0]}', '{r[1]}', '{r[2]}', {r[3]}, '{r[4]}', '{r[5]}')" for r in review_list) + ";\n\n")

        # Carts
        f.write("-- Carts\n")
        f.write("INSERT INTO carts (cart_id, user_id, created_at, status) VALUES\n")
        f.write(",\n".join(f"('{c[0]}', '{c[1]}', '{c[2]}', '{c[3]}')" for c in cart_list) + ";\n\n")

        # Cart Items
        f.write("-- Cart Items\n")
        f.write("INSERT INTO cart_items (cart_item_id, cart_id, product_id, added_at, removed_at) VALUES\n")
        f.write(",\n".join(
            f"('{ci[0]}', '{ci[1]}', '{ci[2]}', '{ci[3]}', " + (f"'{ci[4]}'" if ci[4] else "NULL") + ")"
            for ci in cart_items_list
        ) + ";\n\n")


        # Sessions
        f.write("-- Sessions\n")
        f.write("INSERT INTO sessions (session_id, user_id, traffic_source, session_start, session_end, made_purchase) VALUES\n")
        f.write(",\n".join(
            f"('{s[0]}', " + (f"'{s[1]}'" if s[1] else "NULL") + f", '{s[2]}', '{s[3]}', '{s[4]}', {str(s[5]).upper()})"
            for s in session_list
        ) + ";\n\n")


    print("✅ Dummy data written to 'database/dummy_data.sql' successfully!")

if __name__ == "__main__":
    main()
