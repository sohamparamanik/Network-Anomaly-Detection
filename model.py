"""Train and use an Isolation Forest for network anomaly detection."""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import IsolationForest
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "kddcup.data_10_percent.csv"
MODEL_PATH = PROJECT_DIR / "model.pkl"
MAX_TRAIN_ROWS = 10_000
RANDOM_STATE = 42

# KDD Cup 99 has 41 input features followed by the attack label.
COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins",
    "logged_in", "num_compromised", "root_shell", "su_attempted", "num_root",
    "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
    "dst_host_serror_rate", "dst_host_srv_serror_rate", "dst_host_rerror_rate",
    "dst_host_srv_rerror_rate", "label",
]
FEATURE_COLUMNS = COLUMNS[:-1]
CATEGORICAL_COLUMNS = ["protocol_type", "service", "flag"]
NUMERIC_COLUMNS = [column for column in FEATURE_COLUMNS if column not in CATEGORICAL_COLUMNS]

_MODEL = None


def _clean_category(value):
    """Remove the byte-string wrappers used in some KDD Cup CSV copies."""
    value = str(value).strip()
    if value.startswith("b'") and value.endswith("'"):
        value = value[2:-1]
    if value.lower() in {"", "nan", "none", "<na>"}:
        return "unknown"
    return value


def load_data(file_path=DATA_PATH):
    """Load the headerless KDD Cup CSV and normalize its labels and features."""
    data = pd.read_csv(file_path, header=None, names=COLUMNS)
    if data.empty:
        raise ValueError(f"Dataset is empty: {file_path}")

    for column in CATEGORICAL_COLUMNS:
        data[column] = data[column].map(_clean_category)

    for column in NUMERIC_COLUMNS:
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)

    labels = data["label"].astype(str).str.strip()
    labels = labels.str.replace(r"^b'(.*)'$", r"\1", regex=True)
    data["label"] = labels.str.rstrip(".").str.lower()
    return data


def build_model():
    """Create a preprocessing and anomaly-detection pipeline."""
    preprocessing = ColumnTransformer(
        transformers=[
            ("categories", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_COLUMNS),
        ],
        remainder="passthrough",
        sparse_threshold=1.0,
    )
    detector = IsolationForest(
        n_estimators=100,
        contamination="auto",
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    return Pipeline([
        ("preprocessing", preprocessing),
        ("detector", detector),
    ])


def train_model(file_path=DATA_PATH):
    """Fit on normal training traffic and report results on a held-out split."""
    if not Path(file_path).is_file():
        raise FileNotFoundError(
            f"Dataset not found at {file_path}. Add the KDD Cup 10% CSV there first."
        )

    data = load_data(file_path)
    original_row_count = len(data)

    # Identical records can otherwise appear in both splits and inflate scores.
    label_counts = data.groupby(FEATURE_COLUMNS, sort=False)["label"].transform("nunique")
    data = data.loc[label_counts == 1]
    data = data.drop_duplicates(subset=FEATURE_COLUMNS).reset_index(drop=True)
    features = data[FEATURE_COLUMNS]
    is_anomaly = (data["label"] != "normal").astype(int)
    if is_anomaly.nunique() != 2:
        raise ValueError("The dataset must contain both normal and attack records.")

    x_train, x_test, y_train, y_test = train_test_split(
        features,
        is_anomaly,
        test_size=0.2,
        random_state=RANDOM_STATE,
        stratify=is_anomaly,
    )

    normal_training_rows = x_train.loc[y_train == 0]
    if normal_training_rows.empty:
        raise ValueError("No normal records found in the training split.")
    if len(normal_training_rows) > MAX_TRAIN_ROWS:
        normal_training_rows = normal_training_rows.sample(
            n=MAX_TRAIN_ROWS,
            random_state=RANDOM_STATE,
        )

    model = build_model()
    model.fit(normal_training_rows)

    # Isolation Forest returns 1 for normal and -1 for an anomaly.
    predictions = (model.predict(x_test) == -1).astype(int)
    precision, recall, f1, _ = precision_recall_fscore_support(
        y_test,
        predictions,
        average="binary",
        zero_division=0,
    )
    matrix = confusion_matrix(y_test, predictions, labels=[0, 1])

    joblib.dump(model, MODEL_PATH)
    global _MODEL
    _MODEL = model

    print(f"Unique feature rows: {len(data):,} (from {original_row_count:,})")
    print(f"Normal rows used for training: {len(normal_training_rows):,}")
    print(f"Holdout precision: {precision:.3f}")
    print(f"Holdout recall:    {recall:.3f}")
    print(f"Holdout F1 score:  {f1:.3f}")
    print("Confusion matrix (rows=true, columns=predicted; normal, anomaly):")
    print(matrix)
    print(f"Model saved to: {MODEL_PATH}")
    return model


def load_model():
    """Load the saved model once, when a prediction is first requested."""
    global _MODEL
    if _MODEL is None:
        if not MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Model not found at {MODEL_PATH}. Run `python model.py` first."
            )
        _MODEL = joblib.load(MODEL_PATH)
    return _MODEL


def predict(features):
    """Return 1 for normal traffic or -1 for an anomaly."""
    if not isinstance(features, dict):
        raise TypeError("Features must be provided as a dictionary.")

    row = pd.DataFrame([features]).reindex(columns=FEATURE_COLUMNS)
    for column in CATEGORICAL_COLUMNS:
        row[column] = row[column].map(_clean_category)
    for column in NUMERIC_COLUMNS:
        row[column] = pd.to_numeric(row[column], errors="coerce").fillna(0)

    return load_model().predict(row)


if __name__ == "__main__":
    train_model()
