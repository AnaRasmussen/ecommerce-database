DROP TABLE IF EXISTS sessions CASCADE;
DROP TABLE IF EXISTS cart_items CASCADE;
DROP TABLE IF EXISTS carts CASCADE;
DROP TABLE IF EXISTS reviews CASCADE;
DROP TABLE IF EXISTS order_items CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS products CASCADE;
DROP TABLE IF EXISTS users CASCADE;


-- 1. Users
CREATE TABLE users (
    user_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    signup_source TEXT
);

-- 2. Products
CREATE TABLE products (
    product_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- 3. Orders
CREATE TABLE orders (
    order_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    total_amount DECIMAL(10,2)
);

-- 4. Order Items
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY,
    order_id UUID REFERENCES orders(order_id),
    product_id UUID REFERENCES products(product_id),
    quantity INT NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL
);

-- 5. Reviews
CREATE TABLE reviews (
    review_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    product_id UUID REFERENCES products(product_id),
    rating INT CHECK (rating BETWEEN 1 AND 5),
    comment TEXT,
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Carts
CREATE TABLE carts (
    cart_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT
);

-- 7. Cart Items
CREATE TABLE cart_items (
    cart_item_id UUID PRIMARY KEY,
    cart_id UUID REFERENCES carts(cart_id),
    product_id UUID REFERENCES products(product_id),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    removed_at TIMESTAMP
);

-- 8. Sessions
CREATE TABLE sessions (
    session_id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(user_id),
    traffic_source TEXT,
    session_start TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_end TIMESTAMP,
    made_purchase BOOLEAN DEFAULT FALSE
);
