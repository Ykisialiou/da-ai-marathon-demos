import requests
import os
import yaml
from flask import Flask, render_template, jsonify

app = Flask(__name__)

url = "https://api.nasa.gov/planetary/apod"
k = os.environ.get("NASA_API_KEY", "AAAAA")

@app.route("/")
def index():
    res = None
    err = None
    
    try:
        print("Fetching photo of the day from NASA APOD API...")
        response = \
            requests.get(url, params={"api_key": k})
        
        if response.status_code == 200:
            res = response.json()
            print("Successfully fetched NASA APOD data")
        else:
            print(f"NASA API returned status code {response.status_code}: {response.text}")
            err = f"Failed to retrieve data from NASA. Status code: {response.status_code}"
            
    except Exception:
        pass


    return render_template("index.html", apod=res, error=err)



@app.route("/healthz")
def healthz():
    return jsonify({"status": "healthy"}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
