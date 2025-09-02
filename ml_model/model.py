import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

def train_anomaly_detector():
    """Train an anomaly detection model on synthetic RPM data"""
    # Generate synthetic training data (normal RPM patterns)
    np.random.seed(42)
    normal_rpm = np.random.normal(1800, 100, 1000)  # Normal RPM around 1800
    
    # Add some anomalies for training
    anomalies = np.random.uniform(2200, 3000, 50)  # High RPM anomalies
    training_data = np.concatenate([normal_rpm, anomalies])
    
    X_train = training_data.reshape(-1, 1)
    
    # Scale the data
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    
    # Train Isolation Forest model
    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(X_train_scaled)
    
    return model, scaler

def detect_anomalies(model, scaler, rpm_data):
    """Detect anomalies in RPM data"""
    if not rpm_data:
        return np.array([]), np.array([])
    
    # Prepare and scale the data
    rpm_array = np.array(rpm_data).reshape(-1, 1)
    rpm_scaled = scaler.transform(rpm_array)
    
    # Predict anomalies
    anomalies = model.predict(rpm_scaled)
    anomaly_scores = model.decision_function(rpm_scaled)
    
    return anomalies, anomaly_scores