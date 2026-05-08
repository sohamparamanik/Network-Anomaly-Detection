# Network Anomaly Detection AI

This is a premium Network Anomaly Detection dashboard built with Python, Flask, and an Isolation Forest Machine Learning model. It evaluates network traffic connections to detect deviations and potential "zero-day" attacks.

## Features
- **Real-Time Anomaly Detection**: Uses an Isolation Forest algorithm trained on true "normal" network traffic baselines.
- **Modern Dashboard**: Features a dark glassmorphism aesthetic built with vanilla HTML/CSS/JS.
- **Traffic Simulator**: Simulate normal web requests or anomalous network attacks directly from the UI.

## Setup Instructions

1. **Clone the repository**
2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the Server**:
   ```bash
   python app.py
   ```
5. **Open your browser** and navigate to `http://127.0.0.1:5000`.

## Retraining the Model (Optional)
The pre-trained `.pkl` files are included. If you wish to retrain the model yourself on the KDD Cup dataset:
1. Ensure `kddcup.data_10_percent.csv` is located in the `data/` folder.
2. Run `python model.py`.
