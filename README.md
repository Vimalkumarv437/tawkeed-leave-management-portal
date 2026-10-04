# Tawkeed Investments – Leave Management Portal

Take-home assignment by **Vimal Kumar V.**

A web app where employees apply for leave, managers approve or reject requests from their own team, and admins maintain users, leave types, balances and public holidays.

| | |
|---|---|
| Frontend (Vercel) | https://tawkeed-leave-management-portal.vercel.app |
| Backend (Render) | https://tawkeed-leave-management-portal.onrender.com |
| API docs (Swagger) | https://tawkeed-leave-management-portal.onrender.com/docs |
| Health check | https://tawkeed-leave-management-portal.onrender.com/health |
| Test credentials | `[placeholder: share separately]` |

> **Current Verification Note**
> The login endpoint successfully authenticates credentials, while protected post-login API requests are currently being verified as part of the final deployment validation. The authentication flow is being tested locally and in the deployed environment before final submission.

A longer write-up with diagrams and a step-by-step reviewer checklist is in the accompanying PDF, *Tawkeed_Leave_Management_Portal_Documentation.pdf*.

---

## 1. Run it locally

You need Python, Node.js with npm, Git and a local PostgreSQL server. Minimum versions: not specified.

### Get the code

```bash
git clone <repository-url>
cd tawkeed_leave_management_portal
```

### Backend

Create an empty PostgreSQL database first and keep its connection URL handy.

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

Create `backend/.env` with your own values (never commit this file):

```env
DATABASE_URL=<your-local-postgresql-url>
JWT_SECRET_KEY=<a-long-random-string-you-generate>
JWT_ALGORITHM=<jwt-algorithm-used-by-the-project>
FRONTEND_URL=http://localhost:5173
ENVIRONMENT=<environment-name>
```

Apply migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload
```

Swagger is then at http://localhost:8000/docs and the health check at http://localhost:8000/health.

How the first local admin account is created: **not specified here**. Check `backend/scripts/` and `backend/README.md`.

### Frontend

In a second terminal:

```bash
cd frontend
npm install
```

Create `frontend/.env`:

```env
VITE_API_BASE_URL=http://localhost:8000
```

If the frontend expects the `/api` prefix to be part of this value, adjust it. Then:

```bash
npm run dev
```

Open the URL Vite prints (5173 by default).

The repo also contains `Dockerfile`s, `docker-compose.yml` (backend) and `nginx.conf` (frontend). This guide uses the manual route.

---

## 2. Architecture

```
Browser
   ↓
React + TypeScript   (Vercel)
   ↓
FastAPI REST API     (Render)
   ↓
Service layer
   ↓
SQLAlchemy
   ↓
PostgreSQL           (Render)
```

| Part | Responsibility |
|---|---|
| Frontend | UI, navigation, forms, showing data, calling the API |
| API | Receives requests, returns responses |
| Dependencies | Authentication, authorization, shared request dependencies |
| Services | Business logic (the leave rules) |
| Models | SQLAlchemy representations of database entities |
| Schemas | Pydantic validation of API input and output |
| Database | Persistent data, with schema changes managed by Alembic |

The leave rules live in the service layer so they are in one place and easy to test. The backend is the source of truth: the frontend never decides whether a request is valid.

**Leave rules in plain words**

- Leave is counted in working days, not calendar days.
- Overlapping requests are refused.
- A request needs enough available balance.
- A pending request reserves its days. Approval turns reserved days into used days. Rejection releases them. Eligible cancellation restores the balance according to the request state.
- A manager can only act on their own team's requests, and never on their own.

**Tables:** `users`, `leave_types`, `leave_balances`, `leave_requests`, `leave_request_allocations`, `public_holidays`, `audit_logs`. Column-level detail is in `backend/app/models` and the Alembic migrations.

```
backend/app/    core · models · schemas · api · services · dependencies
backend/        tests · alembic · scripts · agents
frontend/src/   components · pages · context · hooks · services · routes · types · utils
```

The purpose of the `agents/` and `scripts/` folders is not covered here.

---

## 3. API summary

Full request and response details: **https://tawkeed-leave-management-portal.onrender.com/docs**

| Group | Endpoints |
|---|---|
| Auth | `POST /api/auth/login` · `GET /api/auth/me` · `POST /api/auth/logout` |
| Admin: users | `GET, POST /api/admin/users` · `GET, PUT, PATCH /api/admin/users/{user_id}` · `POST /api/admin/users/{user_id}/reactivate` |
| Admin: leave types | `GET, POST /api/admin/leave-types` · `GET, PUT, PATCH /api/admin/leave-types/{leave_type_id}` |
| Admin: balances | `GET, POST /api/admin/balances` · `GET, PUT, PATCH /api/admin/balances/{balance_id}` |
| Admin: holidays | `GET, POST /api/admin/holidays` · `GET, PUT, PATCH /api/admin/holidays/{holiday_id}` |
| Manager | `GET /api/manager/requests` · `POST /api/manager/requests/{request_id}/approve` · `POST /api/manager/requests/{request_id}/reject` · `GET /api/manager/calendar` |
| Employee | `GET /api/employees/me/balances` · `GET /api/employees/me/leaves` |
| Leaves | `POST /api/leaves` · `GET /api/leaves` · `GET /api/leaves/{request_id}` · `POST /api/leaves/{request_id}/cancel` |
| Health | `GET /health` |

---

## 4. Test report

**273 backend tests passed. Coverage approximately 93%** (not 100%).

```bash
cd backend
pytest --cov=app
```

That is the usual Pytest + pytest-cov form. The exact flags used in CI are in `.github/workflows/backend-ci.yml`.

| Group | What it checks |
|---|---|
| Authentication | Login, current-user lookup, logout |
| Authorization | Each role reaches only what it should |
| Leave creation | Valid requests are accepted and stored |
| Leave validation | Invalid or overlapping requests are refused |
| Leave balance | Balances change correctly through each request state |
| Approval / rejection | Reserved days become used or are released |
| Cancellation | Eligible cancellations restore the balance |
| Manager restrictions | Team scope and no self-approval |
| Admin operations | Users, leave types, balances, holidays |
| Error handling | Sensible errors for bad input and forbidden actions |
| Service / API behaviour | Business logic directly, and endpoints through HTTPX |

Tools: Pytest, HTTPX, pytest-cov. Code quality: Ruff (backend), ESLint (frontend).
There are **no frontend automated tests**. CI runs ESLint and a production build for the frontend.

**CI (GitHub Actions)**
- Backend: checkout, set up Python, install dependencies, run tests, run coverage, run code-quality checks.
- Frontend: checkout, set up Node.js, install dependencies, run ESLint, build.

---

## 5. Security measures and why

| Measure | Why |
|---|---|
| JWT authentication | The backend can identify the caller on every request |
| HTTP-only access-token cookie | Page JavaScript can't read the token, so an injected script can't easily steal it |
| Argon2 password hashing | Plain-text passwords are never stored, so a database leak doesn't directly expose them |
| Role-based authorization | The backend verifies the role; the frontend doesn't get to decide who is an admin |
| Failed-login tracking and lockout | Slows down password guessing |
| Active-user checks | Deactivated accounts can't keep working |
| Request validation (Pydantic) | Bad input is rejected before it reaches business logic |
| CORS | Limits which browser origins can call the API (`FRONTEND_URL` identifies the frontend) |
| Environment variables | Secrets and environment-specific values aren't hard-coded |
| No secrets in Git | Production secrets must never be committed |

Environment variables: `VITE_API_BASE_URL` (frontend); `DATABASE_URL`, `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `FRONTEND_URL`, `ENVIRONMENT` (backend).

---

## 6. Assumptions

1. Each user has a single role: Employee, Manager or Admin.
2. A manager's team is the set of users assigned to that manager.
3. The backend is the source of truth for every leave rule; frontend checks are only for faster feedback.
4. Whether a request can be cancelled, and how the balance is restored, is decided by the backend from the request's state.
5. Whether admins hold their own leave is not specified, so no claim is made.
6. Reviewers use the deployed URLs with credentials shared separately.
7. A PostgreSQL server is available locally for local setup.

## 7. Known limitations and issues

| Item | Status |
|---|---|
| Login works, but protected post-login requests are still being verified locally and in the deployed environment (see the note at the top) | **Open** |
| No frontend automated tests | Limitation |
| Backend coverage is approximately 93%, not 100% | Limitation |
| No email notifications | Limitation |
| Password reset / change workflow not covered (future improvement if required) | Limitation |
| Advanced audit-log filtering, structured logging/monitoring and production secret rotation are future improvements | Limitation |
| Further known bugs: `[placeholder: add before submission, or write "None known"]` | Open |

**Possible future work:** email notifications, password reset/change, more frontend tests, audit-log filtering, structured logging and monitoring, secret rotation, pagination improvements, calendar integrations. These are enhancements, not missing requirements.

---

Prepared for: Tawkeed Investments · Assignment: Leave Management Portal · Developer: Vimal Kumar V.
