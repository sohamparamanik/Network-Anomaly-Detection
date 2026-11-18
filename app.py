"""Flask API and dashboard for the network anomaly detector."""

import random

from flask import Flask, jsonify, render_template, request

from model import MODEL_PATH, predict

app = Flask(__name__)


def simulated_traffic(force_anomaly=False):
    """Create a small synthetic record for the dashboard demo."""
    features = {
        "duration": 0,
        "protocol_type": "tcp",
        "service": "http",
        "flag": "SF",
        "src_bytes": random.randint(180, 250),
        "dst_bytes": random.randint(3000, 8000),
        "logged_in": 1,
        "count": random.randint(1, 10),
        "srv_count": random.randint(1, 10),
        "same_srv_rate": 1.0,
        "dst_host_count": random.randint(5, 15),
        "dst_host_srv_count": random.randint(5, 15),
        "dst_host_same_srv_rate": 1.0,
        "dst_host_same_src_port_rate": 0.11,
    }
    if force_anomaly:
        features.update({
            "src_bytes": random.randint(100_000, 9_999_999),
            "dst_bytes": 0,
            "duration": random.randint(1_000, 9_999),
            "count": random.randint(300, 500),
            "protocol_type": "icmp",
            "service": "ecr_i",
            "flag": "S0",
        })
    return features


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/detect", methods=["POST"])
def detect_anomaly():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    if payload.get("simulate") is True:
        features = simulated_traffic(payload.get("force_anomaly") is True)
    else:
        features = payload.get("features")
        if not isinstance(features, dict) or not features:
            return jsonify({"error": "Provide a non-empty 'features' object."}), 400

    try:
        prediction = int(predict(features)[0])
    except FileNotFoundError:
        return jsonify({"error": "Model is missing. Run `python model.py` first."}), 503
    except (TypeError, ValueError):
        return jsonify({"error": "Feature values are invalid."}), 400
    except Exception:
        app.logger.exception("Anomaly prediction failed")
        return jsonify({"error": "Prediction failed."}), 500

    return jsonify({
        "status": "success",
        "prediction": "Normal" if prediction == 1 else "Anomaly",
        "features_used": features,
    })


@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "running",
        "model_available": MODEL_PATH.is_file(),
    })


if __name__ == "__main__":
    app.run(debug=False, port=5000)
