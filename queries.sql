-- Highest Rated Products
SELECT 
    p.product_id,
    p.name,
    AVG(r.rating) AS avg_rating,
    COUNT(r.review_id) AS review_count
FROM products p
JOIN reviews r ON p.product_id = r.product_id
WHERE p.is_active = TRUE
GROUP BY p.product_id, p.name
ORDER BY avg_rating DESC
LIMIT 10;


-- Top Selling Products This Quarter
SELECT 
    p.product_id,
    p.name,
    SUM(oi.quantity) AS total_units_sold
FROM order_items oi
JOIN orders o ON oi.order_id = o.order_id
JOIN products p ON oi.product_id = p.product_id
WHERE DATE_TRUNC('quarter', o.order_date) = DATE_TRUNC('quarter', CURRENT_DATE)
GROUP BY p.product_id, p.name
ORDER BY total_units_sold DESC
LIMIT 10;


-- Repeat Customers Month over Month
WITH monthly_orders AS (
    SELECT
        user_id,
        DATE_TRUNC('month', order_date) AS month,
        COUNT(DISTINCT order_id) AS orders_count
    FROM orders
    GROUP BY user_id, month
)

SELECT
    month,
    COUNT(user_id) AS repeat_customers
FROM monthly_orders
WHERE orders_count > 1
GROUP BY month
ORDER BY month;


-- Average Time from Cart Addition to Purchase
WITH cart_purchase_times AS (
    SELECT
        ci.cart_item_id,
        EXTRACT(EPOCH FROM (o.order_date - ci.added_at)) AS seconds_to_purchase
    FROM cart_items ci
    JOIN carts c ON ci.cart_id = c.cart_id
    JOIN orders o ON c.user_id = o.user_id
    WHERE c.status = 'converted'
)

SELECT 
    AVG(seconds_to_purchase) / 60 AS avg_minutes_to_purchase
FROM cart_purchase_times;


-- Most Abandoned Product by Cart
SELECT 
    p.product_id,
    p.name,
    COUNT(DISTINCT ci.cart_id) AS abandoned_carts_count
FROM cart_items ci
JOIN carts c ON ci.cart_id = c.cart_id
JOIN products p ON ci.product_id = p.product_id
WHERE c.status = 'abandoned'
GROUP BY p.product_id, p.name
ORDER BY abandoned_carts_count DESC
LIMIT 1;
