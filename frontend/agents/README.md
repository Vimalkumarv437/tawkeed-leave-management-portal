# Frontend AI Review & Quality Agents

This directory contains specialized agent definitions and review checklists for developing and evaluating the **Tawkeed Leave Management Portal Frontend** (React + Vite).

---

## Agent Suite Overview

| Agent File | Role | Focus Area |
| :--- | :--- | :--- |
| `frontend-code-reviewer.md` | Senior React Architect | Code quality, component structure, modularity, hook separation |
| `frontend-security-reviewer.md` | Frontend AppSec Specialist | Token lifecycle, XSS prevention, sensitive data exposure, RBAC UI |
| `frontend-ui-ux-reviewer.md` | Senior UI/UX Designer & Engineer | Design consistency, responsiveness, accessibility, loading/empty states |
| `frontend-performance-reviewer.md` | Frontend Performance Engineer | Re-renders, bundle size, network efficiency, memoization |
| `frontend-cleanup-agent.md` | Repository Maintainer | Dead code elimination, unused components/imports, dependency pruning |
| `frontend-api-integration-reviewer.md` | Integration Engineer | API schema parity, error handling, Axios interceptors, backend contract |
| `frontend-test-reviewer.md` | Quality Assurance Lead | Test strategies, critical flow coverage, role routing tests |

---

## Safety & Governance Rules

All agents operating in this repository must strictly adhere to the following rules:
1. **Never modify backend files**: The backend is immutable during frontend development.
2. **Never invent fake API endpoints**: All API integration must match actual FastAPI backend routes.
3. **Never expose secrets or tokens**: Do not hardcode credentials or log JWTs in client code.
4. **Preserve working architecture**: Prefer small, surgical, explainable enhancements over broad rewrites.
5. **No unnecessary dependencies**: Rely on standard React patterns, Axios, and React Router without heavy state libraries.
6. **No nested CI/CD directory**: Frontend must NOT have a `.github/` folder; root `.github/workflows/` manages CI/CD.
