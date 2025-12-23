# Rajbari Ride

A ride-sharing web application built with Django, Channels (WebSockets), and Leaflet/OSM.

## Project Structure

The project has been reorganized for clarity and deployment readiness:

```text
Rajbari Ride/
├── backend/                  # CORE DJANGO PROJECT
│   ├── manage.py             # Entry point
│   ├── rajbari_ride/         # Settings & Config
│   ├── users/                # App: User profiles & auth
│   ├── drivers/              # App: Driver logic
│   ├── rides/                # App: Ride management
│   ├── payments/             # App: Wallet & Payment logic
│   ├── tracking/             # App: WebSocket/Live Tracking
│   ├── vehicles/             # App: Vehicle types
│   └── utils/                # UTILITY SCRIPTS
│       ├── check_users.py    # Verify user data
│       └── ...               # Maintenance scripts
├── requirements.txt          # Python dependencies
├── Procfile                  # Deployment configuration (Railway)
└── README.md
```

## How to Run Locally

1.  **Activate Virtual Environment** (if not active):
    ```bash
    # Windows
    venv\Scripts\activate
    ```

2.  **Navigate to Backend**:
    ```bash
    cd backend
    ```

3.  **Run Server**:
    ```bash
    python manage.py runserver
    ```

## Utility Scripts

To run maintenance scripts (e.g., checking users), navigate to `backend/utils` or run from root:

```bash
# From Project Root
python backend/utils/check_users.py
```
