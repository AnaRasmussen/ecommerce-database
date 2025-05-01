# E-commerce Database & Dashboard

A full-stack simulation of an e-commerce backend and frontend system, with real-time analytics dashboards.

Built using **PostgreSQL**, **MongoDB**, **Flask**, **Tailwind CSS**, and **Chart.js**.

---

## Features

- Product Catalog: View and rate products
- Shopping Cart: Add to cart, checkout, abandon cart
- Analytics Dashboards:
  - Top Rated Products (live average ratings)
  - Top Selling Products (this quarter)
  - Repeat Customers (month-over-month)
  - Most Abandoned Products (based on cart activity)
  - Product Affinity Analysis (frequently bought together)
  - Customer Behavior Analysis (segments, patterns, trends)
  - Database Comparison (PostgreSQL vs MongoDB)
- Live Data: All charts and tables are based on real SQL queries and live user actions
- Responsive Frontend: Built with Tailwind CSS

---

## Tech Stack

| Layer     | Technology            |
|-----------|------------------------|
| Backend   | Flask (Python 3.8+)     |
| Databases | PostgreSQL (14+), MongoDB (8.0+) |
| Frontend  | Tailwind CSS, Chart.js  |
| ORM       | psycopg2, pymongo       |
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
│   ├── schema.sql      # PostgreSQL schema
│   ├── dummy_data.sql  # Generated dummy data
│   └── queries.sql     # Example SQL queries
├── migrate_to_mongodb.py  # MongoDB migration script
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

### 2. Start PostgreSQL and MongoDB

Make sure both databases are running locally:

For PostgreSQL:
```bash
brew services start postgresql
```

For MongoDB:
```bash
brew services start mongodb-community
```

or manually start your services if you are on Linux/Windows.

---

### 3. Configure Database Connections

Open `app/app.py` and modify these values to match your local setup:

```python
# PostgreSQL Configuration
DB_NAME = "postgres"
DB_USER = "your_postgres_username"
DB_PASSWORD = "your_postgres_password"
DB_HOST = "localhost"
DB_PORT = "5432"

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
```

---

### 4. Initialize Databases

1. Initialize PostgreSQL:
```bash
python db_init.py
```

2. Generate dummy data:
```bash
python generate_data.py
```

3. Migrate data to MongoDB:
```bash
python migrate_to_mongodb.py
```

---

## Features in Detail

### Customer Behavior Analysis
- Customer segmentation (VIP, Regular, Casual)
- Product performance tracking
- Category analysis and retention rates
- Peak shopping time analysis

### Product Affinity
- Identifies frequently bought together products
- Calculates affinity percentages
- Visualizes product relationships

### Database Comparison
- Side-by-side comparison of PostgreSQL and MongoDB
- Query performance analysis
- Data structure visualization
- Use case recommendations

---

## Development

### Running the Application

```bash
python app/app.py
```

The application will be available at `http://localhost:5000`

### Generating New Data

To generate new dummy data:
```bash
python generate_data.py
```

### Migrating Data

To migrate data from PostgreSQL to MongoDB:
```bash
python migrate_to_mongodb.py
```

---

![Screenshot](dashboard.png)


