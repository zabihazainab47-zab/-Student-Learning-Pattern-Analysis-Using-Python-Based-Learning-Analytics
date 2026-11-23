# System Architecture & Technical Design
## Student Learning Pattern Analysis

---

## 1. High-Level Architecture Diagram

The system employs a layered, modular client-server architecture designed for high security, clear separation of concerns, and robust role-based access control.

```mermaid
flowchart TD
    subgraph Client["Presentation Layer (Frontend SPA)"]
        UI_Admin["Administrator Console<br/>dashboards/admin.html"]
        UI_Teacher["Teacher Dashboard<br/>dashboards/teacher.html"]
        UI_Student["Student Progress Portal<br/>dashboards/student.html"]
        JS_Client["API Client & Session Guard<br/>js/api.js, js/auth.js"]
    end

    subgraph Backend["Application Layer (FastAPI REST Server)"]
        MainApp["Application Entrypoint<br/>backend/main.py"]
        AuthMiddleware["JWT Authentication & RBAC<br/>backend/auth.py, permissions.py"]
        
        subgraph Routers["API Routers"]
            R_Auth["/api/auth"]
            R_Class["/api/classes"]
            R_Teacher["/api/teachers"]
            R_Student["/api/students"]
            R_Assess["/api/assessments"]
            R_Dash["/api/dashboard"]
            R_Data["/api/data"]
        end

        subgraph Services["Domain Services"]
            S_Assess["Assessment Service<br/>assessment_service.py"]
            S_Analytics["Analytics Service<br/>analytics_service.py"]
            S_Insight["Support Insight Service<br/>insight_service.py"]
            S_CSV["CSV Processing Service<br/>csv_service.py"]
        end
    end

    subgraph Storage["Data Persistence Layer (SQLite)"]
        DB[(fyp.db<br/>Normalized 6-Table Relational Schema)]
    end

    UI_Admin --> JS_Client
    UI_Teacher --> JS_Client
    UI_Student --> JS_Client
    JS_Client -->|Bearer JWT HTTP Requests| MainApp

    MainApp --> AuthMiddleware
    AuthMiddleware --> Routers
    
    R_Assess --> S_Assess
    R_Dash --> S_Analytics
    R_Dash --> S_Insight
    R_Data --> S_CSV
    
    Routers --> DB
    Services --> DB
```

---

## 2. Request Lifecycle & Authorization Enforcement

1. **Authentication:**
   Users submit credentials to `/api/auth/login`. The backend verifies the bcrypt password hash in `users` and emits a signed JWT token encapsulating the user's ID, username, and assigned role.
2. **Permission Boundary:**
   On every secured endpoint, FastAPI dependencies (`get_current_user`, `require_roles`, `check_teacher_class_access`, `check_student_record_access`) intercept the request:
   * **Teacher Class Scoping:** Queries the `teacher_classes` junction table. If a teacher requests data for a class outside their assigned IDs, HTTP 403 Forbidden is immediately raised.
   * **Student Record Scoping:** Compares `user.student_id` directly against the requested record. Students cannot access other students' profiles or administrative endpoints.
3. **Data Validation:**
   Before any assessment record is saved or updated, marks are validated against the exact mid-semester bounds ($0\text{--}30$ Midterm, $0\text{--}3$ Assignment, $0\text{--}3$ Presentation, $0\text{--}4$ Attendance).
4. **Descriptive Analytics & Traceable Insights:**
   Dashboard calculations are performed on-the-fly from live SQL queries, ensuring that no statistics are hardcoded and that missing components are accurately distinguished from zero marks.
