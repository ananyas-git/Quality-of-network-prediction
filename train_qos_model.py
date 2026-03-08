import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

# Load simulated data
df = pd.read_csv("qos_data.csv")

X = df[["latency", "jitter", "packet_loss", "bandwidth", "throughput"]]
y = df["qos_degraded"]

# Train model
model = RandomForestClassifier()
model.fit(X, y)

# Save the model
joblib.dump(model, "qos_model.pkl")
print("✅ Model trained and saved as qos_model.pkl")