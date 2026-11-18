# Network Anomaly Detection

A small network-traffic anomaly detection demo built with Flask and scikit-learn. It uses the KDD Cup 99 10% dataset and an Isolation Forest.

## Run it

1. Create and activate a virtual environment.
2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Put the headerless KDD Cup 99 10% CSV at `data/kddcup.data_10_percent.csv`.
4. Train the model and see the held-out evaluation:

   ```bash
   python model.py
   ```

5. Start the dashboard:

   ```bash
   python app.py
   ```

6. Open <http://127.0.0.1:5000>.

The dataset and model are kept separate: the CSV is not committed, while `model.pkl` is the trained pipeline used by the app. Re-run `python model.py` after changing the dataset or training code.

## How the model works

1. Repeated feature rows are removed so identical records cannot appear in both the training and holdout sets. The unique rows are then split before fitting.
2. The pipeline one-hot encodes the three categorical fields and passes through numeric fields.
3. Isolation Forest is fit only on normal records from the training split. It flags records that are easier to isolate from that normal baseline.
4. Precision, recall, F1, and a confusion matrix are printed for the labeled holdout set. The holdout labels are used for evaluation, not for fitting the detector.

For an interview explanation: “I treated this as an unsupervised anomaly detection problem. I trained Isolation Forest on normal network traffic, encoded categorical fields with one-hot encoding, and evaluated the anomaly predictions on a separate labeled holdout set using precision, recall, and F1.”

## API

Send one record to `POST /api/detect`:

```json
{
  "features": {
    "protocol_type": "tcp",
    "service": "http",
    "flag": "SF",
    "src_bytes": 181,
    "dst_bytes": 5450
  }
}
```

Unspecified numeric features default to zero and unspecified categories are treated as unknown. The dashboard also offers synthetic normal-like and anomaly-like traffic examples.

## Limitations

KDD Cup 99 is an old benchmark dataset, so these results do not establish performance on modern network traffic. The dashboard is a demonstration and does not collect or analyze live network packets. The Isolation Forest threshold is automatic, so the false-positive rate should be tuned against the needs of a real deployment.
