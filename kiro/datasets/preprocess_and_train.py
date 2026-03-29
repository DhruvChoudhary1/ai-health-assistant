import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
import joblib

# Load dataset
df = pd.read_csv('Final_Augmented_dataset_Diseases_and_Symptoms.csv')

# Features: all columns except 'diseases'
X = df.drop('diseases', axis=1)
y = df['diseases']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = MultinomialNB()
clf.fit(X_train, y_train)

# Save model
joblib.dump(clf, 'disease_symptom_model.joblib')

# Evaluate
score = clf.score(X_test, y_test)
print(f'Model accuracy: {score:.2f}')