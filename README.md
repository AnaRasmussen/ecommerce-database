# E-commerce Database & Dashboard

A full-stack simulation of an e-commerce backend and frontend system, with real-time analytics dashboards.

Built using **PostgreSQL**, **Flask**, **Tailwind CSS**, and **Chart.js**.

---

## Features

- Product Catalog: View and rate products
- Shopping Cart: Add to cart, checkout, abandon cart
- Analytics Dashboards:
  - Top Rated Products (live average ratings)
  - Top Selling Products (this quarter)
  - Repeat Customers (month-over-month)
  - Most Abandoned Products (based on cart activity)
- Live Data: All charts and tables are based on real SQL queries and live user actions
- Responsive Frontend: Built with Tailwind CSS

---

## Tech Stack

| Layer     | Technology            |
|-----------|------------------------|
| Backend   | Flask (Python 3.8+)     |
| Database  | PostgreSQL (14+)        |
| Frontend  | Tailwind CSS, Chart.js  |
| ORM       | psycopg2 (manual SQL)   |
| Data Gen  | Faker (dummy data)      |

---

## Project Structure

```
ecommerce-db/
├── app/                # Flask app
│   ├── static/         # Tailwind CSS
│   ├── templates/      # Jinja2 templates (HTML)
│   └── app.py          # Flask backend
├── database/
│   ├── schema.sql      # Database schema
│   ├── dummy_data.sql  # Generated dummy data
│   └── queries.sql     # Example SQL queries
├── generate_data.py    # Faker script to generate dummy data
├── db_init.py          # Initializes database with schema + data
├── requirements.txt    # Python package requirements
└── README.md           # Project documentation
```

---

## Setup Instructions

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

---

### 2. Start PostgreSQL

Make sure PostgreSQL is running locally:

```bash
brew services start postgresql
```
or manually start your PostgreSQL service if you are on Linux/Windows.

---

### 3. Important: Update Database User

Open `app/app.py` and modify these values to match your local PostgreSQL setup:

```python
DB_NAME = "postgres"
DB_USER = "your_postgres_username"
DB_PASSWORD = "your_postgres_password"
DB_HOST = "localhost"
DB_PORT = "5432"
```

**Example** (original):

```python
DB_USER = "analiese_rasmussen"
DB_PASSWORD = ""
```

Change `DB_USER` to match your actual PostgreSQL username.

---

How to find your PostgreSQL username:
You can check by running this command in your terminal:

```bash
psql -U postgres
```

Otherwise, if you're on Mac/Linux, it’s often the same as your computer username.
You can also list all available Postgres roles (usernames) by running:

```bash
psql -c "\du"
```

### 4. Initialize the Database

First, create the database manually if needed:

```bash
createdb postgres
```

Then run:

```bash
python3 generate_data.py
python3 db_init.py
```

This will:
- Create all tables (`schema.sql`)
- Populate them with fake data (`dummy_data.sql`)

---

### 5. Run the Flask App

```bash
cd app
python3 app.py
```

Then open your browser and visit:

```
http://127.0.0.1:5000/
```

Now you can browse products, rate products, add to cart, abandon carts, and view live dashboards.

---

## Main Pages

| Route              | Page                    | Description                                  |
|--------------------|--------------------------|----------------------------------------------|
| `/`                | Home                     | Welcome page                                |
| `/products`        | Products                 | Browse and rate products, add to cart        |
| `/cart`            | Cart                     | View your cart, checkout, or abandon cart    |
| `/top-rated`       | Top Rated Products       | Live average ratings chart                  |
| `/top-selling`     | Top Selling Products     | Top sales this quarter                      |
| `/repeat-customers`| Repeat Customers         | Monthly repeat customer statistics          |
| `/abandoned`       | Most Abandoned Products  | Products abandoned most often in carts      |

---

## Notes

- Abandoned products are tracked based on products left behind in carts that were abandoned.
- Top Rated page updates live after rating products.
- All analytics dashboards are powered by real database queries.

---

## Credits

This project was built as a complete educational simulation of an e-commerce backend and frontend system, focusing on real-time data-driven dashboards.

---

## Future Improvements

- Add real user authentication (login/logout)
- Allow multiple quantities per cart item
- Allow users to leave written comments with ratings
- Add Admin dashboard for product and order management

---

## License

Free to use for educational and demonstration purposes.

