from flask import Flask
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # exposes /metrics automatically


@app.route("/")
def hello():
    return "Hello from Python Service!Experiment"


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)