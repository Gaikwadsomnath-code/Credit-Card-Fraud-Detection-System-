import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import pickle

# 🔹 Step 1: Load preprocessed data
df = pd.read_csv("processed_data.csv")

# 🔹 Step 2: Split X (features) and y (target)
X = df.drop("Class", axis=1)
y = df["Class"]

# 🔹 Step 3: Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 🔹 Step 4: Train model (RandomForest)
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 🔹 Step 5: Evaluate
y_pred = model.predict(X_test)
print("\n🧪 Classification Report:\n")
print(classification_report(y_test, y_pred))

# 🔹 Step 6: Save model as .pkl
with open("fraud_model.pkl", "wb") as f:
    pickle.dump(model, f)

print("\n Model trained and saved as 'fraud_model.pkl'")
