# Database Systems (DBS) Course Project Documentation
## Topic: Bus Reservation System (BookMyBus)

---

### 1. Project Title
**BookMyBus: A Full-Stack Database-Driven Intercity Bus Reservation & Fleet Management System**

---

### 2. Problem Statement
Physical ticket booking counters and manual scheduling ledgers suffer from major operational bottlenecks:
- Inefficient seat allocation and inability of passengers to view real-time layout before purchase.
- Concurrency issues such as double-booking the same seat on high-demand holiday corridors.
- Time-consuming cancellation, refund, and reconciliation processes.
- Lack of aggregated metrics for fleet managers to evaluate route profitability and occupancy.

---

### 3. Objectives of the System
1. **Automate Ticket Reservation:** Provide a responsive digital interface for searching, selecting, and confirming bus bookings in real-time.
2. **Interactive Seat Selection:** Enable passengers to choose specific seat numbers visually with instant feedback on availability.
3. **Data Integrity & Consistency:** Enforce relational integrity through Primary Keys, Foreign Keys, NOT NULL, UNIQUE, and CHECK constraints.
4. **ACID Transaction Guarantees:** Ensure that seat reservation and passenger detail storage either succeed entirely or roll back safely.
5. **Business Intelligence & Reporting:** Deliver executive reports analyzing route revenue, bus utilization rates, and booking statistics.
6. **Curriculum Demonstration:** Implement and demonstrate core course concepts: complex JOINs, aggregate queries, GROUP BY with HAVING, nested subqueries, and relational views.

---

### 4. Identified Users of the Application
- **Passengers / Customers:** Search schedules, view amenities, select seats, book tickets with instant PNR generation, and cancel reservations.
- **Fleet Administrators:** Register new buses, configure intercity routes, schedule departures, manage fares, and inspect bookings.
- **Academic Evaluators / Instructors:** Use the built-in **SQL Query Lab** to execute test queries directly against the database schema.

---

### 5. Functional Modules
1. **Passenger Management Module:** User accounts, contact details, authentication state, and role authorization (`users`).
2. **Bus & Fleet Management Module:** Fleet inventory, bus categories (AC Sleeper, Volvo Multi-Axle, Seater), seat capacity, amenities, and ratings (`buses`).
3. **Route & Corridor Management Module:** Origin/destination pairs, verified distances, and travel durations (`routes`).
4. **Schedule & Trip Management Module:** Timings, calendar dates, bus assignments, and ticket pricing (`trips`).
5. **Seat Allocation & Booking Module:** Interactive cabin layout, PNR generation, payment tracking, and passenger manifests (`bookings`, `booking_passengers`).
6. **Cancellation & Refund Module:** Ticket cancellation mechanism that updates booking status and immediately restores seat availability.
7. **Reports & Analytics Module:** Visual Chart.js charts and summary tables for fleet occupancy and route revenue.
8. **Interactive SQL Lab Module:** Curriculum SQL query runner with real-time execution times and tabular results.

---

### 6. Relational Schema & Integrity Constraints
- **`users`** (`user_id` [PK], `full_name`, `email` [UK], `phone`, `role` [CHECK])
- **`buses`** (`bus_id` [PK], `bus_number` [UK], `operator_name`, `bus_type` [CHECK], `total_seats` [CHECK], `amenities`, `rating` [CHECK])
- **`routes`** (`route_id` [PK], `source_city`, `destination_city`, `distance_km` [CHECK], `estimated_duration_hours` [CHECK], `UNIQUE(source_city, destination_city)`)
- **`trips`** (`trip_id` [PK], `bus_id` [FK &rarr; buses], `route_id` [FK &rarr; routes], `trip_date`, `departure_time`, `arrival_time`, `fare` [CHECK], `status` [CHECK])
- **`bookings`** (`booking_id` [PK], `pnr_number` [UK], `user_id` [FK &rarr; users], `trip_id` [FK &rarr; trips], `booking_timestamp`, `total_seats` [CHECK], `total_amount` [CHECK], `payment_status` [CHECK], `booking_status` [CHECK])
- **`booking_passengers`** (`ticket_id` [PK], `booking_id` [FK &rarr; bookings], `seat_number` [CHECK], `passenger_name`, `passenger_age` [CHECK], `passenger_gender` [CHECK], `UNIQUE(booking_id, seat_number)`)

---

### 7. Normalization Analysis (1NF, 2NF, 3NF)
- **First Normal Form (1NF):** Each attribute contains only atomic values. Passenger details for multiple seats in a single booking are separated into atomic tuples in `booking_passengers`.
- **Second Normal Form (2NF):** All non-key attributes are fully functionally dependent on the entire primary key. Route distance and duration depend only on `route_id`, separated from trip schedules.
- **Third Normal Form (3NF):** No transitive dependencies exist between non-key attributes. In `trips`, only `bus_id` and `route_id` are stored. Operator name and distance are not duplicated in `trips`.

---

### 8. Relational Views
1. **`vw_trip_schedule`:** Multi-table join across `trips`, `buses`, and `routes`.
2. **`vw_booking_summary`:** Comprehensive view combining booking headers, customer profiles, trip timings, and vehicle operators.
3. **`vw_route_revenue`:** Aggregation view computing total scheduled trips, total tickets, and gross confirmed revenue by route.

---

### 9. Representative SQL Queries
All sample queries are located in `database/queries.sql` and demonstrable in `/sql-lab`.
- **WHERE Filtering:** `SELECT * FROM trips WHERE source_city = 'Bangalore' AND fare <= 1300;`
- **ORDER BY:** `SELECT * FROM buses ORDER BY rating DESC, total_seats ASC;`
- **Aggregate Functions:** `SELECT COUNT(booking_id), SUM(total_amount), AVG(total_amount), MIN(total_amount), MAX(total_amount) FROM bookings WHERE booking_status = 'CONFIRMED';`
- **GROUP BY & HAVING:** `SELECT source_city, destination_city, SUM(total_amount) FROM ... GROUP BY ... HAVING SUM(total_amount) >= 1000;`
- **5-Table JOIN:** Joins `bookings`, `users`, `booking_passengers`, `trips`, `routes`, and `buses`.
- **Subquery:** Identifies buses charging above-average fares.
