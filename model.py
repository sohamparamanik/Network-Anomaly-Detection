import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import LabelEncoder
import joblib
import os

# Define the columns (KDD Cup 99 has 41 features + 1 label)
columns = ["duration", "protocol_type", "service", "flag", "src_bytes",
           "dst_bytes", "land", "wrong_fragment", "urgent", "hot",
           "num_failed_logins", "logged_in", "num_compromised", "root_shell",
           "su_attempted", "num_root", "num_file_creations", "num_shells",
           "num_access_files", "num_outbound_cmds", "is_host_login",
           "is_guest_login", "count", "srv_count", "serror_rate",
           "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
           "diff_srv_rate", "srv_diff_host_rate", "dst_host_count",
           "dst_host_srv_count", "dst_host_same_srv_rate", "dst_host_diff_srv_rate",
           "dst_host_same_src_port_rate", "dst_host_srv_diff_host_rate",
           "dst_host_serror_rate", "dst_host_srv_serror_rate",
           "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label"]

def load_data(file_path):
    df = pd.read_csv(file_path, names=columns)
    # The dataset contains strings like "b'tcp'". We need to clean them to just "tcp"
    df.replace({r"^b'(.*)'$": r"\1"}, regex=True, inplace=True)
    # Also clean the label
    df['label'] = df['label'].astype(str).str.replace(r"^b'(.*)\.'$", r"\1", regex=True)
    df['label'] = df['label'].astype(str).str.replace(r"^b'(.*)'$", r"\1", regex=True)
    print(f"Dataset Loaded: {df.shape}")
    return df

def preprocess_and_train():
    file_path = 'data/kddcup.data_10_percent.csv'
    if not os.path.exists(file_path):
        print(f"File {file_path} not found.")
        return None
    
    print("Loading data...")
    df = load_data(file_path)
    
    # Anomaly Detection models should be trained on normal data to learn the baseline
    normal_df = df[df['label'].astype(str).str.contains('normal', case=False)]
    
    if len(normal_df) > 10000:
        normal_df = normal_df.sample(n=10000, random_state=42)
    elif len(normal_df) == 0:
        print("Warning: No normal data found! Using raw sample.")
        normal_df = df.sample(n=10000, random_state=42)
        
    # Separate features and labels
    X = normal_df.drop('label', axis=1)
    
    print("Preprocessing data...")
    # Encode categorical features
    categorical_cols = ['protocol_type', 'service', 'flag']
    encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        # Convert all to string to prevent mixed type errors
        X[col] = le.fit_transform(X[col].astype(str))
        encoders[col] = le
        
    # Fill any NaNs with 0
    X = X.fillna(0)
    
    print("Training Isolation Forest...")
    # Train Isolation Forest
    model = IsolationForest(n_estimators=100, contamination=0.1, random_state=42)
    model.fit(X)
    
    # Save the model and encoders
    print("Saving model and encoders...")
    joblib.dump(model, 'model.pkl')
    joblib.dump(encoders, 'encoders.pkl')
    joblib.dump(X.columns.tolist(), 'features.pkl')
    print("Training completed!")
    return model

def predict(data_dict):
    """
    Predicts if a single connection or batch is an anomaly.
    Returns: 1 for normal, -1 for anomaly.
    """
    if not os.path.exists('model.pkl') or not os.path.exists('encoders.pkl'):
        print("Model not trained yet.")
        return None
        
    model = joblib.load('model.pkl')
    encoders = joblib.load('encoders.pkl')
    feature_names = joblib.load('features.pkl')
    
    df = pd.DataFrame([data_dict]) if isinstance(data_dict, dict) else pd.DataFrame(data_dict)
    
    for col in feature_names:
        if col not in df.columns:
            df[col] = 0
            
    df = df[feature_names]
    
    categorical_cols = ['protocol_type', 'service', 'flag']
    for col in categorical_cols:
        if col in encoders:
            classes = encoders[col].classes_
            df[col] = df[col].astype(str).apply(lambda x: x if x in classes else classes[0])
            df[col] = encoders[col].transform(df[col])
            
    df = df.fillna(0)
    predictions = model.predict(df)
    return predictions

if __name__ == "__main__":
    preprocess_and_train()
