-- ============================================================================
-- BUS RESERVATION SYSTEM - RELATIONAL DATABASE SCHEMA (PostgreSQL)
-- Course: Database Systems (DBS Project)
-- Normalization: 3NF Compliant
-- Features: PKs, FKs, NOT NULL, UNIQUE, CHECK constraints, Indexes, Views
-- ============================================================================

-- 1. DROP EXISTING TABLES & VIEWS (Clean Setup)
DROP VIEW IF EXISTS vw_route_revenue CASCADE;
DROP VIEW IF EXISTS vw_booking_summary CASCADE;
DROP VIEW IF EXISTS vw_trip_schedule CASCADE;
DROP TABLE IF EXISTS booking_passengers CASCADE;
DROP TABLE IF EXISTS bookings CASCADE;
DROP TABLE IF EXISTS trips CASCADE;
DROP TABLE IF EXISTS routes CASCADE;
DROP TABLE IF EXISTS buses CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 2. USERS TABLE (Passengers and Administrators)
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(120) NOT NULL UNIQUE,
    phone VARCHAR(20) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'PASSENGER' 
        CHECK (role IN ('PASSENGER', 'ADMIN')),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. BUSES TABLE (Fleet Management)
CREATE TABLE buses (
    bus_id SERIAL PRIMARY KEY,
    bus_number VARCHAR(30) NOT NULL UNIQUE,
    operator_name VARCHAR(100) NOT NULL,
    bus_type VARCHAR(40) NOT NULL 
        CHECK (bus_type IN ('AC Sleeper (2+1)', 'AC Seater (2+2)', 'Volvo Multi-Axle', 'Non-AC Seater (2+2)')),
    total_seats INTEGER NOT NULL 
        CHECK (total_seats > 0 AND total_seats <= 60),
    amenities TEXT DEFAULT 'WiFi, Charging Port, Water Bottle, Blanket',
    rating NUMERIC(2,1) DEFAULT 4.5 
        CHECK (rating >= 1.0 AND rating <= 5.0)
);

-- 4. ROUTES TABLE (City-to-City Connectivity)
CREATE TABLE routes (
    route_id SERIAL PRIMARY KEY,
    source_city VARCHAR(80) NOT NULL,
    destination_city VARCHAR(80) NOT NULL,
    distance_km NUMERIC(6,1) NOT NULL 
        CHECK (distance_km > 0),
    estimated_duration_hours NUMERIC(4,1) NOT NULL 
        CHECK (estimated_duration_hours > 0),
    CONSTRAINT uq_route_pair UNIQUE (source_city, destination_city),
    CONSTRAINT chk_different_cities CHECK (source_city <> destination_city)
);

-- 5. TRIPS TABLE (Scheduled Bus Journeys)
CREATE TABLE trips (
    trip_id SERIAL PRIMARY KEY,
    bus_id INTEGER NOT NULL REFERENCES buses(bus_id) ON DELETE CASCADE,
    route_id INTEGER NOT NULL REFERENCES routes(route_id) ON DELETE CASCADE,
    trip_date DATE NOT NULL,
    departure_time TIME NOT NULL,
    arrival_time TIME NOT NULL,
    fare NUMERIC(8,2) NOT NULL 
        CHECK (fare > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'SCHEDULED' 
        CHECK (status IN ('SCHEDULED', 'COMPLETED', 'CANCELLED'))
);

-- 6. BOOKINGS TABLE (Reservation Master Record)
CREATE TABLE bookings (
    booking_id SERIAL PRIMARY KEY,
    pnr_number VARCHAR(20) NOT NULL UNIQUE,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    trip_id INTEGER NOT NULL REFERENCES trips(trip_id) ON DELETE RESTRICT,
    booking_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    total_seats INTEGER NOT NULL 
        CHECK (total_seats > 0),
    total_amount NUMERIC(10,2) NOT NULL 
        CHECK (total_amount >= 0),
    payment_status VARCHAR(20) NOT NULL DEFAULT 'PAID' 
        CHECK (payment_status IN ('PAID', 'REFUNDED')),
    booking_status VARCHAR(20) NOT NULL DEFAULT 'CONFIRMED' 
        CHECK (booking_status IN ('CONFIRMED', 'CANCELLED'))
);

-- 7. BOOKING_PASSENGERS TABLE (Seat Allocation & Passenger Manifest)
CREATE TABLE booking_passengers (
    ticket_id SERIAL PRIMARY KEY,
    booking_id INTEGER NOT NULL REFERENCES bookings(booking_id) ON DELETE CASCADE,
    seat_number INTEGER NOT NULL 
        CHECK (seat_number > 0 AND seat_number <= 60),
    passenger_name VARCHAR(100) NOT NULL,
    passenger_age INTEGER NOT NULL 
        CHECK (passenger_age >= 1 AND passenger_age <= 120),
    passenger_gender VARCHAR(15) NOT NULL 
        CHECK (passenger_gender IN ('Male', 'Female', 'Other')),
    CONSTRAINT uq_booking_seat UNIQUE (booking_id, seat_number)
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================
CREATE INDEX idx_trips_search ON trips(route_id, trip_date, status);
CREATE INDEX idx_bookings_pnr ON bookings(pnr_number);
CREATE INDEX idx_bookings_user ON bookings(user_id);
CREATE INDEX idx_seats_booking ON booking_passengers(booking_id);

-- ============================================================================
-- RELATIONAL VIEWS (As required by DBS Project syllabus)
-- ============================================================================

-- View 1: Complete Trip Schedule Details (Multi-Table Join)
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

-- View 2: Comprehensive Booking Summary (Joins with Passengers & Users)
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

-- View 3: Route Revenue & Performance (GROUP BY + Aggregation)
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
