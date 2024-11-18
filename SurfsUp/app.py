from flask import Flask, jsonify
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from datetime import datetime, timedelta


# Create engine and reflect the database
engine = create_engine("sqlite:///hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

# Save references to tables
Measurements = Base.classes.measurements
Stations = Base.classes.stations

# Create Flask app
app = Flask(__name__)

# Home route
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end><br/>"
    )

# Precipitation route
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data."""
    session = Session(engine)
    
    # Find the most recent date
    most_recent_date = session.query(func.max(Measurements.date)).scalar()
    most_recent_date = datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - timedelta(days=365)
    
    # Query precipitation data
    results = (
        session.query(Measurements.date, Measurements.prcp)
        .filter(Measurements.date >= one_year_ago)
        .all()
    )
    session.close()
    
    # Convert results to dictionary
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)

# Stations route
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    session = Session(engine)
    
    # Query all stations
    results = session.query(Stations.station).all()
    session.close()
    
    # Convert results to a list
    stations_list = [station[0] for station in results]
    return jsonify(stations_list)

# TOBS route
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station in the last 12 months."""
    session = Session(engine)
    
    # Find the most active station
    most_active_station_id = (
        session.query(Measurements.station)
        .group_by(Measurements.station)
        .order_by(func.count(Measurements.station).desc())
        .first()[0]
    )
    
    # Find the most recent date
    most_recent_date = session.query(func.max(Measurements.date)).scalar()
    most_recent_date = datetime.strptime(most_recent_date, "%Y-%m-%d")
    one_year_ago = most_recent_date - timedelta(days=365)
    
    # Query temperature data
    results = (
        session.query(Measurements.date, Measurements.tobs)
        .filter(Measurements.station == most_active_station_id)
        .filter(Measurements.date >= one_year_ago)
        .all()
    )
    session.close()
    
    # Convert results to list of dictionaries
    temperature_data = [{"date": date, "temperature": tobs} for date, tobs in results]
    return jsonify(temperature_data)

# Start and Start-End Range route
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def stats(start=None, end=None):
    """Return TMIN, TAVG, and TMAX for the given start or start-end range."""
    session = Session(engine)
    
    # Query to calculate stats
    if not end:
        results = session.query(
            func.min(Measurements.tobs),
            func.avg(Measurements.tobs),
            func.max(Measurements.tobs),
        ).filter(Measurements.date >= start).all()
    else:
        results = session.query(
            func.min(Measurements.tobs),
            func.avg(Measurements.tobs),
            func.max(Measurements.tobs),
        ).filter(Measurements.date >= start).filter(Measurements.date <= end).all()
    
    session.close()
    
    # Convert results to dictionary
    temp_stats = {
        "TMIN": results[0][0],
        "TAVG": results[0][1],
        "TMAX": results[0][2],
    }
    return jsonify(temp_stats)

# Run the app
if __name__ == "__main__":
    app.run(debug=True)