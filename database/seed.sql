-- ============================================================================
-- BUS RESERVATION SYSTEM - REALISTIC SAMPLE SEED DATA
-- Course: Database Systems (DBS Project)
-- ============================================================================

-- 1. INSERT USERS (Administrators and Passengers)
INSERT INTO users (user_id, full_name, email, phone, role) VALUES
(1, 'Admin Controller', 'admin@bookmybus.com', '+91 98765 43210', 'ADMIN'),
(2, 'Rohit Sharma', 'rohit.sharma@example.com', '+91 98450 12345', 'PASSENGER'),
(3, 'Priya Patel', 'priya.patel@example.com', '+91 97312 67890', 'PASSENGER'),
(4, 'Aditya Verma', 'aditya.v@example.com', '+91 99001 54321', 'PASSENGER'),
(5, 'Sneha Kulkarni', 'sneha.k@example.com', '+91 94480 98765', 'PASSENGER'),
(6, 'Rahul Nair', 'rahul.nair@example.com', '+91 91234 56789', 'PASSENGER');

-- 2. INSERT BUSES (Fleet Details)
INSERT INTO buses (bus_id, bus_number, operator_name, bus_type, total_seats, amenities, rating) VALUES
(1, 'KA-01-AB-1234', 'GreenLine Travels', 'AC Sleeper (2+1)', 30, 'WiFi, Charging, Pillow, Blanket, Water Bottle', 4.8),
(2, 'KA-05-MN-5678', 'KSRTC Airavat Club Class', 'Volvo Multi-Axle', 40, 'Reclining Seats, AC, Reading Light, Emergency Hammer', 4.7),
(3, 'MH-02-XY-9012', 'Orange Tours & Travels', 'AC Sleeper (2+1)', 30, 'Personal TV, WiFi, GPS Tracking, Charging Port', 4.6),
(4, 'TS-09-CD-3456', 'VRL Travels', 'Volvo Multi-Axle', 40, 'AC, Charging Port, Blanket, Water Bottle', 4.5),
(5, 'TN-07-EF-7890', 'SRS Express', 'AC Seater (2+2)', 44, 'Pushback Seats, AC, Music, Fire Extinguisher', 4.3),
(6, 'DL-01-GH-2345', 'IntrCity SmartBus', 'AC Sleeper (2+1)', 30, 'Smart Boarding, WiFi, Live CCTV, Restroom on-board', 4.9),
(7, 'GA-03-JK-6789', 'Goa State Shuttle', 'Non-AC Seater (2+2)', 48, 'Comfortable Seating, Luggage Space, FM Radio', 4.1);

-- 3. INSERT ROUTES (Popular Intercity Corridors)
INSERT INTO routes (route_id, source_city, destination_city, distance_km, estimated_duration_hours) VALUES
(1, 'Bangalore', 'Hyderabad', 570.0, 8.5),
(2, 'Hyderabad', 'Bangalore', 570.0, 8.5),
(3, 'Bangalore', 'Chennai', 345.0, 6.0),
(4, 'Chennai', 'Bangalore', 345.0, 6.0),
(5, 'Mumbai', 'Goa', 590.0, 11.0),
(6, 'Goa', 'Mumbai', 590.0, 11.0),
(7, 'Bangalore', 'Goa', 560.0, 10.5),
(8, 'Delhi', 'Jaipur', 280.0, 5.0),
(9, 'Mumbai', 'Pune', 150.0, 3.5),
(10, 'Pune', 'Mumbai', 150.0, 3.5);

-- 4. INSERT TRIPS (Current and Upcoming Schedules)
-- Using dates dynamically around today / static dates
INSERT INTO trips (trip_id, bus_id, route_id, trip_date, departure_time, arrival_time, fare, status) VALUES
(1, 1, 1, CURRENT_DATE, '21:30:00', '06:00:00', 1250.00, 'SCHEDULED'),
(2, 2, 3, CURRENT_DATE, '06:00:00', '12:00:00', 850.00, 'SCHEDULED'),
(3, 3, 5, CURRENT_DATE, '20:00:00', '07:00:00', 1600.00, 'SCHEDULED'),
(4, 4, 1, CURRENT_DATE, '22:15:00', '06:45:00', 1150.00, 'SCHEDULED'),
(5, 5, 3, CURRENT_DATE, '14:30:00', '20:30:00', 650.00, 'SCHEDULED'),
(6, 6, 8, CURRENT_DATE, '07:00:00', '12:00:00', 799.00, 'SCHEDULED'),
(7, 1, 7, CURRENT_DATE + INTERVAL '1 day', '21:00:00', '07:30:00', 1400.00, 'SCHEDULED'),
(8, 2, 4, CURRENT_DATE + INTERVAL '1 day', '13:00:00', '19:00:00', 850.00, 'SCHEDULED'),
(9, 3, 6, CURRENT_DATE + INTERVAL '1 day', '19:30:00', '06:30:00', 1550.00, 'SCHEDULED'),
(10, 4, 2, CURRENT_DATE + INTERVAL '1 day', '22:00:00', '06:30:00', 1200.00, 'SCHEDULED');

-- 5. INSERT BOOKINGS (Historical & Active Bookings)
INSERT INTO bookings (booking_id, pnr_number, user_id, trip_id, booking_timestamp, total_seats, total_amount, payment_status, booking_status) VALUES
(1, 'PNR-BMB-1001', 2, 1, CURRENT_TIMESTAMP - INTERVAL '2 days', 2, 2500.00, 'PAID', 'CONFIRMED'),
(2, 'PNR-BMB-1002', 3, 2, CURRENT_TIMESTAMP - INTERVAL '1 day', 1, 850.00, 'PAID', 'CONFIRMED'),
(3, 'PNR-BMB-1003', 4, 3, CURRENT_TIMESTAMP - INTERVAL '3 days', 2, 3200.00, 'PAID', 'CONFIRMED'),
(4, 'PNR-BMB-1004', 5, 1, CURRENT_TIMESTAMP - INTERVAL '1 day', 1, 1250.00, 'PAID', 'CONFIRMED'),
(5, 'PNR-BMB-1005', 6, 4, CURRENT_TIMESTAMP - INTERVAL '4 hours', 1, 1150.00, 'PAID', 'CONFIRMED'),
(6, 'PNR-BMB-1006', 2, 3, CURRENT_TIMESTAMP - INTERVAL '5 days', 1, 1600.00, 'REFUNDED', 'CANCELLED');

-- 6. INSERT PASSENGER SEAT ALLOCATIONS
INSERT INTO booking_passengers (ticket_id, booking_id, seat_number, passenger_name, passenger_age, passenger_gender) VALUES
(1, 1, 3, 'Rohit Sharma', 34, 'Male'),
(2, 1, 4, 'Ritika Sharma', 31, 'Female'),
(3, 2, 12, 'Priya Patel', 28, 'Female'),
(4, 3, 7, 'Aditya Verma', 25, 'Male'),
(5, 3, 8, 'Neha Verma', 24, 'Female'),
(6, 4, 15, 'Sneha Kulkarni', 29, 'Female'),
(7, 5, 9, 'Rahul Nair', 30, 'Male'),
(8, 6, 18, 'Rohit Sharma', 34, 'Male');
