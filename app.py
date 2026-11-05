"""
Bus Reservation System - Flask Web Application
Course: Database Systems (DBS Project)
Designed for local execution and Vercel serverless deployment.
"""

import os
from datetime import date, datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dbs-bus-reservation-secret-key-2026")

# Automatically initialize database on startup
with app.app_context():
    try:
        db.init_db()
    except Exception as e:
        print(f"[Startup Warning] DB init error: {e}")


@app.context_processor
def inject_global_data():
    """Inject common attributes to all templates."""
    return {
        "current_year": datetime.now().year,
        "is_postgres": db.IS_POSTGRES,
        "today_date": date.today().isoformat(),
        "tomorrow_date": (date.today() + timedelta(days=1)).isoformat()
    }


# ============================================================================
# USER & PUBLIC ROUTES
# ============================================================================

@app.route("/")
def index():
    """Home page with search form and highlights."""
    cities = db.get_distinct_cities()
    popular_trips = db.search_trips()[:4]
    metrics = db.get_admin_analytics()["metrics"]
    return render_template("index.html", cities=cities, popular_trips=popular_trips, metrics=metrics)


@app.route("/trips")
def trips():
    """Search & filter scheduled bus trips."""
    source = request.args.get("source", "").strip()
    destination = request.args.get("destination", "").strip()
    travel_date = request.args.get("travel_date", "").strip()
    bus_type = request.args.get("bus_type", "").strip()

    cities = db.get_distinct_cities()
    results = db.search_trips(
        source=source if source else None,
        destination=destination if destination else None,
        travel_date=travel_date if travel_date else None
    )

    if bus_type:
        results = [t for t in results if bus_type.lower() in t["bus_type"].lower()]

    return render_template(
        "trips.html",
        trips=results,
        cities=cities,
        source=source,
        destination=destination,
        travel_date=travel_date,
        bus_type=bus_type
    )


@app.route("/book/<int:trip_id>", methods=["GET", "POST"])
def book_seat(trip_id):
    """Interactive seat selection and reservation booking."""
    trip = db.get_trip_details(trip_id)
    if not trip:
        flash("Scheduled trip not found.", "error")
        return redirect(url_for("trips"))

    booked_seats = db.get_trip_booked_seats(trip_id)

    if request.method == "POST":
        try:
            # Current logged in passenger (defaults to Rohit Sharma for student demo)
            user_id = int(request.form.get("user_id", 2))
            seat_numbers_str = request.form.get("selected_seats", "")
            
            if not seat_numbers_str:
                flash("Please select at least one seat from the layout.", "error")
                return redirect(url_for("book_seat", trip_id=trip_id))

            seat_numbers = [int(s) for s in seat_numbers_str.split(",") if s.strip()]
            passengers = []

            for seat in seat_numbers:
                p_name = request.form.get(f"passenger_name_{seat}", "").strip()
                p_age = request.form.get(f"passenger_age_{seat}", "").strip()
                p_gender = request.form.get(f"passenger_gender_{seat}", "Male")

                if not p_name or not p_age:
                    flash(f"Please enter complete details for Seat #{seat}.", "error")
                    return redirect(url_for("book_seat", trip_id=trip_id))

                passengers.append({
                    "seat_number": seat,
                    "name": p_name,
                    "age": int(p_age),
                    "gender": p_gender
                })

            # Execute transactional reservation
            booking_res = db.create_reservation(user_id=user_id, trip_id=trip_id, passengers=passengers)
            flash(f"Booking confirmed successfully! Your PNR is {booking_res['pnr']}", "success")
            return redirect(url_for("confirmation", pnr=booking_res["pnr"]))

        except Exception as e:
            flash(f"Reservation failed: {str(e)}", "error")
            return redirect(url_for("book_seat", trip_id=trip_id))

    return render_template(
        "book.html",
        trip=trip,
        booked_seats=booked_seats,
        total_seats=trip["total_seats"]
    )


@app.route("/confirmation/<pnr>")
def confirmation(pnr):
    """View digital ticket confirmation by PNR."""
    booking = db.get_booking_by_pnr(pnr)
    if not booking:
        flash("PNR record not found.", "error")
        return redirect(url_for("index"))
    return render_template("confirmation.html", booking=booking)


@app.route("/my-bookings")
def my_bookings():
    """Passenger booking history and cancellation portal."""
    search_pnr = request.args.get("pnr", "").strip()
    if search_pnr:
        single_booking = db.get_booking_by_pnr(search_pnr)
        bookings = [single_booking] if single_booking else []
    else:
        # Default user 2 (Rohit Sharma)
        bookings = db.query_db("""
            SELECT * FROM vw_booking_summary 
            WHERE customer_email = 'rohit.sharma@example.com' 
            ORDER BY booking_timestamp DESC;
        """) or []

    return render_template("my_bookings.html", bookings=bookings, search_pnr=search_pnr)


@app.route("/cancel-booking", methods=["POST"])
def cancel_ticket():
    """Cancel booking and process refund."""
    pnr = request.form.get("pnr", "").strip()
    try:
        db.cancel_booking(pnr)
        flash(f"Booking {pnr} has been successfully cancelled and refund initiated.", "success")
    except Exception as e:
        flash(f"Cancellation failed: {str(e)}", "error")
    return redirect(url_for("my_bookings"))


# ============================================================================
# ADMIN & FLEET MANAGEMENT
# ============================================================================

@app.route("/admin")
def admin_dashboard():
    """Admin dashboard for managing buses, routes, and trips."""
    buses = db.query_db("SELECT * FROM buses ORDER BY bus_id ASC;") or []
    routes = db.query_db("SELECT * FROM routes ORDER BY route_id ASC;") or []
    trips = db.query_db("SELECT * FROM vw_trip_schedule ORDER BY trip_date DESC, departure_time ASC;") or []
    bookings = db.get_all_bookings()
    return render_template(
        "admin.html",
        buses=buses,
        routes=routes,
        trips=trips,
        bookings=bookings
    )


@app.route("/admin/bus/add", methods=["POST"])
def admin_add_bus():
    """Add a new bus to the fleet (Demonstrating INSERT operation)."""
    try:
        bus_number = request.form.get("bus_number", "").strip().upper()
        operator_name = request.form.get("operator_name", "").strip()
        bus_type = request.form.get("bus_type", "").strip()
        total_seats = int(request.form.get("total_seats", 40))
        amenities = request.form.get("amenities", "WiFi, Charging Port, Water Bottle")
        rating = float(request.form.get("rating", 4.5))

        db.query_db("""
            INSERT INTO buses (bus_number, operator_name, bus_type, total_seats, amenities, rating)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (bus_number, operator_name, bus_type, total_seats, amenities, rating), commit=True)
        flash(f"Bus '{bus_number}' added successfully to the fleet!", "success")
    except Exception as e:
        flash(f"Error adding bus: {str(e)}", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/route/add", methods=["POST"])
def admin_add_route():
    """Add a new route (Demonstrating INSERT with UNIQUE constraint)."""
    try:
        source_city = request.form.get("source_city", "").strip()
        destination_city = request.form.get("destination_city", "").strip()
        distance_km = float(request.form.get("distance_km", 0))
        duration = float(request.form.get("estimated_duration_hours", 0))

        db.query_db("""
            INSERT INTO routes (source_city, destination_city, distance_km, estimated_duration_hours)
            VALUES (?, ?, ?, ?);
        """, (source_city, destination_city, distance_km, duration), commit=True)
        flash(f"Route '{source_city} -> {destination_city}' created successfully!", "success")
    except Exception as e:
        flash(f"Error creating route: {str(e)}", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/trip/add", methods=["POST"])
def admin_add_trip():
    """Schedule a new trip (Demonstrating INSERT with Foreign Keys)."""
    try:
        bus_id = int(request.form.get("bus_id"))
        route_id = int(request.form.get("route_id"))
        trip_date = request.form.get("trip_date")
        departure_time = request.form.get("departure_time")
        arrival_time = request.form.get("arrival_time")
        fare = float(request.form.get("fare"))

        db.query_db("""
            INSERT INTO trips (bus_id, route_id, trip_date, departure_time, arrival_time, fare, status)
            VALUES (?, ?, ?, ?, ?, ?, 'SCHEDULED');
        """, (bus_id, route_id, trip_date, departure_time, arrival_time, fare), commit=True)
        flash("Trip successfully scheduled!", "success")
    except Exception as e:
        flash(f"Error scheduling trip: {str(e)}", "error")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/reports")
def admin_reports():
    """Comprehensive analytical reports with SQL aggregates and Chart.js."""
    analytics = db.get_admin_analytics()
    return render_template("reports.html", analytics=analytics)


@app.route("/admin/reset-db", methods=["POST"])
def admin_reset_db():
    """Reset database to fresh seed data."""
    try:
        db.init_db(force=True)
        flash("Database has been reset to default realistic seed data!", "success")
    except Exception as e:
        flash(f"Failed to reset database: {str(e)}", "error")
    return redirect(url_for("admin_dashboard"))


# ============================================================================
# DBS SYLLABUS DEMO: SQL LAB & RELATIONAL SCHEMA
# ============================================================================

@app.route("/sql-lab")
def sql_lab():
    """Interactive SQL Query Console & Syllabus Query Demonstrator."""
    tables = [
        {"name": "users", "desc": "Passenger accounts & system administrators"},
        {"name": "buses", "desc": "Fleet details, type, seat capacity & rating"},
        {"name": "routes", "desc": "Source & destination corridors with distances"},
        {"name": "trips", "desc": "Scheduled departures, timing, bus assignment & fare"},
        {"name": "bookings", "desc": "Reservation header with PNR, amounts & status"},
        {"name": "booking_passengers", "desc": "Seat numbers and passenger names manifest"},
        {"name": "vw_trip_schedule", "desc": "Relational view joining trips, buses & routes"},
        {"name": "vw_booking_summary", "desc": "Relational view joining bookings, users & routes"},
        {"name": "vw_route_revenue", "desc": "Aggregated revenue & passenger metrics view"}
    ]
    return render_template("sql_lab.html", tables=tables)


@app.route("/api/execute-sql", methods=["POST"])
def api_execute_sql():
    """API endpoint to run raw SQL query for demonstration."""
    data = request.get_json() or {}
    query_str = data.get("query", "").strip()
    if not query_str:
        return jsonify({"success": False, "error": "Query cannot be empty."})

    res = db.execute_raw_sql(query_str)
    return jsonify(res)


@app.route("/schema")
def schema_viewer():
    """Interactive ER diagram, relational schema, and 3NF normalization notes."""
    schema_path = os.path.join(os.path.dirname(__file__), "database", "schema.sql")
    queries_path = os.path.join(os.path.dirname(__file__), "database", "queries.sql")
    seed_path = os.path.join(os.path.dirname(__file__), "database", "seed.sql")

    schema_sql = open(schema_path, "r", encoding="utf-8").read() if os.path.exists(schema_path) else ""
    queries_sql = open(queries_path, "r", encoding="utf-8").read() if os.path.exists(queries_path) else ""
    seed_sql = open(seed_path, "r", encoding="utf-8").read() if os.path.exists(seed_path) else ""

    return render_template(
        "schema.html",
        schema_sql=schema_sql,
        queries_sql=queries_sql,
        seed_sql=seed_sql
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
