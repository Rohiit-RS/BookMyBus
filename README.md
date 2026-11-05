# 🚌 BookMyBus - Enterprise Intercity Bus Ticketing Platform
**Architecture:** Python, PostgreSQL / Unified Relational Engine, Tailwind CSS (Light & Dark Theme), Chart.js, Mermaid.js  
**Deployment:** Vercel Production Serverless

---

## 📌 Platform Overview
**BookMyBus** is a high-availability, transactional intercity coach ticketing and fleet operations platform. It features real-time inventory locking, dynamic bus cabin seat selection, unique PNR generation, integrated cancellation and refund handling, and executive revenue intelligence dashboards.

### Key Capabilities
- **Live Seat Allocation:** Interactive cabin visualizer for 2x2 and 2+1 multi-axle sleeper/seater configurations.
- **ACID Transaction Guarantees:** Concurrency-safe reservations with unique PNR generation.
- **Fleet & Corridor Management:** Dynamic dispatching, route pairing, and schedule publishing.
- **Operational & Financial Reports:** Real-time route revenue summaries and fleet capacity utilization metrics powered by SQL aggregates.
- **Database Query Studio:** Direct execution console with duration meters and tabular results.
- **Adaptive Dark / Light Interface:** Native theme switching persisted in client storage.

---

## 🏛️ System Architecture
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

## 🚀 Local Development Setup
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the application
python app.py
```
Open [http://localhost:5000](http://localhost:5000) in your browser.

> **Database Configuration**:
> - Defaults to an integrated zero-config relational engine pre-seeded with sample records.
> - To connect directly to a remote PostgreSQL database, set `DATABASE_URL=postgresql://user:password@host:port/dbname`.
