import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split # Optional for this rule-based data
from sklearn.metrics import accuracy_score # Optional for this rule-based data
import joblib # For saving/loading the model

# --- 1. Data Definition (Based on your app's logic) ---

# Symptom list (ensure this order matches the map below and your app)
symptoms_list = [
    "Fever", "Cough", "Headache", "Fatigue", "Sneezing", "Body Ache",
    "Chills", "Sore Throat", "High BP", "High Sugar", "Runny Nose", "Rash",
    "Vomiting", "Diarrhea", "Abdominal Pain", "Loss of Appetite", "Dizziness",
    "Shortness of Breath", "Chest Pain", "Nausea", "Swelling", "Red Eyes",
    "Ear Pain", "Dehydration"
]

# Disease list (ensure this order matches the map below and your app)
diseases_list = [
    'Flu', 'Common Cold', 'Migraine', 'Hypertension', 'Allergy', 'Dengue',
    'Viral Fever', 'Strep Throat', 'High BP Crisis', 'Diabetes', 'Sinusitis',
    'Chickenpox', 'Gastroenteritis', 'Food Poisoning', 'Appendicitis', 'Typhoid',
    'Vertigo', 'Asthma', 'Heart Condition', 'Motion Sickness', 'Inflammation',
    'Conjunctivitis', 'Ear Infection', 'Dehydration'
]

# Symptom-to-Disease Mapping (0 or 1 for each disease in diseases_list order)
symptom_disease_map = {
    #       Flu CoC Mig Hyp All Den Vir Str HBP Dia Sin Chi Gas Foo App Typ Ver Ast Hea Mot Inf Con Ear Deh
    'Fever':             [1, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'Cough':             [1, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0],
    'Headache':          [1, 1, 1, 1, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0],
    'Fatigue':           [1, 1, 0, 0, 1, 1, 0, 0, 1, 1, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'Sneezing':          [0, 1, 0, 0, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Body Ache':         [1, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Chills':            [0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Sore Throat':       [1, 1, 0, 0, 0, 1, 0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'High BP':           [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'High Sugar':        [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Runny Nose':        [0, 1, 0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Rash':              [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Vomiting':          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    'Diarrhea':          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Abdominal Pain':    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    'Loss of Appetite':  [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
    'Dizziness':         [0, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0],
    'Shortness of Breath': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0],
    'Chest Pain':        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
    'Nausea':            [0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    'Swelling':          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
    'Red Eyes':          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0],
    'Ear Pain':          [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0],
    'Dehydration':       [0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
}

# --- 2. Data Preparation ---

# Create training data based on the rules
# Each row represents a 'perfect' example for a specific disease
training_data = []
for i, disease in enumerate(diseases_list):
    row = {}
    for symptom in symptoms_list:
        # Get the value (0 or 1) for this symptom and this disease
        row[symptom] = symptom_disease_map[symptom][i]
    row['disease'] = disease # Add the target disease label
    training_data.append(row)

# Convert to Pandas DataFrame
df_train = pd.DataFrame(training_data)

# Separate features (X) and target (y)
X_train = df_train[symptoms_list] # Features are the symptom columns
y_train = df_train['disease']     # Target is the disease column

print("Training Data Prepared:")
print(df_train.head()) # Print first few rows to verify

# --- 3. Model Training ---

print("\nTraining Decision Tree model...")
# Initialize the Decision Tree Classifier model
# random_state ensures the split is the same each time, making results reproducible
model = DecisionTreeClassifier(random_state=42)

# Train the model using the prepared data
model.fit(X_train, y_train)

print("Model training complete.")

# --- 4. (Optional) Save the Trained Model ---
# This allows you to load the model later without retraining
model_filename = 'disease_predictor_dt_model.joblib'
try:
    joblib.dump(model, model_filename)
    print(f"Model saved successfully to '{model_filename}'")
except Exception as e:
    print(f"Error saving model: {e}")

# --- 5. Example Prediction (How to use the model) ---

def predict_disease_with_model(selected_symptoms_keys, trained_model, all_symptoms_list):
    """ Predicts disease using the trained model. """
    if not selected_symptoms_keys:
        return "General Illness"

    # Create input vector matching the training data columns
    input_vector = pd.DataFrame([[0]*len(all_symptoms_list)], columns=all_symptoms_list)

    # Set 1 for selected symptoms
    for symptom_key in selected_symptoms_keys:
        if symptom_key in input_vector.columns:
            input_vector[symptom_key] = 1
        else:
            print(f"Warning: Symptom '{symptom_key}' not found in model features.")

    try:
        # Make prediction using the trained model
        prediction = trained_model.predict(input_vector)
        # predict returns an array, get the first (and only) element
        return prediction[0]
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Prediction Error"

# Example usage after training (or loading the saved model)
if __name__ == "__main__":
    # Load the saved model (if running this script separately later)
    try:
        loaded_model = joblib.load(model_filename)
        print(f"\nModel '{model_filename}' loaded successfully.")

        # Test prediction 1
        test_symptoms = ["Fever", "Cough", "Headache"]
        prediction = predict_disease_with_model(test_symptoms, loaded_model, symptoms_list)
        print(f"Symptoms: {test_symptoms}")
        print(f"Predicted Disease: {prediction}") # Expected: Flu (based on rules)

        # Test prediction 2
        test_symptoms_2 = ["Headache", "Nausea"]
        prediction_2 = predict_disease_with_model(test_symptoms_2, loaded_model, symptoms_list)
        print(f"\nSymptoms: {test_symptoms_2}")
        print(f"Predicted Disease: {prediction_2}") # Expected: Migraine or Gastroenteritis (depending on tree splits)

    except FileNotFoundError:
        print(f"\nModel file '{model_filename}' not found. Run training first.")
    except Exception as e:
        print(f"\nError loading or using model: {e}")

