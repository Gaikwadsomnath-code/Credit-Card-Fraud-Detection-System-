import pandas as pd
import random

# Load preprocessed dataset
df = pd.read_csv("processed_data.csv")  # Make sure this file exists in same folder

# Add dummy values to every row
df['user_id'] = [random.randint(1, 5) for _ in range(len(df))]
df['card_id'] = [random.randint(100, 105) for _ in range(len(df))]
df['merchant_name'] = random.choices(['Amazon', 'Flipkart', 'Snapdeal', 'Meesho'], k=len(df))
df['location'] = random.choices(['Pune', 'Mumbai', 'Delhi', 'Bangalore'], k=len(df))

#  Add dummy amount
df['amount'] = df['scaled_amount'] * 1000  # approximate reverse scaling


# Save extended dataset
df.to_csv("processed_data_extended.csv", index=False)
print(" All 985 records updated with dummy details and saved as 'processed_data_extended.csv'")
