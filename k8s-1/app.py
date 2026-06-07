import os
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Fetch API configuration
NASA_API_URL = "https://api.nasa.gov/planetary/apod"
NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

@app.route("/")
def index():
    apod_data = None
    error_message = None
    
    # Calculate dates
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    yesterday_str = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Get target date from query parameters (falls back to today)
    target_date = request.args.get("date")
    
    params = {"api_key": NASA_API_KEY}
    if target_date:
        params["date"] = target_date
    
    try:
        logger.info(f"Fetching photo from NASA APOD API (date: {target_date or 'today'})...")
        response = requests.get(
            NASA_API_URL, 
            params=params, 
            timeout=10
        )
        
        if response.status_code == 200:
            apod_data = response.json()
            logger.info("Successfully fetched NASA APOD data")
        else:
            logger.error(f"NASA API returned status code {response.status_code}: {response.text}")
            error_message = f"Failed to retrieve data from NASA. Status code: {response.status_code}"
            
    except requests.exceptions.RequestException as e:
        logger.exception("Network error while connecting to NASA APOD API")
        error_message = f"Unable to reach NASA APOD API. Error details: {str(e)}"
    except Exception as e:
        logger.exception("Unexpected error occurred")
        error_message = f"An unexpected error occurred: {str(e)}"

    return render_template(
        "index.html", 
        apod=apod_data, 
        error=error_message,
        today=today_str,
        yesterday=yesterday_str,
        current_date=target_date or today_str
    )

@app.route("/healthz")
def healthz():
    """Health check endpoint for Kubernetes liveness/readiness probes."""
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
