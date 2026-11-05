-- ============================================================================
-- BUS RESERVATION SYSTEM - DEMONSTRATION SQL QUERIES
-- Course: Database Systems (DBS Project - Section 11 & Section 15)
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. SELECT & FILTERING USING WHERE
-- Retrieve all scheduled trips departing from 'Bangalore' with fare below 1300
-- ----------------------------------------------------------------------------
SELECT 
    t.trip_id,
    r.source_city,
    r.destination_city,
    t.trip_date,
    t.departure_time,
    t.fare,
    b.operator_name,
    b.bus_type
FROM trips t
INNER JOIN routes r ON t.route_id = r.route_id
INNER JOIN buses b ON t.bus_id = b.bus_id
WHERE r.source_city = 'Bangalore' 
  AND t.fare <= 1300.00
  AND t.status = 'SCHEDULED';

-- ----------------------------------------------------------------------------
-- 2. SORTING USING ORDER BY
-- List all buses sorted by customer rating in descending order, then capacity
-- ----------------------------------------------------------------------------
SELECT 
    bus_id,
    bus_number,
    operator_name,
    bus_type,
    total_seats,
    rating
FROM buses
ORDER BY rating DESC, total_seats ASC;

-- ----------------------------------------------------------------------------
-- 3. AGGREGATE FUNCTIONS (COUNT, SUM, AVG, MIN, MAX)
-- Calculate key metrics: total revenue, average fare, min/max fare, confirmed bookings
-- ----------------------------------------------------------------------------
SELECT 
    COUNT(booking_id) AS total_bookings_count,
    SUM(total_amount) AS gross_sales_amount,
    AVG(total_amount) AS average_ticket_amount,
    MIN(total_amount) AS minimum_ticket_paid,
    MAX(total_amount) AS maximum_ticket_paid
FROM bookings
WHERE booking_status = 'CONFIRMED';

-- ----------------------------------------------------------------------------
-- 4. GROUP BY & HAVING
-- Find routes that have generated more than 1000 in confirmed revenue
-- ----------------------------------------------------------------------------
SELECT 
    r.source_city || ' -> ' || r.destination_city AS route_name,
    COUNT(bk.booking_id) AS total_bookings,
    SUM(bk.total_seats) AS total_passengers,
    SUM(bk.total_amount) AS total_route_revenue
FROM routes r
INNER JOIN trips t ON r.route_id = t.route_id
INNER JOIN bookings bk ON t.trip_id = bk.trip_id
WHERE bk.booking_status = 'CONFIRMED'
GROUP BY r.source_city, r.destination_city
HAVING SUM(bk.total_amount) >= 1000.00
ORDER BY total_route_revenue DESC;

-- ----------------------------------------------------------------------------
-- 5. MULTI-TABLE JOINS (INNER & LEFT JOIN)
-- Retrieve passenger manifest with user details, trip timing, and seat number
-- ----------------------------------------------------------------------------
SELECT 
    bk.pnr_number,
    u.full_name AS booked_by,
    bp.seat_number,
    bp.passenger_name,
    bp.passenger_age,
    bp.passenger_gender,
    r.source_city,
    r.destination_city,
    t.trip_date,
    t.departure_time,
    b.operator_name
FROM bookings bk
INNER JOIN users u ON bk.user_id = u.user_id
INNER JOIN booking_passengers bp ON bk.booking_id = bp.booking_id
INNER JOIN trips t ON bk.trip_id = t.trip_id
INNER JOIN routes r ON t.route_id = r.route_id
INNER JOIN buses b ON t.bus_id = b.bus_id
WHERE bk.booking_status = 'CONFIRMED'
ORDER BY bk.pnr_number, bp.seat_number;

-- ----------------------------------------------------------------------------
-- 6. NESTED SUBQUERY (Uncorrelated & Correlated)
-- Find all buses whose average trip fare is higher than the overall average fare
-- ----------------------------------------------------------------------------
SELECT 
    b.bus_number,
    b.operator_name,
    b.bus_type,
    b.rating
FROM buses b
WHERE b.bus_id IN (
    SELECT t.bus_id
    FROM trips t
    GROUP BY t.bus_id
    HAVING AVG(t.fare) > (SELECT AVG(fare) FROM trips)
);

-- ----------------------------------------------------------------------------
-- 7. SQL VIEW QUERY
-- Query from pre-defined view for fast executive reporting
-- ----------------------------------------------------------------------------
SELECT * FROM vw_route_revenue
ORDER BY total_revenue DESC;

-- ----------------------------------------------------------------------------
-- 8. DATA MANIPULATION (INSERT, UPDATE, DELETE)
-- ----------------------------------------------------------------------------

-- A) INSERT a new booking and passenger seat:
-- INSERT INTO bookings (pnr_number, user_id, trip_id, total_seats, total_amount, payment_status, booking_status)
-- VALUES ('PNR-BMB-9999', 2, 1, 1, 1250.00, 'PAID', 'CONFIRMED');

-- B) UPDATE booking status to CANCELLED and mark refund:
-- UPDATE bookings 
-- SET booking_status = 'CANCELLED', payment_status = 'REFUNDED'
-- WHERE pnr_number = 'PNR-BMB-9999';

-- C) DELETE a cancelled booking passenger allocation (or soft-delete):
-- DELETE FROM booking_passengers 
-- WHERE booking_id = (SELECT booking_id FROM bookings WHERE pnr_number = 'PNR-BMB-9999');
