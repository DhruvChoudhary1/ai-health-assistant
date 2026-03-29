import pandas as pd
df = pd.read_csv('ai-medical-chatbot.csv', nrows=5)
print(df.columns)
print(df.head())