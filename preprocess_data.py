import pandas as pd
from sklearn.preprocessing import StandardScaler

#  Step 1: Load Dataset
df = pd.read_csv('C:/Users/Somnath Gaikwad/OneDrive/Desktop/safeswipe/creditcard.csv')  # Replace with your file name

#  Step 2: Check Missing Values
print("Missing values:\n", df.isnull().sum())


#  Step 3: Scale 'Amount' and 'Time'
scaler = StandardScaler()

df['scaled_amount'] = scaler.fit_transform(df[['Amount']])
df['scaled_time'] = scaler.fit_transform(df[['Time']])

#  Step 4: Drop original 'Amount' and 'Time'
df.drop(['Amount', 'Time'], axis=1, inplace=True)

#  Step 5: Reorder columns (optional, for clarity)
scaled_cols = ['scaled_time'] + [col for col in df.columns if col not in ['scaled_time', 'Class']] + ['Class']
df = df[scaled_cols]

#  Step 6: Balance dataset (undersampling)
fraud_df = df[df['Class'] == 1]
non_fraud_df = df[df['Class'] == 0].sample(len(fraud_df), random_state=42)

df_balanced = pd.concat([fraud_df, non_fraud_df]).sample(frac=1, random_state=42)

#  Step 7: Save cleaned dataset
df_balanced.to_csv("processed_data.csv", index=False)
print(" Preprocessing complete. Saved to 'processed_data.csv'")

