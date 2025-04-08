# train_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Load dataset
df = pd.read_csv("ai4i2020.csv")

# Encode 'Type' categorical variable
le = LabelEncoder()
df["type"] = le.fit_transform(df["Type"])  # L:0, M:1, H:2

# Select features and target
X = df[["Air temperature [K]", "Process temperature [K]",
        "Rotational speed [rpm]", "Torque [Nm]", "Tool wear [min]", "type"]]
y = df["Machine failure"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Model
clf = RandomForestClassifier(n_estimators=100)
clf.fit(X_train, y_train)

# Evaluation
print(classification_report(y_test, clf.predict(X_test)))

# Save model
joblib.dump(clf, "failure_model.pkl")
