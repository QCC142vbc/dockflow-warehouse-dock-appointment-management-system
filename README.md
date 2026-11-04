# Dock Appointment Scheduling

A warehouse dock appointment management system built with FastAPI (backend) and React (frontend). This system allows carriers to schedule dock appointments and warehouse managers to manage them efficiently.

## User-entered operational data

The application starts without seeded warehouses, docks, carriers, or appointments. Administrators create warehouse records, and authorized warehouse staff create and manage docks and appointments through the application. Appointment forms require users to enter arrival and departure times and select any dock assignment themselves; availability checks only list eligible docks. Dashboard metrics reflect registered records and remain unavailable when there is insufficient data. Warehouse, dock, and appointment deletions are handled as deactivation or cancellation so linked operational and audit history is retained.

## Prerequisites

- Python 3.14+
- Node.js 22+
- PostgreSQL 16+ (optional, for production; SQLite for development)

## Project Structure

```
DockAppointmentScheduling/
├── backend/              # FastAPI backend
│   ├── app/
│   │   ├── api/         # API endpoints
│   │   ├── core/        # Core configuration and security
│   │   ├── engines/     # Custom engines
│   │   ├── integrations/# External integrations
│   │   ├── models/      # SQLAlchemy models
│   │   ├── repositories/# Data access layer
│   │   ├── schemas/     # Pydantic schemas
│   │   └── services/    # Business logic
│   ├── migrations/      # Alembic database migrations
│   ├── scripts/         # Administrator setup utilities
│   ├── requirements.txt
│   └── .env.example
├── frontend/            # React frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

## Backend Setup

### 1. Navigate to the backend directory

```bash
cd backend
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the virtual environment

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Configure environment variables

Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` and set the following variables:

```env
APP_NAME=Dock Appointment Scheduling
APP_VERSION=0.1.0
DEBUG=True
DATABASE_URL=sqlite:///./dock_appointments.db
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30
CORS_ORIGINS=http://localhost:5173
JWT_ISSUER=dock-appointment-scheduling
JWT_AUDIENCE=dock-appointment-api
```

**Generate a secure SECRET_KEY:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 6. Run database migrations (if using PostgreSQL)

```bash
alembic upgrade head
```

### 7. Start the backend server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 8. Access API documentation

Open your browser and navigate to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Frontend Setup

### 1. Navigate to the frontend directory

```bash
cd frontend
```

### 2. Install dependencies

```bash
npm install
```

### 3. Start the development server

```bash
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 4. Build for production

```bash
npm run build
```

## Running the Application

### Development Mode

Run both backend and frontend in separate terminals:

**Terminal 1 (Backend):**
```bash
cd backend
.venv\Scripts\activate  # or source .venv/bin/activate on Linux/Mac
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 (Frontend):**
```bash
cd frontend
npm run dev
```

### Docker Compose (Production)

Create `backend/.env` from `backend/.env.example`, configure a strong `SECRET_KEY`, and set `SERVICE_AUTH_SECRET` to the same random value used by the DockFlow Operations backend. Start the application services:

```bash
docker-compose up --build
```

To also run the outbox dispatcher, configure `OPERATIONS_API_URL` in the Compose project's root `.env` file if DockFlow Operations is not reachable at the default host URL, then start the integration profile:

```bash
docker-compose --profile integration up --build
```

The worker and DockFlow Operations must use matching `SERVICE_AUTH_SECRET`, `SERVICE_AUTH_ISSUER`, and `SERVICE_AUTH_AUDIENCE` values. The worker sends short-lived bearer tokens; the Operations sync routes reject unauthenticated requests. The default container URL assumes DockFlow Operations is running on the Docker host at port 8001.

The application will be available at:
- Frontend: `http://localhost:80`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## Environment Variables

### Backend (.env)

| Variable | Description | Default |
|----------|-------------|---------|
| `APP_NAME` | Application name | Dock Appointment Scheduling |
| `APP_VERSION` | Application version | 0.1.0 |
| `DEBUG` | Debug mode (True/False) | False |
| `DATABASE_URL` | Database connection string | sqlite:///./dock_appointments.db |
| `SECRET_KEY` | Random secret of at least 32 characters for JWT tokens | Required |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | JWT token expiration time | 30 |
| `CORS_ORIGINS` | Comma-separated list of allowed CORS origins | http://localhost:5173 |
| `JWT_ISSUER` | JWT token issuer | dock-appointment-scheduling |
| `JWT_AUDIENCE` | JWT token audience | dock-appointment-api |
| `SERVICE_AUTH_SECRET` | Shared secret for signed outbox-worker tokens (minimum 32 characters) | Not set |
| `SERVICE_AUTH_TOKEN_EXPIRE_SECONDS` | Outbox-worker token lifetime | 300 |
| `SERVICE_AUTH_ISSUER` | Integration token issuer | dock-appointment-scheduling |
| `SERVICE_AUTH_AUDIENCE` | Integration token audience | dockflow-operations |

## Testing

### Backend Tests

```bash
cd backend
pytest
```

### Frontend Tests

```bash
cd frontend
npm test
```

## Security Features

- **Password Hashing**: Uses bcrypt for secure password storage
- **JWT Authentication**: Token-based authentication with configurable expiration
- **CORS Protection**: Configurable CORS origins to prevent unauthorized cross-origin requests
- **Rate Limiting**: API rate limiting to prevent abuse (100 req/min for authenticated, 20 req/min for public endpoints)
- **Environment Variables**: Sensitive configuration via environment variables
- **SQL Injection Protection**: SQLAlchemy ORM with parameterized queries

## Database

### Development (SQLite)

By default, the application uses SQLite for development. The database file is `dock_appointments.db` in the backend directory.

### Production (PostgreSQL)

For production, configure PostgreSQL:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/dock_appointments
```

Run migrations:
```bash
alembic upgrade head
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `GET /api/v1/auth/me` - Get current user profile

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user
- `GET /api/v1/users/{id}` - Get user by ID
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Carriers
- `GET /api/v1/carriers` - List carriers
- `POST /api/v1/carriers` - Create carrier
- `GET /api/v1/carriers/{id}` - Get carrier by ID
- `PUT /api/v1/carriers/{id}` - Update carrier
- `DELETE /api/v1/carriers/{id}` - Delete carrier

### Warehouses
- `GET /api/v1/warehouses` - List warehouses
- `POST /api/v1/warehouses` - Create warehouse
- `GET /api/v1/warehouses/{id}` - Get warehouse by ID
- `PUT /api/v1/warehouses/{id}` - Update warehouse
- `DELETE /api/v1/warehouses/{id}` - Delete warehouse

### Docks
- `GET /api/v1/docks` - List docks
- `POST /api/v1/docks` - Create dock
- `GET /api/v1/docks/{id}` - Get dock by ID
- `PUT /api/v1/docks/{id}` - Update dock
- `DELETE /api/v1/docks/{id}` - Delete dock

### Appointments
- `GET /api/v1/appointments` - List appointments
- `POST /api/v1/appointments` - Create appointment
- `GET /api/v1/appointments/{id}` - Get appointment by ID
- `PUT /api/v1/appointments/{id}` - Update appointment
- `DELETE /api/v1/appointments/{id}` - Delete appointment

### Dock Unavailability
- `GET /api/v1/dock-unavailability` - List dock unavailability records
- `POST /api/v1/dock-unavailability` - Create dock unavailability record
- `GET /api/v1/dock-unavailability/{id}` - Get dock unavailability by ID
- `PATCH /api/v1/dock-unavailability/{id}` - Update dock unavailability
- `DELETE /api/v1/dock-unavailability/{id}` - Delete dock unavailability

### Dashboard
- `GET /api/v1/dashboard/metrics` - Get dashboard metrics

### Audit Logs
- `GET /api/v1/audit-logs` - List audit logs

For complete API documentation, visit `http://localhost:8000/docs`

## Timezone Handling

All datetime values are stored and returned in UTC (Coordinated Universal Time) to ensure consistency across different time zones. The application uses a custom `UTCDateTime` type decorator to enforce this.

## Troubleshooting

### Backend won't start
- Ensure Python 3.14+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify environment variables are set in `.env`

### Frontend won't start
- Ensure Node.js 22+ is installed
- Check that dependencies are installed: `npm install`
- Verify port 5173 is not in use

### Database connection errors
- For SQLite: Ensure the backend directory is writable
- For PostgreSQL: Verify the database is running and credentials are correct
- Check that the `DATABASE_URL` in `.env` is properly formatted

### CORS errors
- Verify `CORS_ORIGINS` in `.env` includes your frontend URL
- For local development, ensure `http://localhost:5173` is included

## License

This project is proprietary software. All rights reserved.
