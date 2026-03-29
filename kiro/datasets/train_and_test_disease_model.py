import pandas as pd
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt
import joblib

# ==============================
# Load and preprocess training data
# ==============================
train_df = pd.read_csv('training_data.csv')
train_df = train_df.fillna(0)
train_df = train_df.loc[:, ~train_df.columns.str.startswith('Unnamed:')]

X_train = train_df.drop('prognosis', axis=1)
y_train = train_df['prognosis']


# ==============================
# Load and preprocess test data
# ==============================
test_df = pd.read_csv('test_data.csv')
test_df = test_df.fillna(0)
test_df = test_df.loc[:, ~test_df.columns.str.startswith('Unnamed:')]

X_test = test_df[X_train.columns]
y_test = test_df['prognosis']


# ==============================
# Coverage & Consistency Checks
# ==============================
print("\n=== Coverage and Consistency Checks ===")

print(f"Number of symptoms (features) in training: {X_train.shape[1]}")
print(f"Number of symptoms (features) in test: {X_test.shape[1]}")

if list(X_train.columns) == list(X_test.columns):
    print("All symptom columns match between training and test data.")
else:
    print("Mismatch in symptom columns between training and test data!")
    print("Training columns not in test:", set(X_train.columns) - set(X_test.columns))
    print("Test columns not in training:", set(X_test.columns) - set(X_train.columns))

train_diseases = set(y_train.unique())
test_diseases = set(y_test.unique())

print(f"\nNumber of unique diseases in training: {len(train_diseases)}")
print(f"Number of unique diseases in test: {len(test_diseases)}")

print("\nDiseases in training data:", train_diseases)
print("Diseases in test data:", test_diseases)

print("\nDiseases only in training:", train_diseases - test_diseases)
print("Diseases only in test:", test_diseases - train_diseases)

if train_diseases == test_diseases:
    print("All diseases/classes are present in both training and test data.")
else:
    print("Warning: Some diseases are missing in test or training data!")


# ==============================
# Model Training
# ==============================
clf = MultinomialNB()
clf.fit(X_train, y_train)


# ==============================
# Training Accuracy
# ==============================
y_train_pred = clf.predict(X_train)
train_acc = accuracy_score(y_train, y_train_pred)
print(f"\nTraining Accuracy: {train_acc * 100:.2f}%")


# ==============================
# Save Model
# ==============================
joblib.dump(clf, 'disease_symptom_model.joblib')


# ==============================
# Test Evaluation
# ==============================
y_test_pred = clf.predict(X_test)
test_acc = accuracy_score(y_test, y_test_pred)

print(f"\nTest Accuracy: {test_acc * 100:.2f}%")

print("\n=== Classification Report ===")
print(classification_report(y_test, y_test_pred))


# ==============================
# Confusion Matrix
# ==============================
cm = confusion_matrix(y_test, y_test_pred)

print("\n=== Confusion Matrix ===")
print(cm)

# Plot Confusion Matrix
disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=clf.classes_)
disp.plot(xticks_rotation=90)
plt.title("Confusion Matrix")
plt.show()