from datetime import datetime as dt, timedelta
import numpy as mean
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from flask import Flask, jsonify


#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")
conn = engine.connect()

station_df = pd.DataFrame(conn.execute('SELECT station, name, latitude, longitude, elevation FROM stations').fetchall())
station_df.columns=['stations','name', 'latitude', 'longitude', 'elevation']
station_df

prcp_df = pd.DataFrame(
   conn.execute('SELECT date, station, prcp \
                FROM measurements \
                WHERE date >= \'2016-08-23\' \
                GROUP BY date, station').fetchall()
)
prcp_df.columns = ['date', 'station', 'prcp']
prcp_df

temperature_data = pd.read_sql('measurements', conn, parse_dates={'date': {'format': '%Y-%m-%d'}}, columns=['date', 'tobs'])
temperature_data.head()

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
Base.classes.keys()
# Save reference to the table
Stations = Base.classes.stations
Measurements = Base.classes.measurements

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
# 0. Create app
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

# 0. Initialize home page
@app.route('/api/v1.0/home')
def Home():
    return (
        f"Welcome to Hawaii Temperatures API!<br/>"
        f"<br/>"
        f"Available Routes:<br/>"
        f"<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start<br/>"
        f"/api/v1.0/start/end"
        )

# 1. precipitation
@app.route('/api/v1.0/precipitation')
def Precipitation():
    precipitation = prcp_df[['date', 'prcp']]
    precipitation_table = []
    for i in range(precipitation.shape[0]):
        dic = {}
        dic['date'] = precipitation.date[i]
        dic['prcp'] = int(precipitation.prcp[i])
        precipitation_table.append(dic)
        
    return jsonify(precipitation_table)

# 2. Station
@app.route('/api/v1.0/stations')
def Station():
    results = session.query(Stations).all()
    
    stations = [entry.station for entry in results]
    names = [entry.name for entry in results]
    latitudes = [entry.latitude for entry in results]
    longitudes = [entry.longitude for entry in results]
    elevations = [entry.elevation for entry in results]
    
    response = [{"Station": station,
                 "Name": name,
                 "Latitude": lat,
                 "Longitude": lon,
                 "Elevation": elev}
        
                for station, name, lat, lon, elev
                in zip(stations, names, latitudes, longitudes, elevations)]

    return jsonify(response)

# 3. Tobs
@app.route('/api/v1.0/tobs')
def Tobs():
    
    final_date_str = session.query(Measurements).order_by(Measurements.date.desc()).first().date
    final_date = dt.strptime(final_date_str, "%Y-%m-%d")
    initial_date = dt.strptime(f"{final_date.year - 1}-{final_date.month}-{final_date.day}", "%Y-%m-%d")
    
    query = session.query(Measurements).order_by(Measurements.date) \
                       .filter(Measurements.date > initial_date).all()
    
    dates = [entry.date for entry in query]
    tobs = [entry.tobs for entry in query]
    
    response = [{"Date": date,
                 "Temperature": temp}
    
                for date, temp
                in zip(dates, tobs)]
    
    return jsonify(response)
    
# 4. Temperature
@app.route('/api/v1.0/<start>')
def tobs_start(start):
    def calc_temps(start_date):
        df = temperature_data[temperature_data.date >= start_date]
        dic = {}
        dic['min'] = df.tobs.min()
        dic['avg'] = df.tobs.mean()
        dic['max'] = df.tobs.max()
        return(dic)
    temps = calc_temps(start)
    results = {}
    results['TMIN'] = float(temps['min'])
    results['TAVG'] = float(temps['avg'])
    results['TMAX'] = float(temps['max'])
    
    return jsonify(results)

# Date entry must be in YYYY-MM-DD, YYYY-MM-DD in order to work
@app.route('/api/v1.0/<start>/<end>')
def show_start_end(start, end):
    def calc_temps(start_date, end_date):
        df = temperature_data[(temperature_data.date >= start_date) & (temperature_data.date <= end_date)]
        dic = {}
        dic['min'] = df.tobs.min()
        dic['avg'] = df.tobs.mean()
        dic['max'] = df.tobs.max()
        return(dic)
    temps = calc_temps(start, end)
    results = {}
    results['TMIN'] = float(temps['min'])
    results['TAVG'] = float(temps['avg'])
    results['TMAX'] = float(temps['max'])
    return jsonify(results)

# 5. Run App
if __name__ == '__main__':
    app.run(port = 5000, debug=True)