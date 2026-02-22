# Vikmo — Docker Quick Start Guide

Get the entire Vikmo platform running in 5 minutes with Docker. No Python, no Node.js, no PostgreSQL installation needed.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- Git

---

## Step 1 — Clone the repository

```bash
git clone https://github.com/YOURUSERNAME/vikmo-project.git
cd vikmo-project
```

---

## Step 2 — Start everything

```bash
docker-compose up --build
```

This single command will:
- Pull and start PostgreSQL 15
- Build and start the Django backend (runs migrations automatically)
- Build and start the React frontend

Wait until you see:
```
vikmo_backend | Starting Django server...
vikmo_backend | Django version 6.0.2
vikmo_frontend | VITE ready in xxx ms
```

---

## Step 3 — Create admin account

Open a **new terminal** (keep docker-compose running) and run:

```bash
docker exec -it vikmo_backend python manage.py createsuperuser
```

Enter your desired username, email, and password.

---

## Step 4 — Open the app

| What | URL |
|------|-----|
| 🖥️ React Frontend | http://localhost:5173 |
| 🔌 Django API | http://localhost:8000/api/ |
| 📖 API Docs (Swagger) | http://localhost:8000/api/docs/ |
| ⚙️ Django Admin | http://localhost:8000/admin/ |

Login at `http://localhost:5173` with the superuser credentials you just created.

---

## Step 5 — Set up sample data

Once logged in as admin, follow this order:

### 1. Add Products
Go to **Products → New Product**
```
SKU: BP-001
Name: Brake Pad
Price: 500
```

### 2. Add Stock
Go to **Inventory → Adjust Stock**
```
New Quantity: 100
Reason: Initial stock load
```

### 3. Create a Dealer
Go to **Dealers → New Dealer**
```
Username: dealer1
Password: dealer123
Name: ABC Motors
...fill other fields
```

### 4. Place an Order
Sign out → Login as `dealer1` → Go to **My Orders → New Order**
- Select Brake Pad, quantity 10
- Create Draft Order
- Click **Confirm** → stock deducts automatically
- Click **Deliver** → order complete

### 5. Check Dashboard
Login as admin → **Dashboard** shows revenue, top products, low stock alerts.

---

## Stopping the app

```bash
# Stop containers (keeps data)
docker-compose down

# Stop and DELETE all data (fresh start)
docker-compose down -v
```

---

## Restarting later

```bash
# No need to rebuild — just run:
docker-compose up

# Only rebuild if you changed code:
docker-compose up --build
```

---

## Troubleshooting

**Port already in use:**
```bash
# Change ports in docker-compose.yml
# e.g. "8001:8000" for backend, "5174:5173" for frontend
```

**Backend not connecting to DB:**
```bash
# Restart just the backend
docker-compose restart backend
```

**See logs for a specific service:**
```bash
docker logs vikmo_backend
docker logs vikmo_frontend
docker logs vikmo_db
```

**Run Django management commands:**
```bash
docker exec -it vikmo_backend python manage.py <command>
```