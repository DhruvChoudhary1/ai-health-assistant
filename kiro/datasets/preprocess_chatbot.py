import pandas as pd

# Load the dataset
df = pd.read_csv('ai-medical-chatbot.csv', usecols=['Description', 'Doctor'])

# Clean and drop missing values
df = df.dropna(subset=['Description', 'Doctor'])

# Save as a new CSV for chatbot use
df.to_csv('chatbot_conversations_cleaned.csv', index=False)

# Print a sample
print(df.sample(5))