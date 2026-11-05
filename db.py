"""
Database Access Layer for Bus Reservation System (DBS Project)
Supports:
1. PostgreSQL (via DATABASE_URL or POSTGRES_URL)
2. Standalone SQLite (zero-config local / Vercel fallback)
Includes automatic schema creation, realistic seed data, and SQL demonstration query engine.
"""

import os
import random
import re
import string
import sqlite3
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple

# Database connection configuration
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL")
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith(("postgres://", "postgresql://")))

if IS_POSTGRES:
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
    except ImportError:
        IS_POSTGRES = False

SQLITE_PATH = os.environ.get("SQLITE_PATH") or (
    "/tmp/bus_reservation.db" if os.path.exists("/tmp") and os.name != "nt" else os.path.join(os.path.dirname(__file__), "bus_reservation.db")
)


def get_connection():
    """Get a database connection (PostgreSQL if configured, otherwise SQLite)."""
    global IS_POSTGRES
    if IS_POSTGRES and DATABASE_URL:
        try:
            # Handle postgres:// vs postgresql://
            url = DATABASE_URL
            if url.startswith("postgres://"):
                url = url.replace("postgres://", "postgresql://", 1)
            conn = psycopg2.connect(url)
            conn.autocommit = False
            return conn, "postgres"
        except Exception as e:
            print(f"[DB Warning] Could not connect to PostgreSQL ({e}). Falling back to SQLite.")
            IS_POSTGRES = False

    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn, "sqlite"


def query_db(query: str, args: tuple = (), one: bool = False, commit: bool = False) -> Any:
    """Execute a query and return results as list of dicts or single dict."""
    conn, db_type = get_connection()
    try:
        if db_type == "postgres":
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Convert SQLite style ? to %s if needed
                pg_query = query.replace("?", "%s")
                cur.execute(pg_query, args)
                if commit:
                    conn.commit()
                    return cur.rowcount
                if cur.description:
                    results = [dict(row) for row in cur.fetchall()]
                    return (results[0] if results else None) if one else results
                conn.commit()
                return None
        else:
            cur = conn.cursor()
            # Convert %s to ? if postgres style passed
            sqlite_query = re.sub(r'(?<!%)(%s)', '?', query)
            cur.execute(sqlite_query, args)
            if commit:
                conn.commit()
                return cur.rowcount
            if cur.description:
                rows = cur.fetchall()
                results = [dict(row) for row in rows]
                return (results[0] if results else None) if one else results
            conn.commit()
            return None
    finally:
        conn.close()


def execute_transaction(operations: List[Tuple[str, tuple]]) -> bool:
    """Execute multiple queries within a single ACID transaction."""
    conn, db_type = get_connection()
    try:
        if db_type == "postgres":
            with conn.cursor() as cur:
                for q, args in operations:
                    pg_q = q.replace("?", "%s")
                    cur.execute(pg_q, args)
            conn.commit()
        else:
            cur = conn.cursor()
            for q, args in operations:
                sq_q = re.sub(r'(?<!%)(%s)', '?', q)
                cur.execute(sq_q, args)
            conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db(force: bool = False):
    """Initialize database tables, views, and seed data."""
    conn, db_type = get_connection()
    try:
        cur = conn.cursor()
        
        # Check if tables already exist
        if not force:
            if db_type == "postgres":
                cur.execute("SELECT to_regclass('public.buses');")
                if cur.fetchone()[0]:
                    return
            else:
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='buses';")
                if cur.fetchone():
                    return

        print(f"[DB Init] Setting up database using {db_type.upper()}...")

        if db_type == "postgres":
            schema_file = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
            seed_file = os.path.join(os.path.dirname(__file__), "database", "seed.sql")
            if os.path.exists(schema_file):
                with open(schema_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
            if os.path.exists(seed_file):
                with open(seed_file, "r", encoding="utf-8") as f:
                    cur.execute(f.read())
            conn.commit()
        else:
            # SQLite setup with identical schema semantics
            sqlite_ddl = """
            DROP VIEW IF EXISTS vw_route_revenue;
            DROP VIEW IF EXISTS vw_booking_summary;
            DROP VIEW IF EXISTS vw_trip_schedule;
            DROP TABLE IF EXISTS booking_passengers;
            DROP TABLE IF EXISTS bookings;
            DROP TABLE IF EXISTS trips;
            DROP TABLE IF EXISTS routes;
            DROP TABLE IF EXISTS buses;
            DROP TABLE IF EXISTS users;

            CREATE TABLE users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'PASSENGER' CHECK (role IN ('PASSENGER', 'ADMIN')),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE buses (
                bus_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_number TEXT NOT NULL UNIQUE,
                operator_name TEXT NOT NULL,
                bus_type TEXT NOT NULL CHECK (bus_type IN ('AC Sleeper (2+1)', 'AC Seater (2+2)', 'Volvo Multi-Axle', 'Non-AC Seater (2+2)')),
                total_seats INTEGER NOT NULL CHECK (total_seats > 0 AND total_seats <= 60),
                amenities TEXT DEFAULT 'WiFi, Charging Port, Water Bottle, Blanket',
                rating REAL DEFAULT 4.5 CHECK (rating >= 1.0 AND rating <= 5.0)
            );

            CREATE TABLE routes (
                route_id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_city TEXT NOT NULL,
                destination_city TEXT NOT NULL,
                distance_km REAL NOT NULL CHECK (distance_km > 0),
                estimated_duration_hours REAL NOT NULL CHECK (estimated_duration_hours > 0),
                CONSTRAINT uq_route_pair UNIQUE (source_city, destination_city),
                CONSTRAINT chk_diff_city CHECK (source_city <> destination_city)
            );

            CREATE TABLE trips (
                trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
                bus_id INTEGER NOT NULL REFERENCES buses(bus_id) ON DELETE CASCADE,
                route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
                trip_date TEXT NOT NULL,
                departure_time TEXT NOT NULL,
                arrival_time TEXT NOT NULL,
                fare REAL NOT NULL CHECK (fare > 0),
                status TEXT NOT NULL DEFAULT 'SCHEDULED' CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED'))
            );

            CREATE TABLE bookings (
                booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                pnr_number TEXT NOT NULL UNIQUE,
                user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
                trip_id INTEGER NOT NULL REFERENCES trips(trip_id) ON DELETE RESTRICT,
                booking_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                total_seats INTEGER NOT NULL CHECK (total_seats > 0),
                total_amount REAL NOT NULL CHECK (total_amount >= 0),
                payment_status TEXT NOT NULL DEFAULT 'PAID' CHECK (payment_status IN ('PAID', 'REFUNDED')),
                booking_status TEXT NOT NULL DEFAULT 'CONFIRMED' CHECK (booking_status IN ('CONFIRMED', 'CANCELLED'))
            );

            CREATE TABLE booking_passengers (
                ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
                seat_number INTEGER NOT NULL CHECK (seat_number > 0 AND seat_number <= 60),
                passenger_name TEXT NOT NULL,
                passenger_age INTEGER NOT NULL CHECK (passenger_age >= 1 AND passenger_age <= 120),
                passenger_gender TEXT NOT NULL CHECK (passenger_gender IN ('Male', 'Female', 'Other')),
                CONSTRAINT uq_booking_seat UNIQUE (booking_id, seat_number)
            );

            -- Views
            CREATE VIEW vw_trip_schedule AS
            SELECT 
                t.trip_id,
                t.trip_date,
                t.departure_time,
                t.arrival_time,
                t.fare,
                t.status AS trip_status,
                b.bus_id,
                b.bus_number,
                b.operator_name,
                b.bus_type,
                b.total_seats,
                r.route_id,
                r.source_city,
                r.destination_city,
                r.distance_km,
                r.estimated_duration_hours
            FROM trips t
            INNER JOIN buses b ON t.bus_id = b.bus_id
            INNER JOIN routes r ON t.route_id = r.route_id;

            CREATE VIEW vw_booking_summary AS
            SELECT 
                bk.booking_id,
                bk.pnr_number,
                bk.booking_timestamp,
                bk.total_seats,
                bk.total_amount,
                bk.payment_status,
                bk.booking_status,
                u.full_name AS customer_name,
                u.email AS customer_email,
                u.phone AS customer_phone,
                r.source_city,
                r.destination_city,
                t.trip_date,
                t.departure_time,
                b.bus_number,
                b.operator_name,
                b.bus_type
            FROM bookings bk
            INNER JOIN users u ON bk.user_id = u.user_id
            INNER JOIN trips t ON bk.trip_id = t.trip_id
            INNER JOIN routes r ON t.route_id = r.route_id
            INNER JOIN buses b ON t.bus_id = b.bus_id;

            CREATE VIEW vw_route_revenue AS
            SELECT 
                r.route_id,
                r.source_city,
                r.destination_city,
                COUNT(DISTINCT t.trip_id) AS total_trips,
                COUNT(DISTINCT bk.booking_id) AS total_bookings,
                COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_seats ELSE 0 END), 0) AS confirmed_passengers,
                COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_amount ELSE 0 END), 0) AS total_revenue
            FROM routes r
            LEFT JOIN trips t ON r.route_id = t.route_id
            LEFT JOIN bookings bk ON t.trip_id = bk.trip_id
            GROUP BY r.route_id, r.source_city, r.destination_city;
            """
            cur.executescript(sqlite_ddl)

            # Insert Seed Data
            today_str = date.today().isoformat()
            tomorrow_str = (date.today() + timedelta(days=1)).isoformat()
            day_after_str = (date.today() + timedelta(days=2)).isoformat()

            users_data = [
                (1, 'Admin Controller', 'admin@bookmybus.com', '+91 98765 43210', 'ADMIN'),
                (2, 'Rohit Sharma', 'rohit.sharma@example.com', '+91 98450 12345', 'PASSENGER'),
                (3, 'Priya Patel', 'priya.patel@example.com', '+91 97312 67890', 'PASSENGER'),
                (4, 'Aditya Verma', 'aditya.v@example.com', '+91 99001 54321', 'PASSENGER'),
                (5, 'Sneha Kulkarni', 'sneha.k@example.com', '+91 94480 98765', 'PASSENGER'),
                (6, 'Rahul Nair', 'rahul.nair@example.com', '+91 91234 56789', 'PASSENGER')
            ]
            cur.executemany("INSERT INTO users VALUES (?, ?, ?, ?, ?, datetime('now', '-5 days'));", users_data)

            buses_data = [
                (1, 'KA-01-AB-1234', 'GreenLine Travels', 'AC Sleeper (2+1)', 30, 'WiFi, Charging, Pillow, Blanket, Water Bottle', 4.8),
                (2, 'KA-05-MN-5678', 'KSRTC Airavat Club Class', 'Volvo Multi-Axle', 40, 'Reclining Seats, AC, Reading Light, Emergency Hammer', 4.7),
                (3, 'MH-02-XY-9012', 'Orange Tours & Travels', 'AC Sleeper (2+1)', 30, 'Personal TV, WiFi, GPS Tracking, Charging Port', 4.6),
                (4, 'TS-09-CD-3456', 'VRL Travels', 'Volvo Multi-Axle', 40, 'AC, Charging Port, Blanket, Water Bottle', 4.5),
                (5, 'TN-07-EF-7890', 'SRS Express', 'AC Seater (2+2)', 44, 'Pushback Seats, AC, Music, Fire Extinguisher', 4.3),
                (6, 'DL-01-GH-2345', 'IntrCity SmartBus', 'AC Sleeper (2+1)', 30, 'Smart Boarding, WiFi, Live CCTV, Restroom on-board', 4.9),
                (7, 'GA-03-JK-6789', 'Goa State Shuttle', 'Non-AC Seater (2+2)', 48, 'Comfortable Seating, Luggage Space, FM Radio', 4.1)
            ]
            cur.executemany("INSERT INTO buses VALUES (?, ?, ?, ?, ?, ?, ?);", buses_data)

            routes_data = [
                (1, 'Bangalore', 'Hyderabad', 570.0, 8.5),
                (2, 'Hyderabad', 'Bangalore', 570.0, 8.5),
                (3, 'Bangalore', 'Chennai', 345.0, 6.0),
                (4, 'Chennai', 'Bangalore', 345.0, 6.0),
                (5, 'Mumbai', 'Goa', 590.0, 11.0),
                (6, 'Goa', 'Mumbai', 590.0, 11.0),
                (7, 'Bangalore', 'Goa', 560.0, 10.5),
                (8, 'Delhi', 'Jaipur', 280.0, 5.0),
                (9, 'Mumbai', 'Pune', 150.0, 3.5),
                (10, 'Pune', 'Mumbai', 150.0, 3.5)
            ]
            cur.executemany("INSERT INTO routes VALUES (?, ?, ?, ?, ?);", routes_data)

            trips_data = [
                (1, 1, 1, today_str, '21:30', '06:00', 1250.00, 'SCHEDULED'),
                (2, 2, 3, today_str, '06:00', '12:00', 850.00, 'SCHEDULED'),
                (3, 3, 5, today_str, '20:00', '07:00', 1600.00, 'SCHEDULED'),
                (4, 4, 1, today_str, '22:15', '06:45', 1150.00, 'SCHEDULED'),
                (5, 5, 3, today_str, '14:30', '20:30', 650.00, 'SCHEDULED'),
                (6, 6, 8, today_str, '07:00', '12:00', 799.00, 'SCHEDULED'),
                (7, 1, 7, tomorrow_str, '21:00', '07:30', 1400.00, 'SCHEDULED'),
                (8, 2, 4, tomorrow_str, '13:00', '19:00', 850.00, 'SCHEDULED'),
                (9, 3, 6, tomorrow_str, '19:30', '06:30', 1550.00, 'SCHEDULED'),
                (10, 4, 2, tomorrow_str, '22:00', '06:30', 1200.00, 'SCHEDULED'),
                (11, 1, 1, day_after_str, '21:30', '06:00', 1250.00, 'SCHEDULED'),
                (12, 2, 3, day_after_str, '06:30', '12:30', 890.00, 'SCHEDULED')
            ]
            cur.executemany("INSERT INTO trips VALUES (?, ?, ?, ?, ?, ?, ?, ?);", trips_data)

            bookings_data = [
                (1, 'PNR-BMB-1001', 2, 1, '2026-11-03 10:15:00', 2, 2500.00, 'PAID', 'CONFIRMED'),
                (2, 'PNR-BMB-1002', 3, 2, '2026-11-04 14:20:00', 1, 850.00, 'PAID', 'CONFIRMED'),
                (3, 'PNR-BMB-1003', 4, 3, '2026-11-02 09:30:00', 2, 3200.00, 'PAID', 'CONFIRMED'),
                (4, 'PNR-BMB-1004', 5, 1, '2026-11-04 18:45:00', 1, 1250.00, 'PAID', 'CONFIRMED'),
                (5, 'PNR-BMB-1005', 6, 4, '2026-11-05 08:00:00', 1, 1150.00, 'PAID', 'CONFIRMED'),
                (6, 'PNR-BMB-1006', 2, 3, '2026-11-01 11:10:00', 1, 1600.00, 'REFUNDED', 'CANCELLED')
            ]
            cur.executemany("INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);", bookings_data)

            passengers_data = [
                (1, 1, 3, 'Rohit Sharma', 34, 'Male'),
                (2, 1, 4, 'Ritika Sharma', 31, 'Female'),
                (3, 2, 12, 'Priya Patel', 28, 'Female'),
                (4, 3, 7, 'Aditya Verma', 25, 'Male'),
                (5, 3, 8, 'Neha Verma', 24, 'Female'),
                (6, 4, 15, 'Sneha Kulkarni', 29, 'Female'),
                (7, 5, 9, 'Rahul Nair', 30, 'Male'),
                (8, 6, 18, 'Rohit Sharma', 34, 'Male')
            ]
            cur.executemany("INSERT INTO booking_passengers VALUES (?, ?, ?, ?, ?, ?);", passengers_data)

            conn.commit()

        print("[DB Init] Setup successfully completed!")
    finally:
        conn.close()


# ============================================================================
# DOMAIN QUERY HELPERS
# ============================================================================

def get_distinct_cities() -> List[str]:
    """Retrieve all available source and destination cities."""
    sources = query_db("SELECT DISTINCT source_city as city FROM routes;")
    destinations = query_db("SELECT DISTINCT destination_city as city FROM routes;")
    cities = set()
    for row in (sources or []):
        cities.add(row["city"])
    for row in (destinations or []):
        cities.add(row["city"])
    return sorted(list(cities))


def search_trips(source: Optional[str] = None, destination: Optional[str] = None, travel_date: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search available scheduled bus trips matching filters."""
    sql = """
    SELECT 
        t.trip_id,
        t.trip_date,
        t.departure_time,
        t.arrival_time,
        t.fare,
        t.status,
        b.bus_id,
        b.bus_number,
        b.operator_name,
        b.bus_type,
        b.total_seats,
        b.amenities,
        b.rating,
        r.source_city,
        r.destination_city,
        r.distance_km,
        r.estimated_duration_hours,
        (b.total_seats - COALESCE((
            SELECT SUM(bp_count.cnt)
            FROM (
                SELECT COUNT(bp.ticket_id) AS cnt
                FROM bookings bk
                JOIN booking_passengers bp ON bk.booking_id = bp.booking_id
                WHERE bk.trip_id = t.trip_id AND bk.booking_status = 'CONFIRMED'
            ) bp_count
        ), 0)) AS available_seats
    FROM trips t
    JOIN buses b ON t.bus_id = b.bus_id
    JOIN routes r ON t.route_id = r.route_id
    WHERE t.status = 'SCHEDULED'
    """
    params = []
    if source:
        sql += " AND LOWER(r.source_city) = LOWER(?)"
        params.append(source)
    if destination:
        sql += " AND LOWER(r.destination_city) = LOWER(?)"
        params.append(destination)
    if travel_date:
        sql += " AND t.trip_date = ?"
        params.append(travel_date)

    sql += " ORDER BY t.trip_date ASC, t.departure_time ASC;"
    return query_db(sql, tuple(params)) or []


def get_trip_details(trip_id: int) -> Optional[Dict[str, Any]]:
    """Fetch complete details of a specific scheduled trip."""
    sql = """
    SELECT 
        t.trip_id,
        t.trip_date,
        t.departure_time,
        t.arrival_time,
        t.fare,
        t.status,
        b.bus_id,
        b.bus_number,
        b.operator_name,
        b.bus_type,
        b.total_seats,
        b.amenities,
        b.rating,
        r.source_city,
        r.destination_city,
        r.distance_km,
        r.estimated_duration_hours
    FROM trips t
    JOIN buses b ON t.bus_id = b.bus_id
    JOIN routes r ON t.route_id = r.route_id
    WHERE t.trip_id = ?;
    """
    return query_db(sql, (trip_id,), one=True)


def get_trip_booked_seats(trip_id: int) -> List[int]:
    """Retrieve seat numbers that are already reserved for this trip."""
    sql = """
    SELECT bp.seat_number
    FROM bookings bk
    JOIN booking_passengers bp ON bk.booking_id = bp.booking_id
    WHERE bk.trip_id = ? AND bk.booking_status = 'CONFIRMED';
    """
    rows = query_db(sql, (trip_id,)) or []
    return [row["seat_number"] for row in rows]


def create_reservation(user_id: int, trip_id: int, passengers: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    ACID Transaction:
    1. Verify trip exists and seats are not already booked.
    2. Generate unique PNR.
    3. Calculate total amount.
    4. Insert into bookings table.
    5. Insert into booking_passengers table.
    """
    trip = get_trip_details(trip_id)
    if not trip:
        raise ValueError("Trip not found.")

    booked_seats = set(get_trip_booked_seats(trip_id))
    requested_seats = [p["seat_number"] for p in passengers]

    for s in requested_seats:
        if s in booked_seats:
            raise ValueError(f"Seat number {s} has already been booked. Please choose another seat.")
        if s < 1 or s > trip["total_seats"]:
            raise ValueError(f"Seat number {s} is invalid for this bus capacity ({trip['total_seats']}).")

    if len(requested_seats) != len(set(requested_seats)):
        raise ValueError("Duplicate seat numbers in passenger list.")

    # Generate PNR: PNR-BMB-XXXX
    rand_code = ''.join(random.choices(string.digits, k=4))
    pnr = f"PNR-BMB-{rand_code}"

    # Calculate total
    total_amount = float(trip["fare"]) * len(passengers)

    conn, db_type = get_connection()
    try:
        cur = conn.cursor()
        
        # Insert Booking
        if db_type == "postgres":
            cur.execute("""
                INSERT INTO bookings (pnr_number, user_id, trip_id, total_seats, total_amount, payment_status, booking_status)
                VALUES (%s, %s, %s, %s, %s, 'PAID', 'CONFIRMED')
                RETURNING booking_id;
            """, (pnr, user_id, trip_id, len(passengers), total_amount))
            booking_id = cur.fetchone()[0]
            
            for p in passengers:
                cur.execute("""
                    INSERT INTO booking_passengers (booking_id, seat_number, passenger_name, passenger_age, passenger_gender)
                    VALUES (%s, %s, %s, %s, %s);
                """, (booking_id, p["seat_number"], p["name"], p["age"], p["gender"]))
        else:
            cur.execute("""
                INSERT INTO bookings (pnr_number, user_id, trip_id, total_seats, total_amount, payment_status, booking_status)
                VALUES (?, ?, ?, ?, ?, 'PAID', 'CONFIRMED');
            """, (pnr, user_id, trip_id, len(passengers), total_amount))
            booking_id = cur.lastrowid
            
            for p in passengers:
                cur.execute("""
                    INSERT INTO booking_passengers (booking_id, seat_number, passenger_name, passenger_age, passenger_gender)
                    VALUES (?, ?, ?, ?, ?);
                """, (booking_id, p["seat_number"], p["name"], p["age"], p["gender"]))

        conn.commit()
        return {
            "booking_id": booking_id,
            "pnr": pnr,
            "total_amount": total_amount,
            "total_seats": len(passengers),
            "status": "CONFIRMED"
        }
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def get_booking_by_pnr(pnr: str) -> Optional[Dict[str, Any]]:
    """Retrieve full booking receipt including trip and passenger list."""
    booking_sql = """
    SELECT 
        bk.booking_id,
        bk.pnr_number,
        bk.booking_timestamp,
        bk.total_seats,
        bk.total_amount,
        bk.payment_status,
        bk.booking_status,
        u.user_id,
        u.full_name AS customer_name,
        u.email AS customer_email,
        u.phone AS customer_phone,
        t.trip_id,
        t.trip_date,
        t.departure_time,
        t.arrival_time,
        t.fare,
        r.source_city,
        r.destination_city,
        r.distance_km,
        r.estimated_duration_hours,
        b.bus_number,
        b.operator_name,
        b.bus_type
    FROM bookings bk
    JOIN users u ON bk.user_id = u.user_id
    JOIN trips t ON bk.trip_id = t.trip_id
    JOIN routes r ON t.route_id = r.route_id
    JOIN buses b ON t.bus_id = b.bus_id
    WHERE bk.pnr_number = ?;
    """
    booking = query_db(booking_sql, (pnr,), one=True)
    if not booking:
        return None

    passengers_sql = """
    SELECT ticket_id, seat_number, passenger_name, passenger_age, passenger_gender
    FROM booking_passengers
    WHERE booking_id = ?
    ORDER BY seat_number ASC;
    """
    passengers = query_db(passengers_sql, (booking["booking_id"],)) or []
    booking["passengers"] = passengers
    return booking


def cancel_booking(pnr: str) -> bool:
    """Cancel booking and refund amount, immediately freeing up allocated seats."""
    booking = query_db("SELECT booking_id, booking_status FROM bookings WHERE pnr_number = ?;", (pnr,), one=True)
    if not booking:
        raise ValueError("Booking with this PNR does not exist.")
    if booking["booking_status"] == "CANCELLED":
        raise ValueError("This booking has already been cancelled.")

    rows = query_db(
        "UPDATE bookings SET booking_status = 'CANCELLED', payment_status = 'REFUNDED' WHERE pnr_number = ?;",
        (pnr,),
        commit=True
    )
    return bool(rows)


def get_all_bookings() -> List[Dict[str, Any]]:
    """Retrieve all bookings for admin management."""
    return query_db("SELECT * FROM vw_booking_summary ORDER BY booking_timestamp DESC;") or []


def get_admin_analytics() -> Dict[str, Any]:
    """Calculate key administrative reports & summaries using aggregate SQL functions."""
    metrics_sql = """
    SELECT 
        COUNT(booking_id) AS total_bookings,
        COALESCE(SUM(CASE WHEN booking_status = 'CONFIRMED' THEN total_amount ELSE 0 END), 0) AS total_revenue,
        COALESCE(SUM(CASE WHEN booking_status = 'CONFIRMED' THEN total_seats ELSE 0 END), 0) AS total_passengers,
        COALESCE(SUM(CASE WHEN booking_status = 'CANCELLED' THEN 1 ELSE 0 END), 0) AS cancelled_bookings
    FROM bookings;
    """
    metrics = query_db(metrics_sql, one=True) or {}

    fleet_sql = """
    SELECT 
        COUNT(bus_id) AS total_buses,
        AVG(rating) AS average_fleet_rating
    FROM buses;
    """
    fleet = query_db(fleet_sql, one=True) or {}

    route_revenue_sql = "SELECT * FROM vw_route_revenue ORDER BY total_revenue DESC LIMIT 5;"
    top_routes = query_db(route_revenue_sql) or []

    bus_occupancy_sql = """
    SELECT 
        b.bus_number,
        b.operator_name,
        b.bus_type,
        b.total_seats,
        COUNT(DISTINCT t.trip_id) as trips_count,
        COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_seats ELSE 0 END), 0) as seats_booked,
        ROUND(
            (COALESCE(SUM(CASE WHEN bk.booking_status = 'CONFIRMED' THEN bk.total_seats ELSE 0 END), 0) * 100.0) / 
            NULLIF((COUNT(DISTINCT t.trip_id) * b.total_seats), 0), 1
        ) as occupancy_percentage
    FROM buses b
    LEFT JOIN trips t ON b.bus_id = t.bus_id
    LEFT JOIN bookings bk ON t.trip_id = bk.trip_id
    GROUP BY b.bus_id, b.bus_number, b.operator_name, b.bus_type, b.total_seats
    ORDER BY occupancy_percentage DESC;
    """
    occupancy = query_db(bus_occupancy_sql) or []

    return {
        "metrics": metrics,
        "fleet": fleet,
        "top_routes": top_routes,
        "occupancy": occupancy
    }


def execute_raw_sql(sql_query: str) -> Dict[str, Any]:
    """Execute arbitrary SQL query for the DBS SQL Lab demonstration."""
    conn, db_type = get_connection()
    try:
        cur = conn.cursor()
        cleaned_sql = sql_query.strip()
        
        # Check if DDL / DML or SELECT
        is_select = cleaned_sql.lower().startswith(("select", "with", "explain", "pragma"))
        
        start_time = datetime.now()
        cur.execute(cleaned_sql)
        duration_ms = round((datetime.now() - start_time).total_seconds() * 1000, 2)
        
        if is_select and cur.description:
            columns = [desc[0] for desc in cur.description]
            rows = [dict(zip(columns, row)) if not isinstance(row, dict) else dict(row) for row in cur.fetchall()]
            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count": len(rows),
                "duration_ms": duration_ms,
                "db_engine": db_type.upper()
            }
        else:
            conn.commit()
            return {
                "success": True,
                "columns": ["Result"],
                "rows": [{"Result": f"Statement executed successfully. Affected rows: {cur.rowcount}"}],
                "row_count": cur.rowcount,
                "duration_ms": duration_ms,
                "db_engine": db_type.upper()
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "columns": [],
            "rows": [],
            "row_count": 0,
            "db_engine": db_type.upper()
        }
    finally:
        conn.close()
