# 🚌 BookMyBus - Bus Reservation System
### Database-Driven Web Application (Python + PostgreSQL)
**Course:** Database Systems (DBS Project)  
**Architecture:** Python (Flask), PostgreSQL / SQLite Dual-Engine, Tailwind CSS, Chart.js, Mermaid.js  
**Deployment Target:** Vercel

---

## 📌 1. Project Overview & Problem Statement
Traditional intercity bus booking processes often suffer from fragmented schedule records, manual ticket bookkeeping errors, lack of real-time seat availability visibility, and risk of double-booking under concurrency. 

**BookMyBus** is a complete, normalized relational database-driven web application designed to automate the lifecycle of bus travel management. It provides:
- Real-time seat allocation with visual bus cabin layout (lower/upper deck, 2x2 grid).
- Atomic reservation processing with ACID transactions and unique PNR generation.
- Cancellation and refund management with automatic seat release.
- Fleet, corridor, and schedule management for administrators.
- Comprehensive SQL analytical reports (Occupancy rates %, route revenues, booking status distributions).
- An interactive **SQL Query Lab** demonstrating all core database curriculum concepts (SELECT + WHERE, ORDER BY, Aggregates, GROUP BY + HAVING, Multi-Table JOINs, Subqueries, Views, and DML).

---

## 🏛️ 2. Functional Modules
| Module Name | Description | Database Entities Involved |
|-------------|-------------|----------------------------|
| **Passenger Management** | Account records, passenger roles, contacts | `users` |
| **Fleet Management** | Bus registration, categories, capacity, ratings | `buses` |
| **Route Management** | Intercity corridors, distances, durations | `routes` |
| **Schedule / Trip Planning** | Departure/arrival timings, bus assignments, fares | `trips`, `buses`, `routes` |
| **Seat Booking & Reservation** | Interactive cabin grid, atomic reservation, PNR generation | `bookings`, `booking_passengers` |
| **Cancellation & Refund** | Freeing up allocated seats, updating payment & booking state | `bookings`, `booking_passengers` |
| **Executive Reports & Analytics** | Aggregated gross revenues, fleet occupancy %, route popularity | `vw_route_revenue`, `bookings`, `trips` |
| **Interactive SQL Query Lab** | Live execution and evaluation of SQL syllabus queries | All tables and views |

---

## 📊 3. Entity-Relationship (ER) Diagram
```mermaid
erDiagram
    USERS ||--o{ BOOKINGS : "places (1:N)"
    BUSES ||--o{ TRIPS : "assigned_to (1:N)"
    ROUTES ||--o{ TRIPS : "scheduled_on (1:N)"
    TRIPS ||--o{ BOOKINGS : "reserved_for (1:N)"
    BOOKINGS ||--|{ BOOKING_PASSENGERS : "contains (1:N)"

    USERS {
        int user_id PK
        string full_name
        string email UK
        string phone
        string role
        timestamp created_at
    }

    BUSES {
        int bus_id PK
        string bus_number UK
        string operator_name
        string bus_type
        int total_seats
        float rating
    }

    ROUTES {
        int route_id PK
        string source_city
        string destination_city
        float distance_km
        float estimated_duration_hours
    }

    TRIPS {
        int trip_id PK
        int bus_id FK
        int route_id FK
        date trip_date
        time departure_time
        time arrival_time
        float fare
        string status
    }

    BOOKINGS {
        int booking_id PK
        string pnr_number UK
        int user_id FK
        int trip_id FK
        timestamp booking_timestamp
        int total_seats
        float total_amount
        string payment_status
        string booking_status
    }

    BOOKING_PASSENGERS {
        int ticket_id PK
        int booking_id FK
        int seat_number
        string passenger_name
        int passenger_age
        string passenger_gender
    }
```

---

## 🗄️ 4. Relational Schema & Integrity Constraints
All relations are strictly normalized to **Third Normal Form (3NF)**:

1. **`users`**
   - `user_id` (INTEGER, PRIMARY KEY)
   - `full_name` (VARCHAR(100), NOT NULL)
   - `email` (VARCHAR(120), UNIQUE, NOT NULL)
   - `phone` (VARCHAR(20), NOT NULL)
   - `role` (VARCHAR(20), CHECK role IN ('PASSENGER', 'ADMIN'))
   - `created_at` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)

2. **`buses`**
   - `bus_id` (INTEGER, PRIMARY KEY)
   - `bus_number` (VARCHAR(30), UNIQUE, NOT NULL)
   - `operator_name` (VARCHAR(100), NOT NULL)
   - `bus_type` (VARCHAR(40), CHECK IN ('AC Sleeper (2+1)', 'AC Seater (2+2)', 'Volvo Multi-Axle', 'Non-AC Seater (2+2)'))
   - `total_seats` (INTEGER, CHECK > 0 AND <= 60)
   - `amenities` (TEXT)
   - `rating` (NUMERIC(2,1), CHECK >= 1.0 AND <= 5.0)

3. **`routes`**
   - `route_id` (INTEGER, PRIMARY KEY)
   - `source_city` (VARCHAR(80), NOT NULL)
   - `destination_city` (VARCHAR(80), NOT NULL)
   - `distance_km` (NUMERIC(6,1), CHECK > 0)
   - `estimated_duration_hours` (NUMERIC(4,1), CHECK > 0)
   - `CONSTRAINT uq_route_pair UNIQUE (source_city, destination_city)`
   - `CONSTRAINT chk_diff_city CHECK (source_city <> destination_city)`

4. **`trips`**
   - `trip_id` (INTEGER, PRIMARY KEY)
   - `bus_id` (INTEGER, FK &rarr; `buses.bus_id` ON DELETE CASCADE)
   - `route_id` (INTEGER, FK &rarr; `routes.route_id` ON DELETE CASCADE)
   - `trip_date` (DATE, NOT NULL)
   - `departure_time` (TIME, NOT NULL)
   - `arrival_time` (TIME, NOT NULL)
   - `fare` (NUMERIC(8,2), CHECK fare > 0)
   - `status` (VARCHAR(20), CHECK status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED'))

5. **`bookings`**
   - `booking_id` (INTEGER, PRIMARY KEY)
   - `pnr_number` (VARCHAR(20), UNIQUE, NOT NULL)
   - `user_id` (INTEGER, FK &rarr; `users.user_id` ON DELETE RESTRICT)
   - `trip_id` (INTEGER, FK &rarr; `trips.trip_id` ON DELETE RESTRICT)
   - `booking_timestamp` (TIMESTAMP, DEFAULT CURRENT_TIMESTAMP)
   - `total_seats` (INTEGER, CHECK total_seats > 0)
   - `total_amount` (NUMERIC(10,2), CHECK total_amount >= 0)
   - `payment_status` (VARCHAR(20), CHECK IN ('PAID', 'REFUNDED'))
   - `booking_status` (VARCHAR(20), CHECK IN ('CONFIRMED', 'CANCELLED'))

6. **`booking_passengers`**
   - `ticket_id` (INTEGER, PRIMARY KEY)
   - `booking_id` (INTEGER, FK &rarr; `bookings.booking_id` ON DELETE CASCADE)
   - `seat_number` (INTEGER, CHECK > 0 AND <= 60)
   - `passenger_name` (VARCHAR(100), NOT NULL)
   - `passenger_age` (INTEGER, CHECK >= 1 AND <= 120)
   - `passenger_gender` (VARCHAR(15), CHECK IN ('Male', 'Female', 'Other'))
   - `CONSTRAINT uq_booking_seat UNIQUE (booking_id, seat_number)`

---

## 🔍 5. SQL Concepts Covered in the Syllabus
All of the following are implemented and demonstrable with 1-click in the web application's **SQL Lab** (`/sql-lab`):
1. **SELECT & Filtering with WHERE**: Finding available trips by city and maximum fare threshold.
2. **ORDER BY**: Sorting fleet by customer review rating and passenger capacity.
3. **Aggregates (COUNT, SUM, AVG, MIN, MAX)**: Calculating gross revenue, average booking value, and total ticket count.
4. **GROUP BY & HAVING**: Identifying high-performing routes generating revenue above a given threshold.
5. **Multi-Table Relational JOIN**: 5-table join (`bookings`, `users`, `booking_passengers`, `trips`, `routes`, `buses`) to assemble complete passenger boarding manifests.
6. **Nested Subqueries**: Identifying premium buses whose average trip fare exceeds the fleet-wide average.
7. **Relational Views**:
   - `vw_trip_schedule`: Consolidates route and bus details for all scheduled trips.
   - `vw_booking_summary`: Formats booking records with customer and route info.
   - `vw_route_revenue`: Aggregate view computing total passengers and revenue per city pair.
8. **Data Modification (INSERT, UPDATE, DELETE)**: Adding buses and routes, rescheduling departures, and releasing cancelled seats.

---

## 🚀 6. Running Locally
```bash
# 1. Clone repository
git clone <repo-url>
cd BookMyBus

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the application
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

> **Database Configuration**:
> - By default, the application runs on a high-speed SQLite compatibility engine pre-seeded with realistic data.
> - To connect directly to a remote PostgreSQL instance (e.g. Neon, Supabase, or AWS RDS), set `DATABASE_URL=postgresql://user:password@host:port/dbname`.

---

## 🌐 7. Vercel Deployment
The application is structured for Vercel's native Python serverless runtime:
- `api/index.py` handles requests through WSGI.
- `vercel.json` routes all paths into the Python function.
