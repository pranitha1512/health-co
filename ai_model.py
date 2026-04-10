import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib # For saving/loading the model (optional)

# --- 1. Data Preparation ---
# Use the data structures similar to your Tkinter app

symptom_translations = {
    "Fever": {"english": "Fever", "hindi": "बुखार", "telugu": "జ్వరం"},
    "Cough": {"english": "Cough", "hindi": "खांसी", "telugu": "దగ్గు"},
    "Headache": {"english": "Headache", "hindi": "सिरदर्द", "telugu": "తలనొప్పి"},
    "Fatigue": {"english": "Fatigue", "hindi": "थकान", "telugu": "అలసట"},
    "Sneezing": {"english": "Sneezing", "hindi": "छींक आना", "telugu": "తుమ్ము"},
    "Body Ache": {"english": "Body Ache", "hindi": "शरीर में दर्द", "telugu": "శరీరం నొప్పి"},
    "Chills": {"english": "Chills", "hindi": "ठंड लगना", "telugu": "చలి"},
    "Sore Throat": {"english": "Sore Throat", "hindi": "गले में खराश", "telugu": "గొంతు నొప్పి"},
    "High BP": {"english": "High BP", "hindi": "उच्च रक्तचाप", "telugu": "అధిక రక్తపోటు"},
    "High Sugar": {"english": "High Sugar", "hindi": "उच्च शर्करा", "telugu": "అధిక షుగర్"},
    "Runny Nose": {"english": "Runny Nose", "hindi": "नाक बहना", "telugu": "నాసికా స్రావం"},
    "Rash": {"english": "Rash", "hindi": "दाने", "telugu": "టొణపం"},
    "Vomiting": {"english": "Vomiting", "hindi": "उल्टी", "telugu": "వాంతి"},
    "Diarrhea": {"english": "Diarrhea", "hindi": "दस्त", "telugu": "అతిసారం"},
    "Abdominal Pain": {"english": "Abdominal Pain", "hindi": "पेट दर्द", "telugu": "ఉదరం నొప్పి"},
    "Loss of Appetite": {"english": "Loss of Appetite", "hindi": "भूख न लगना", "telugu": "ఆకలి లేకపోవడం"},
    "Dizziness": {"english": "Dizziness", "hindi": "चक्कर आना", "telugu": "తలతిరుగుడు"},
    "Shortness of Breath": {"english": "Shortness of Breath", "hindi": "सांस लेने में तकलीफ", "telugu": "ఊపిరి ఆడకపోవడం"},
    "Chest Pain": {"english": "Chest Pain", "hindi": "सीने में दर्द", "telugu": "ఛాతీ నొప్పి"},
    "Nausea": {"english": "Nausea", "hindi": "मतली", "telugu": "వికారం"},
    "Swelling": {"english": "Swelling", "hindi": "सूजन", "telugu": "ఊతం"},
    "Red Eyes": {"english": "Red Eyes", "hindi": "लाल आँखें", "telugu": "ఎర్రగా కన్నులు"},
    "Ear Pain": {"english": "Ear Pain", "hindi": "कान दर्द", "telugu": "చెవి నొప్పి"},
    "Dehydration": {"english": "Dehydration", "hindi": "निर्जलीकरण", "telugu": "నిర్జలీకరణ"}
}
symptoms_list = list(symptom_translations.keys())

symptom_disease_map = {
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

diseases_list = [
    'Flu', 'Common Cold', 'Migraine', 'Hypertension', 'Allergy', 'Dengue',
    'Viral Fever', 'Strep Throat', 'High BP Crisis', 'Diabetes', 'Sinusitis',
    'Chickenpox', 'Gastroenteritis', 'Food Poisoning', 'Appendicitis', 'Typhoid',
    'Vertigo', 'Asthma', 'Heart Condition', 'Motion Sickness', 'Inflammation',
    'Conjunctivitis', 'Ear Infection', 'Dehydration'
]

# Create a DataFrame - this represents our training data
# Rows: Examples of symptom combinations leading to a disease
# Columns: Symptoms (0 or 1) + Target Disease
data_rows = []
for disease_index, disease_name in enumerate(diseases_list):
    # Find all symptoms associated with this disease
    symptoms_for_disease = {}
    for symptom_key in symptoms_list:
        if symptom_disease_map[symptom_key][disease_index] == 1:
            symptoms_for_disease[symptom_key] = 1
        else:
             symptoms_for_disease[symptom_key] = 0 # Explicitly add 0 for non-associated symptoms

    # Add the target disease
    symptoms_for_disease['disease'] = disease_name
    data_rows.append(symptoms_for_disease)

# Convert to Pandas DataFrame
df = pd.DataFrame(data_rows)

# Handle potential missing symptoms (if map doesn't cover all) - fill with 0
df = df.fillna(0)

# Separate features (X) and target (y)
X = df[symptoms_list] # Features are the symptom columns
y = df['disease']     # Target is the disease column

# --- 2. Model Training ---
# Split data (optional but good practice, though less meaningful with synthetic rule-based data)
# X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Initialize the Decision Tree Classifier model
# random_state ensures reproducibility
model = DecisionTreeClassifier(random_state=42)

# Train the model on the *entire* dataset since it's derived from rules
model.fit(X, y)

print("Model training complete.")

# --- (Optional) Evaluate Model Accuracy (less useful here) ---
# y_pred = model.predict(X_test)
# accuracy = accuracy_score(y_test, y_pred)
# print(f"Model Accuracy on Test Set: {accuracy * 100:.2f}%") # Will likely be high due to rule-based data

# --- (Optional) Save the Trained Model ---
model_filename = 'disease_predictor_model.joblib'
joblib.dump(model, model_filename)
print(f"Model saved to {model_filename}")

# --- 3. Prediction Function ---

# Load the model (if saved separately)
# loaded_model = joblib.load(model_filename)
# print("Model loaded.")

def predict_disease_ai(selected_symptoms_keys, trained_model, all_symptoms_list):
    """
    Predicts disease based on selected symptoms using the trained AI model.

    Args:
        selected_symptoms_keys (list): A list of symptom keys (strings) that are present.
        trained_model: The trained scikit-learn model object.
        all_symptoms_list (list): The full list of all possible symptom keys in the correct order.

    Returns:
        str: The predicted disease name, or "General Illness" if prediction fails or no symptoms match.
    """
    if not selected_symptoms_keys:
        return "General Illness" # Or handle as appropriate

    # Create the input vector (like in the training data)
    # Initialize with all zeros
    input_vector = [0] * len(all_symptoms_list)

    # Set 1 for the symptoms that are present
    for i, symptom_key in enumerate(all_symptoms_list):
        if symptom_key in selected_symptoms_keys:
            input_vector[i] = 1

    # Reshape for single prediction: scikit-learn expects a 2D array
    input_df = pd.DataFrame([input_vector], columns=all_symptoms_list)

    try:
        # Make prediction
        prediction = trained_model.predict(input_df)
        return prediction[0] # predict returns an array, get the first element
    except Exception as e:
        print(f"Error during prediction: {e}")
        return "Prediction Error"


# --- 4. Example Usage ---
if __name__ == "__main__":
    # Simulate symptoms selected by the user in the GUI
    # Example 1: Flu-like symptoms
    user_symptoms_1 = ["Fever", "Cough", "Body Ache", "Headache"]
    predicted_disease_1 = predict_disease_ai(user_symptoms_1, model, symptoms_list)
    print(f"\nSymptoms: {user_symptoms_1}")
    print(f"Predicted Disease (AI): {predicted_disease_1}")

    # Example 2: Cold-like symptoms
    user_symptoms_2 = ["Cough", "Sneezing", "Runny Nose", "Sore Throat"]
    predicted_disease_2 = predict_disease_ai(user_symptoms_2, model, symptoms_list)
    print(f"\nSymptoms: {user_symptoms_2}")
    print(f"Predicted Disease (AI): {predicted_disease_2}")

    # Example 3: Migraine-like symptoms
    user_symptoms_3 = ["Headache", "Nausea", "Dizziness"]
    predicted_disease_3 = predict_disease_ai(user_symptoms_3, model, symptoms_list)
    print(f"\nSymptoms: {user_symptoms_3}")
    print(f"Predicted Disease (AI): {predicted_disease_3}")

    # Example 4: Only one symptom
    user_symptoms_4 = ["Rash"]
    predicted_disease_4 = predict_disease_ai(user_symptoms_4, model, symptoms_list)
    print(f"\nSymptoms: {user_symptoms_4}")
    print(f"Predicted Disease (AI): {predicted_disease_4}") # Might predict Chickenpox based on rules
