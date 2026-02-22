# Vikmo — Sales Order & Inventory Management System

A B2B SaaS backend for auto parts distribution built with Django REST Framework and PostgreSQL.

---

## Tech Stack

- **Language:** Python 3.10+
- **Framework:** Django 4.2 + Django REST Framework
- **Database:** PostgreSQL
- **Auth:** Django built-in (Session + Basic Auth)
- **API Docs:** drf-spectacular (Swagger UI)
- **Frontend:** React.js (separate folder)

---

## Features Implemented

- Full product catalog management with SKU search
- Automatic inventory record creation on product creation (Django signals)
- Inventory audit trail — every stock change is logged with who did it
- Dealer account management (admin creates dealer + user in one request)
- Complete order lifecycle: Draft → Confirmed → Delivered
- Stock validation on order confirmation — checks ALL items, rejects entire order if any fail
- Atomic stock deduction — all or nothing, prevents race conditions
- Price locking — unit price captured at order creation, never changes
- Role-based access — Admin vs Dealer permissions on every endpoint
- Order summary report with revenue, top products, low stock alerts
- 17 unit tests covering all critical business logic
- Swagger API docs at `/api/docs/`

---

## Project Structure

```
vikmo_project/
├── manage.py
├── requirements.txt
├── .env.example
├── vikmo_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── inventory/
│   ├── models.py         # 5 models: Product, Inventory, InventoryLog, Dealer, Order, OrderItem
│   ├── serializers.py    # DRF serializers with validation
│   ├── views.py          # API views with business logic
│   ├── urls.py           # API routes
│   ├── admin.py          # Django admin configuration
│   ├── signals.py        # Auto-creates inventory on product creation
│   └── tests.py          # 17 unit tests
└── frontend/             # React.js frontend
```

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd vikmo_project
```

### 2. Create and activate virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
```
Edit `.env` with your PostgreSQL credentials:
```
DEBUG=True
SECRET_KEY=your-secret-key
DB_NAME=vikmo_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### 5. Create PostgreSQL database
```bash
psql -U postgres -c "CREATE DATABASE vikmo_db;"
```

### 6. Run migrations
```bash
python manage.py migrate
```

### 7. Create admin user
```bash
python manage.py createsuperuser
```

### 8. Run the server
```bash
python manage.py runserver
```

- API Base: `http://localhost:8000/api/`
- Swagger Docs: `http://localhost:8000/api/docs/`
- Django Admin: `http://localhost:8000/admin/`

### 9. Run tests
```bash
python manage.py test inventory
```

---

## Database Schema

```
User (Django built-in)
├── is_staff=True  → Admin
└── is_staff=False → linked to Dealer profile

Product
├── id, sku (unique), name, description, price, is_active
└── OneToOne → Inventory (auto-created via signal)

Inventory
├── product (OneToOne), quantity, last_updated_by
└── ForeignKey → InventoryLog (audit trail)

InventoryLog
└── action, quantity_before, quantity_after, quantity_changed, reason, updated_by

Dealer
├── user (OneToOne), dealer_code (auto: DLR-0001), name
└── phone, address, city, state, pincode

Order
├── order_number (auto: ORD-YYYYMMDD-XXXX), dealer (FK)
├── status (draft → confirmed → delivered)
├── total_amount (auto-calculated), confirmed_at, delivered_at
└── OneToMany → OrderItem

OrderItem
└── order (FK), product (FK), quantity, unit_price (locked), line_total (auto)
```

---

## API Documentation

### Authentication
All endpoints require authentication via Basic Auth or Session Auth.
- **Admin:** `is_staff=True` — full access
- **Dealer:** `is_staff=False` — limited access (own orders only)

---

### Products

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/products/` | Any | List all products with stock |
| POST | `/api/products/` | Admin | Create product |
| GET | `/api/products/{id}/` | Any | Product detail |
| PUT | `/api/products/{id}/` | Admin | Update product |
| DELETE | `/api/products/{id}/` | Admin | Delete product |

**Create Product:**
```json
POST /api/products/
{
    "sku": "BP-001",
    "name": "Brake Pad",
    "description": "High quality brake pad",
    "price": "500.00",
    "is_active": true
}
```

**Response:**
```json
{
    "id": 1,
    "sku": "BP-001",
    "name": "Brake Pad",
    "price": "500.00",
    "current_stock": 0,
    "created_at": "2026-02-21T10:00:00Z"
}
```

---

### Inventory (Admin Only)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/inventory/` | Admin | List all inventory levels |
| GET | `/api/inventory/{product_id}/` | Admin | Single product inventory + audit log |
| PUT | `/api/inventory/{product_id}/adjust/` | Admin | Manual stock adjustment |

**Adjust Stock:**
```json
PUT /api/inventory/1/adjust/
{
    "quantity": 100,
    "reason": "Initial stock load"
}
```

**Response:**
```json
{
    "message": "Stock updated successfully for Brake Pad",
    "product": "Brake Pad",
    "previous_quantity": 0,
    "new_quantity": 100
}
```

---

### Dealers (Admin Only)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/dealers/` | Admin | List all dealers |
| POST | `/api/dealers/` | Admin | Create dealer + user account |
| GET | `/api/dealers/{id}/` | Admin | Dealer detail |
| PUT | `/api/dealers/{id}/` | Admin | Update dealer |

**Create Dealer:**
```json
POST /api/dealers/
{
    "username": "abcmotors",
    "email": "abc@motors.com",
    "password": "dealer123",
    "name": "ABC Motors",
    "phone": "9876543210",
    "address": "123 Main Street",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400001"
}
```

**Response:**
```json
{
    "id": 1,
    "dealer_code": "DLR-0001",
    "name": "ABC Motors",
    "username": "abcmotors",
    "email": "abc@motors.com"
}
```

---

### Orders

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/orders/` | Any | List orders (dealer: own only, admin: all) |
| POST | `/api/orders/` | Any | Create draft order |
| GET | `/api/orders/{id}/` | Any | Order detail with items |
| PUT | `/api/orders/{id}/` | Any | Update draft order only |
| POST | `/api/orders/{id}/confirm/` | Any | Confirm order (validates + deducts stock) |
| POST | `/api/orders/{id}/deliver/` | Any | Mark as delivered |
| GET | `/api/orders/summary/` | Admin | Business summary report |

**Create Order (Dealer):**
```json
POST /api/orders/
{
    "notes": "Urgent delivery",
    "items": [
        {"product": 1, "quantity": 10},
        {"product": 2, "quantity": 5}
    ]
}
```

**Create Order (Admin — must provide dealer_id):**
```json
POST /api/orders/
{
    "dealer_id": 1,
    "items": [{"product": 1, "quantity": 10}]
}
```

**Confirm Order — Success:**
```json
{
    "message": "Order ORD-20260221-0001 confirmed successfully. Stock has been deducted.",
    "order": { "status": "confirmed", ... }
}
```

**Confirm Order — Insufficient Stock:**
```json
{
    "error": "Order confirmation failed due to insufficient stock.",
    "stock_errors": [
        {
            "product": "Brake Pad",
            "sku": "BP-001",
            "requested": 200,
            "available": 90,
            "error": "Insufficient stock for Brake Pad. Available: 90, Requested: 200"
        }
    ]
}
```

**Order Summary (Admin):**
```json
GET /api/orders/summary/
{
    "total_orders": 10,
    "orders_by_status": {"draft": 2, "confirmed": 5, "delivered": 3},
    "total_confirmed_revenue": 125000.00,
    "top_5_products_by_quantity": [...],
    "low_stock_alert": [...]
}
```

---

## Frontend Setup (React)

### Run locally
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: `http://localhost:5173`

### Features
- Login page (admin and dealer roles)
- Admin Dashboard with revenue, top products, low stock alerts
- Dealer Dashboard with personal order stats
- Products page — browse, search, create (admin), delete (admin)
- Inventory page — stock levels, manual adjustment with audit log (admin only)
- Dealers page — create and manage dealer accounts (admin only)
- Orders page — create draft, confirm (deducts stock), deliver, filter by status
- Role-based sidebar — dealers see only their relevant pages
- Click any order row to expand and see line items

---

## Running with Docker (Full Stack)

Run the entire stack — PostgreSQL + Django + React — with one command:

```bash
docker-compose up --build
```

| Service | URL |
|---------|-----|
| React Frontend | http://localhost:5173 |
| Django API | http://localhost:8000/api/ |
| Swagger Docs | http://localhost:8000/api/docs/ |
| Django Admin | http://localhost:8000/admin/ |

To stop:
```bash
docker-compose down
```

To reset database:
```bash
docker-compose down -v
docker-compose up --build
```

---


1. **Stock validation** — ALL items checked before confirming, entire order rejected if any fail
2. **Atomic transactions** — stock deducted all-or-nothing, no partial deductions possible
3. **Status flow** — Draft → Confirmed → Delivered only, invalid transitions rejected
4. **Order locking** — confirmed/delivered orders cannot be edited
5. **Price locking** — unit_price captured at order time, never changes with product price updates
6. **Auto calculations** — line_total = qty × price, order total = sum of line totals
7. **Audit trail** — every inventory change logged with user, timestamp, before/after quantities

---

## Assumptions Made

- Admin creates all dealer accounts (dealers cannot self-register)
- A product can only appear once per order (use quantity to order more)
- Stock cannot go below 0 (enforced at DB and API level)
- Deleting a dealer or product that has orders is blocked (PROTECT constraint)
- Inventory record is always auto-created with 0 stock when product is created

Images : Delaer dashboard
  <img width="732" height="722" alt="image" src="https://github.com/user-attachments/assets/309a7924-ee16-4d9c-af56-55bb1988e086" />

  <img width="1867" height="815" alt="image" src="https://github.com/user-attachments/assets/1d9276fc-5bb9-43de-97a7-e785a139942a" />
  <img width="1904" height="598" alt="image" src="https://github.com/user-attachments/assets/5a4d0c1e-5037-41b0-9b92-34e8f6a8f156" />
  <img width="1903" height="817" alt="image" src="https://github.com/user-attachments/assets/8e741ecf-56f0-4f2e-9672-e4c007766ab6" />
  <img width="1903" height="604" alt="image" src="https://github.com/user-attachments/assets/4d8043b3-95e6-4df9-8ab1-2f0f4474a34b" />
Images : Admin dashboard
<img width="1903" height="817" alt="image" src="https://github.com/user-attachments/assets/20003e80-d904-4154-aec3-91c23e66fdd2" />
<img width="1913" height="567" alt="image" src="https://github.com/user-attachments/assets/42ca11c7-6032-4eb8-bd80-9fedfc8dc08f" />
<img width="1918" height="566" alt="image" src="https://github.com/user-attachments/assets/6db44410-0e63-47d0-9711-6c273a5a372b" />
<img width="1910" height="552" alt="image" src="https://github.com/user-attachments/assets/ee34207c-5fd8-4a93-b17a-6b9c286e5de4" />
<img width="1550" height="390" alt="image" src="https://github.com/user-attachments/assets/998dcc3c-d3c3-41f1-a247-d17a01e2fa46" />
<img width="1567" height="771" alt="image" src="https://github.com/user-attachments/assets/d4ad1342-cc3e-4ccf-9795-c9bce4bad656" />
<img width="1480" height="703" alt="image" src="https://github.com/user-attachments/assets/5ce99311-77fd-4724-9d77-b48fef2b57d6" />

