import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from sqlite3 import Error
import webbrowser
from datetime import datetime

class ClickableText(tk.Text):
    """A custom Text widget that makes URLs clickable."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configure the 'link' tag for visual appearance
        self.tag_configure("link", foreground="blue", underline=True)
        # Bind events for clicking and hovering over the link
        self.tag_bind("link", "<Button-1>", self._on_link_click)
        self.tag_bind("link", "<Enter>", lambda e: self.config(cursor="hand2"))
        self.tag_bind("link", "<Leave>", lambda e: self.config(cursor=""))
        # Dictionary to store link ranges and their corresponding URLs
        self.links = {}

    def add_link(self, start, end, url):
        """Adds a clickable link to the text widget."""
        self.tag_add("link", start, end)
        self.links[(start, end)] = url

    def _on_link_click(self, event):
        """Handles the click event on a link."""
        # Get the index of the character clicked
        index = self.index(f"@{event.x},{event.y}")
        # Check if the click was within any of the defined link ranges
        for (start, end), url in self.links.items():
            if self.compare(start, "<=", index) and self.compare(index, "<", end):
                # Open the URL in a web browser if clicked
                webbrowser.open_new(url)
                break

class Database:
    """Handles database operations for the hospital management system."""
    def __init__(self, db_file="hospital.db"):
        """Initializes the database connection and creates tables if they don't exist."""
        self.conn = None
        try:
            # Connect to the SQLite database
            self.conn = sqlite3.connect(db_file)
            # Enable foreign key constraint enforcement
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Create necessary tables
            self.create_tables()
        except Error as e:
            messagebox.showerror("Database Error", f"Error connecting to database: {e}")

    def create_tables(self):
        """Creates the necessary tables in the database if they don't already exist."""
        sql_commands = [
            """CREATE TABLE IF NOT EXISTS patients (
                patient_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER,
                sex TEXT,
                address TEXT,
                phone TEXT,
                email TEXT,
                registered_date TEXT DEFAULT CURRENT_TIMESTAMP
            );""",
            """CREATE TABLE IF NOT EXISTS doctors (
                doctor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT,
                phone TEXT,
                email TEXT,
                department TEXT
            );""",
            """CREATE TABLE IF NOT EXISTS appointments (
                appointment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                diagnosis TEXT,
                prescription TEXT,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
            );""",
            """CREATE TABLE IF NOT EXISTS medical_history (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                visit_date TEXT DEFAULT CURRENT_TIMESTAMP,
                symptoms TEXT,
                diagnosis TEXT,
                treatment TEXT,
                doctor_id INTEGER,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
                FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
            );"""
        ]

        try:
            cursor = self.conn.cursor()
            # Execute each SQL command to create tables
            for command in sql_commands:
                cursor.execute(command)
            # Commit the changes to the database
            self.conn.commit()
        except Error as e:
            messagebox.showerror("Database Error", f"Error creating tables: {e}")

    def add_patient(self, name, age=None, sex=None, address=None, phone=None, email=None):
        """Adds a new patient record to the database."""
        sql = """INSERT INTO patients(name, age, sex, address, phone, email)
                 VALUES(?,?,?,?,?,?)"""
        try:
            cursor = self.conn.cursor()
            # Ensure age is an integer or None
            age_val = int(age) if age and str(age).isdigit() else None
            cursor.execute(sql, (name, age_val, sex, address, phone, email))
            self.conn.commit()
            # Return the ID of the newly inserted patient
            return cursor.lastrowid
        except Error as e:
            messagebox.showerror("Database Error", f"Error adding patient: {e}")
            return None
        except ValueError:
             messagebox.showerror("Input Error", "Age must be a number.")
             return None


    def get_patient(self, patient_id):
        """Retrieves a patient record by their ID."""
        sql = "SELECT * FROM patients WHERE patient_id = ?"
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (patient_id,))
            # Return the fetched patient data (ID, Name, Age, Sex, Address, Phone, Email, RegDate)
            return cursor.fetchone()
        except Error as e:
            messagebox.showerror("Database Error", f"Error getting patient: {e}")
            return None

    def add_medical_record(self, patient_id, symptoms, diagnosis, treatment, doctor_id=None):
        """Adds a new medical record for a patient."""
        sql = """INSERT INTO medical_history(patient_id, symptoms, diagnosis, treatment, doctor_id)
                 VALUES(?,?,?,?,?)"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (patient_id, symptoms, diagnosis, treatment, doctor_id))
            self.conn.commit()
            # Return the ID of the newly inserted medical record
            return cursor.lastrowid
        except Error as e:
            messagebox.showerror("Database Error", f"Error adding medical record: {e}")
            return None

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()

class DiseasePredictor:
    """Predicts diseases based on symptoms using a simple mapping."""
    def __init__(self):
        """Initializes symptom translations, the symptom list, and the symptom-disease map."""
        # Dictionary mapping symptom keys to their translations in different languages
        self.symptom_translations = {
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

        # List of all symptom keys
        self.symptoms = list(self.symptom_translations.keys())

        # Matrix mapping symptoms (rows) to diseases (columns)
        # 1 indicates the symptom is associated with the disease, 0 otherwise
        self.symptom_disease_map = {
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

        # List of diseases corresponding to the columns in symptom_disease_map
        self.diseases = [
            'Flu', 'Common Cold', 'Migraine', 'Hypertension', 'Allergy', 'Dengue',
            'Viral Fever', 'Strep Throat', 'High BP Crisis', 'Diabetes', 'Sinusitis',
            'Chickenpox', 'Gastroenteritis', 'Food Poisoning', 'Appendicitis', 'Typhoid',
            'Vertigo', 'Asthma', 'Heart Condition', 'Motion Sickness', 'Inflammation',
            'Conjunctivitis', 'Ear Infection', 'Dehydration'
        ]

    def get_symptom_name(self, symptom_key, language):
        """Returns the translated name of a symptom for the given language."""
        return self.symptom_translations.get(symptom_key, {}).get(language, symptom_key)

    def predict(self, symptoms):
        """Predicts the most likely disease based on the selected symptoms."""
        # Create a binary vector from the selected symptoms
        symptom_vector = [1 if s else 0 for s in symptoms]
        # Initialize scores for each disease to zero
        disease_scores = [0] * len(self.diseases)

        # Iterate through each symptom and update disease scores
        for symptom_idx, symptom_present in enumerate(symptom_vector):
            if symptom_present:
                symptom_key = self.symptoms[symptom_idx]
                # Check the symptom-disease map for this symptom
                if symptom_key in self.symptom_disease_map:
                    for disease_idx in range(len(self.diseases)):
                        # If the symptom is associated with the disease, increment the score
                        if self.symptom_disease_map[symptom_key][disease_idx] == 1:
                            disease_scores[disease_idx] += 1

        # Find the maximum score among all diseases
        max_score = max(disease_scores) if disease_scores else 0

        # If no symptoms match any disease significantly, return "General Illness"
        if max_score == 0:
            return "General Illness"

        # Find the index (and thus the name) of the disease with the highest score
        best_match_idx = disease_scores.index(max_score)
        return self.diseases[best_match_idx]

class HospitalApp:
    """Main application class for the Hospital Management System GUI."""
    def __init__(self, root):
        """Initializes the application UI and components."""
        self.root = root
        self.root.title("Hospital Management System - KG Reddy College")
        self.root.geometry("1200x800") # Set initial window size
        self.root.configure(bg="#e0f7fa") # Light blue background

        # Initialize database and predictor
        self.db = Database()
        self.predictor = DiseasePredictor()
        # Language variable for UI text
        self.language = tk.StringVar(value="english")
        # Load translations and treatment data
        self.translations = self.get_translations()
        self.treatment_db = self.get_treatment_db()
        # List to hold symptom checkbox widgets
        self.symptom_checkboxes = []
        # Variable to store the current diagnosis result
        self.current_diagnosis = None
        # Variable to store the currently loaded patient ID
        self.current_patient_id = None

        # --- Style Configuration ---
        self.style = ttk.Style()
        self.style.theme_use('clam') # Using a theme that allows more customization
        self.style.configure('TButton', font=('Arial', 11), padding=5)
        self.style.configure('TLabel', background="#e0f7fa", font=('Arial', 11))
        self.style.configure('TEntry', font=('Arial', 11))
        self.style.configure('TCombobox', font=('Arial', 11))
        self.style.configure('TCheckbutton', background="#e0f7fa", font=('Arial', 11))
        self.style.configure('TLabelframe', background="#e0f7fa", padding=10)
        self.style.configure('TLabelframe.Label', background="#e0f7fa", font=('Arial', 12, 'bold'))
        self.style.configure('Header.TFrame', background="#01579b")
        self.style.configure('Header.TLabel', background="#01579b", foreground="white")
        self.style.configure('Report.TLabel', background="#bbdefb", anchor='w', justify='left')
        self.style.configure('Report.TLabelframe', background="#bbdefb")
        self.style.configure('Report.TLabelframe.Label', background="#bbdefb", font=('Arial', 12))
        self.style.configure('Action.TButton', foreground='white', font=('Arial', 12, 'bold'), padding=10)
        self.style.map('Action.TButton', background=[('active', '#0277bd'), ('!disabled', '#0288d1')]) # Diagnose button color
        self.style.configure('Clear.TButton', foreground='black', font=('Arial', 11, 'bold'), padding=5)
        self.style.map('Clear.TButton', background=[('active', '#cfd8dc'), ('!disabled', '#eceff1')]) # Clear button color
        self.style.configure('Save.TButton', foreground='white', font=('Arial', 12), padding=5)
        self.style.map('Save.TButton', background=[('active', '#00695c'), ('!disabled', '#00796b')]) # Save button color
        self.style.configure('Search.TButton', foreground='black', font=('Arial', 11), padding=5)
        self.style.map('Search.TButton', background=[('active', '#b0bec5'), ('!disabled', '#cfd8dc')]) # Search button color


        # Create UI elements
        self.create_header()
        self.create_main_frames()
        # --- New: Create Search Section FIRST ---
        self.create_patient_search()
        self.create_patient_form()
        self.create_symptoms_form()
        # --- New: Create Action Buttons Frame ---
        self.create_action_buttons()
        self.create_report_section()
        self.create_language_selector()
        # Initial UI update based on default language
        self.update_language()

    def create_header(self):
        """Creates the header section with title and college name."""
        # Use ttk Frame for styling
        header = ttk.Frame(self.root, height=80, style='Header.TFrame')
        header.pack(fill=tk.X)
        header.pack_propagate(False) # Prevent resizing based on content

        title = ttk.Label(
            header,
            text=self.translations["title"][self.language.get()], # Use translated title
            font=('Helvetica', 20, 'bold'),
            style='Header.TLabel'
        )
        title.pack(pady=(15,0)) # Adjusted padding
        self.title_label = title # Store reference for language update

        college = ttk.Label(
            header,
            text="KG Reddy College of Engineering CSM-A",
            font=('Helvetica', 12),
            style='Header.TLabel'
        )
        college.pack(side=tk.BOTTOM, pady=(0,10)) # Adjusted padding

    def create_main_frames(self):
        """Creates the main left and right frames for input and output."""
        main_frame = ttk.Frame(self.root, padding=(20, 10)) # Use ttk Frame
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Left frame for patient info and symptoms
        self.left_frame = ttk.LabelFrame(
            main_frame,
            text=self.translations["patient_info"][self.language.get()], # Translated label
            style='TLabelframe'
        )
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5)) # Adjusted padding

        # Right frame for diagnosis report
        self.right_frame = ttk.LabelFrame(
            main_frame,
            text=self.translations["diagnosis_report"][self.language.get()], # Translated label
            style='TLabelframe'
        )
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0)) # Adjusted padding

    # --- NEW: Patient Search Section ---
    def create_patient_search(self):
        """Creates the section for searching patients by ID."""
        search_frame = ttk.LabelFrame(
            self.left_frame,
            text=self.translations["search_patient_title"][self.language.get()],
            style='TLabelframe',
            padding=(10, 5)
        )
        search_frame.pack(fill=tk.X, pady=(0, 10), padx=5) # Pack at the top

        # Patient ID Label and Entry
        self.search_id_label = ttk.Label(search_frame, text=self.translations["patient_id_label"][self.language.get()])
        self.search_id_label.grid(row=0, column=0, padx=(0, 5), pady=5, sticky=tk.W)

        self.patient_id_entry = ttk.Entry(search_frame, width=10)
        self.patient_id_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)

        # Search Button
        self.search_btn = ttk.Button(
            search_frame,
            text=self.translations["search_button"][self.language.get()],
            command=self.search_patient,
            style='Search.TButton'
        )
        self.search_btn.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)


    def create_patient_form(self):
        """Creates the form for entering patient details."""
        # Renamed frame for clarity
        self.patient_details_frame = ttk.LabelFrame(
            self.left_frame,
            text=self.translations["patient_details_title"][self.language.get()],
            style='TLabelframe',
            padding=(10, 5)
        )
        self.patient_details_frame.pack(fill=tk.X, pady=5, padx=5) # Pack below search

        # Patient Name
        self.patient_name_label = ttk.Label(self.patient_details_frame, text=self.translations["patient_name_label"][self.language.get()])
        self.patient_name_label.grid(row=0, column=0, sticky=tk.W, pady=5, padx=(0,5))
        self.patient_name_entry = ttk.Entry(self.patient_details_frame, width=30)
        self.patient_name_entry.grid(row=0, column=1, pady=5, padx=5, sticky=tk.EW) # Use EW sticky

        # Age
        self.age_label = ttk.Label(self.patient_details_frame, text=self.translations["age_label"][self.language.get()])
        self.age_label.grid(row=1, column=0, sticky=tk.W, pady=5, padx=(0,5))
        self.patient_age_entry = ttk.Entry(self.patient_details_frame, width=10)
        self.patient_age_entry.grid(row=1, column=1, pady=5, padx=5, sticky=tk.W) # Use W sticky

        # Sex
        self.sex_label = ttk.Label(self.patient_details_frame, text=self.translations["sex_label"][self.language.get()])
        self.sex_label.grid(row=2, column=0, sticky=tk.W, pady=5, padx=(0,5))
        self.patient_sex_combo = ttk.Combobox(self.patient_details_frame, values=["Male", "Female", "Other"], state="readonly", width=10)
        self.patient_sex_combo.grid(row=2, column=1, pady=5, padx=5, sticky=tk.W) # Use W sticky

        # Phone
        self.phone_label = ttk.Label(self.patient_details_frame, text=self.translations["phone_label"][self.language.get()])
        self.phone_label.grid(row=3, column=0, sticky=tk.W, pady=5, padx=(0,5))
        self.patient_phone_entry = ttk.Entry(self.patient_details_frame, width=20)
        self.patient_phone_entry.grid(row=3, column=1, pady=5, padx=5, sticky=tk.W) # Use W sticky

        # Configure column 1 to expand
        self.patient_details_frame.columnconfigure(1, weight=1)


    def create_symptoms_form(self):
        """Creates the scrollable form for selecting symptoms."""
        # Frame for symptoms section
        self.symptoms_frame = ttk.LabelFrame(
            self.left_frame,
            text=self.translations["symptoms"][self.language.get()], # Translated label
            style='TLabelframe'
        )
        self.symptoms_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=5) # Pack below patient details

        # Canvas and Scrollbar for scrolling through symptoms
        canvas = tk.Canvas(self.symptoms_frame, bg="#e0f7fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.symptoms_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas, style='TFrame') # Use ttk Frame

        # Configure scrollable frame to update canvas scroll region
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        # Place scrollable frame inside canvas
        canvas_window = canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Adjust canvas window width on canvas resize
        canvas.bind('<Configure>', lambda e: canvas.itemconfig(canvas_window, width=e.width))


        # Create checkboxes for each symptom
        self.symptom_vars = []
        self.symptom_checkboxes = []
        num_symptoms = len(self.predictor.symptoms)
        cols = 2 # Arrange symptoms in 2 columns
        rows_per_col = (num_symptoms + cols - 1) // cols

        for i, symptom_key in enumerate(self.predictor.symptoms):
            var = tk.IntVar()
            self.symptom_vars.append(var)

            # Get translated symptom name
            symptom_name = self.predictor.get_symptom_name(symptom_key, self.language.get())

            # Create Checkbutton using ttk
            cb = ttk.Checkbutton(
                self.scrollable_frame,
                text=symptom_name,
                variable=var,
                style='TCheckbutton'
                # anchor='w' # Anchor is not a ttk Checkbutton option
            )
            self.symptom_checkboxes.append((symptom_key, cb)) # Store key and widget

            # Grid layout for checkboxes
            row_num = i % rows_per_col
            col_num = i // rows_per_col
            cb.grid(row=row_num, column=col_num, sticky='w', pady=2, padx=5)

        # Configure columns to have equal weight within the scrollable frame
        self.scrollable_frame.columnconfigure(0, weight=1)
        self.scrollable_frame.columnconfigure(1, weight=1)


    # --- NEW: Action Buttons Frame ---
    def create_action_buttons(self):
        """Creates a frame for Diagnose and Clear buttons."""
        action_button_frame = ttk.Frame(self.left_frame, style='TFrame')
        action_button_frame.pack(pady=10)

        # Diagnose Button
        self.diagnose_btn = ttk.Button(
            action_button_frame,
            text=self.translations["diagnose"][self.language.get()], # Translated text
            command=self.diagnose_patient,
            style='Action.TButton' # Custom style for prominent button
        )
        self.diagnose_btn.pack(side=tk.LEFT, padx=10)

        # Clear Button
        self.clear_btn = ttk.Button(
            action_button_frame,
            text=self.translations["clear_button"][self.language.get()], # Translated text
            command=self.clear_fields, # Link to clear_fields method
            style='Clear.TButton' # Custom style
        )
        self.clear_btn.pack(side=tk.LEFT, padx=10)


    def create_report_section(self):
        """Creates the section to display the diagnosis report."""
        # Label for Predicted Condition
        self.disease_label = ttk.Label(
            self.right_frame,
            text=self.translations["predicted_condition"][self.language.get()], # Translated text
            font=('Arial', 14, 'bold'),
            style='Report.TLabel', # Use style
            wraplength=450 # Wrap text if too long
        )
        self.disease_label.pack(fill=tk.X, pady=5, padx=10)

        # Label for Severity
        self.severity_label = ttk.Label(
            self.right_frame,
            text=self.translations["severity"][self.language.get()], # Translated text
            font=('Arial', 12),
            style='Report.TLabel' # Use style
        )
        self.severity_label.pack(fill=tk.X, pady=5, padx=10)

        # Frame and Text widget for Remedies
        self.remedies_frame = ttk.LabelFrame(
            self.right_frame,
            text=self.translations["remedies"][self.language.get()], # Translated label
            style='Report.TLabelframe' # Use style
        )
        self.remedies_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        # Add scrollbar for remedies text
        remedies_scrollbar = ttk.Scrollbar(self.remedies_frame)
        remedies_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.remedies_text = tk.Text(
            self.remedies_frame,
            wrap=tk.WORD,
            font=('Arial', 11),
            height=6,
            bg="white",
            state=tk.DISABLED, # Initially disabled
            yscrollcommand=remedies_scrollbar.set # Link scrollbar
        )
        self.remedies_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5,0), pady=5)
        remedies_scrollbar.config(command=self.remedies_text.yview)


        # Frame and ClickableText widget for Medicines
        self.medicines_frame = ttk.LabelFrame(
            self.right_frame,
            text=self.translations["medicines"][self.language.get()], # Translated label
            style='Report.TLabelframe' # Use style
        )
        self.medicines_frame.pack(fill=tk.BOTH, expand=True, pady=5, padx=10)

        # Add scrollbar for medicines text
        medicines_scrollbar = ttk.Scrollbar(self.medicines_frame)
        medicines_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.medicines_text = ClickableText(
            self.medicines_frame,
            wrap=tk.WORD,
            font=('Arial', 11),
            height=6,
            bg="white",
            state=tk.DISABLED, # Initially disabled
            yscrollcommand=medicines_scrollbar.set # Link scrollbar
        )
        self.medicines_text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT, padx=(5,0), pady=5)
        medicines_scrollbar.config(command=self.medicines_text.yview)

        # Save Button
        self.save_btn = ttk.Button(
            self.right_frame,
            text=self.translations["save_records"][self.language.get()], # Translated text
            command=self.save_to_records,
            style='Save.TButton' # Use style
        )
        self.save_btn.pack(pady=10)

    def create_language_selector(self):
        """Creates the radio buttons for language selection."""
        lang_frame = ttk.Frame(self.root, style='TFrame', padding=(0, 10)) # Use ttk Frame
        lang_frame.pack(side=tk.BOTTOM, fill=tk.X) # Fill X to center content

        # Inner frame to center the radio buttons
        center_frame = ttk.Frame(lang_frame, style='TFrame')
        center_frame.pack() # Pack in the middle

        self.language_label_widget = ttk.Label(center_frame, text=self.translations["language_label"][self.language.get()])
        self.language_label_widget.pack(side=tk.LEFT, padx=(0, 10))

        languages = [("English", "english"), ("हिंदी", "hindi"), ("తెలుగు", "telugu")]
        for text, lang in languages:
            rb = ttk.Radiobutton(
                center_frame,
                text=text,
                variable=self.language,
                value=lang,
                command=self.update_language, # Call update function on change
                style='TRadiobutton' # Use ttk style
            )
            rb.pack(side=tk.LEFT, padx=5)

    def get_translations(self):
        """Returns a dictionary containing translations for UI elements."""
        # Centralized dictionary for all UI text translations
        return {
            "title": {
                "english": "Hospital Management System",
                "hindi": "हॉस्पिटल मैनेजमेंट सिस्टम",
                "telugu": "హాస్పిటల్ మేనేజ్మెంట్ సిస్టమ్"
            },
            "patient_info": {
                "english": "Patient Information & Diagnosis", # Combined title
                "hindi": "रोगी की जानकारी और निदान",
                "telugu": "రోగి సమాచారం & రోగ నిర్ధారణ"
            },
            "diagnosis_report": {
                "english": "Diagnosis Report",
                "hindi": "निदान रिपोर्ट",
                "telugu": "రోగ నిర్ధారణ నివేదిక"
            },
            "symptoms": {
                "english": "Symptoms Checklist", # More descriptive
                "hindi": "लक्षण चेकलिस्ट",
                "telugu": "లక్షణాలు చెక్‌లిస్ట్"
            },
            "diagnose": {
                "english": "Diagnose",
                "hindi": "निदान करें",
                "telugu": "రోగ నిర్ధారణ"
            },
            "save_records": {
                "english": "Save Diagnosis", # Changed text
                "hindi": "निदान सहेजें",
                "telugu": "రోగ నిర్ధారణ సేవ్ చేయండి"
            },
            "predicted_condition": {
                "english": "Predicted Condition: ",
                "hindi": "संभावित स्थिति: ",
                "telugu": "అంచనా వ్యాధి: "
            },
            "severity": {
                "english": "Severity: ",
                "hindi": "गंभीरता: ",
                "telugu": "తీవ్రత: "
            },
            "remedies": {
                "english": "Recommended Remedies",
                "hindi": "सुझाए गए उपचार",
                "telugu": "సిఫార్సు చేసిన పరిష్కారాలు"
            },
            "medicines": {
                "english": "Recommended Medicines & Resources", # Added Resources
                "hindi": "सुझाई गई दवाएं और संसाधन",
                "telugu": "సిఫార్సు చేసిన మందులు & వనరులు"
            },
            "patient_name_label": {
                "english": "Patient Name:", "hindi": "रोगी का नाम:", "telugu": "రోగి పేరు:"
            },
            "age_label": {
                "english": "Age:", "hindi": "आयु:", "telugu": "వయస్సు:"
            },
            "sex_label": {
                "english": "Sex:", "hindi": "लिंग:", "telugu": "లింగం:"
            },
            "phone_label": {
                "english": "Phone:", "hindi": "फ़ोन:", "telugu": "ఫోన్:"
            },
            "language_label": {
                "english": "Language:", "hindi": "भाषा:", "telugu": "భాష:"
            },
            # --- New Translations ---
            "clear_button": {
                "english": "Clear Form", "hindi": "फ़ॉर्म साफ़ करें", "telugu": "ఫారమ్ క్లియర్ చేయండి"
            },
            "search_patient_title": {
                "english": "Search Patient", "hindi": "रोगी खोजें", "telugu": "రోగిని శోధించండి"
            },
             "patient_details_title": {
                "english": "Patient Details", "hindi": "रोगी का विवरण", "telugu": "రోగి వివరాలు"
            },
            "patient_id_label": {
                "english": "Patient ID:", "hindi": "रोगी आईडी:", "telugu": "రోగి ఐడి:"
            },
            "search_button": {
                "english": "Search", "hindi": "खोजें", "telugu": "శోధించండి"
            },
            "patient_not_found": {
                "english": "Patient ID not found.", "hindi": "रोगी आईडी नहीं मिला।", "telugu": "రోగి ఐడి కనుగొనబడలేదు."
            },
            "patient_loaded": {
                "english": "Patient details loaded.", "hindi": "रोगी का विवरण लोड किया गया।", "telugu": "రోగి వివరాలు లోడ్ చేయబడ్డాయి."
            },
            "enter_patient_id": {
                "english": "Please enter a numeric Patient ID.", "hindi": "कृपया एक संख्यात्मक रोगी आईडी दर्ज करें।", "telugu": "దయచేసి సంఖ్యా రోగి ఐడిని నమోదు చేయండి."
            }
            # Add other labels as needed
        }

    def get_treatment_db(self):
        """Returns a dictionary containing remedies, medicines, links, and severity for diseases."""
        # --- Content remains the same as previous version ---
        return {
            "Flu": {
                "remedies": {
                    "english": [
                        "Complete bed rest for 3-5 days",
                        "Stay hydrated with water, herbal teas, and electrolyte solutions",
                        "Use warm compresses for muscle pain relief",
                        "Take steamy showers to relieve nasal congestion",
                        "Use a humidifier to moisten dry air",
                        "Gargle with warm salt water to soothe throat"
                    ],
                    "hindi": [
                        "3-5 दिनों के लिए पूर्ण बिस्तर आराम",
                        "पानी, हर्बल चाय और इलेक्ट्रोलाइट समाधान के साथ हाइड्रेटेड रहें",
                        "मांसपेशियों में दर्द से राहत के लिए गर्म सेक का उपयोग करें",
                        "नाक की भीड़ से राहत के लिए भाप वाले शावर लें",
                        "सूखी हवा को नम करने के लिए ह्यूमिडिफायर का उपयोग करें",
                        "गले को शांत करने के लिए गर्म नमक के पानी से गरारे करें"
                    ],
                    "telugu": [
                        "3-5 రోజులు పూర్తి పడక విశ్రాంతి",
                        "నీరు, హెర్బల్ టీలు మరియు ఎలక్ట్రోలైట్ ద్రావణాలతో హైడ్రేటెడ్‌గా ఉండండి",
                        "కండరాల నొప్పి నుండి ఉపశమనం కోసం వెచ్చని కంప్రెస్‌లను ఉపయోగించండి",
                        "ముక్కు అత్యవసరాన్ని తగ్గించడానికి ఆవిరి షవర్‌లు తీసుకోండి",
                        "పొడి గాలిని తేమగా ఉంచడానికి హ్యూమిడిఫైయర్ ఉపయోగించండి",
                        "గొంతును శాంతపరచడానికి వేడి ఉప్పు నీటితో గార్గిల్ చేయండి"
                    ]
                },
                "medicines": {
                    "english": [
                        "Oseltamivir (Tamiflu) - 75mg twice daily for 5 days (as prescribed)",
                        "Ibuprofen - 200-400mg every 6-8 hours for pain/fever",
                        "Dextromethorphan - 10-20mg every 4-6 hours for cough",
                        "Phenylephrine - 10mg every 4 hours as decongestant",
                        "Chlorpheniramine - 4mg every 4-6 hours for allergies/runny nose",
                        "https://youtu.be/0AHC4X-ujwA", # Mayo Clinic
                        "https://www.cdc.gov/flu/treatment/index.html"
                    ],
                    "hindi": [
                        "ओसेल्टामिविर (टैमीफ्लू) - 5 दिनों के लिए दिन में दो बार 75mg (डॉक्टर के निर्देशानुसार)",
                        "इबुप्रोफेन - दर्द/बुखार के लिए हर 6-8 घंटे में 200-400mg",
                        "डेक्सट्रोमेथॉर्फन - खांसी के लिए हर 4-6 घंटे में 10-20mg",
                        "फेनिलेफ्राइन - डिकंजेस्टेंट के रूप में हर 4 घंटे में 10mg",
                        "क्लोरफेनिरामाइन - एलर्जी/बहती नाक के लिए हर 4-6 घंटे में 4mg",
                        "https://youtu.be/2hZSVj92eTI", # Hindi Health
                        "https://www.nhp.gov.in/flu-season_mtl"
                    ],
                    "telugu": [
                        "ఓసెల్టామివిర్ (టామిఫ్లూ) - 5 రోజుల పాటు రోజుకు రెండుసార్లు 75mg (వైద్యుని సూచనల ప్రకారం)",
                        "ఇబుప్రోఫెన్ - నొప్పి/జ్వరం కోసం ప్రతి 6-8 గంటలకు 200-400mg",
                        "డెక్స్ట్రోమెథోర్ఫాన్ - దగ్గు కోసం ప్రతి 4-6 గంటలకు 10-20mg",
                        "ఫెనైలెఫ్రిన్ - డికంజెస్టెంట్గా ప్రతి 4 గంటలకు 10mg",
                        "క్లోర్ఫెనిరామిన్ - అలెర్జీ/రన్నీ నోస్ కోసం ప్రతి 4-6 గంటలకు 4mg",
                        "https://youtu.be/abc123", # Telugu Health
                        "https://telugu.oneindia.com/health/flu-treatment-12345" # Example link, replace if needed
                    ]
                },
                "severity": {
                    "english": "Moderate to Severe", "hindi": "मध्यम से गंभीर", "telugu": "మధ్యస్థం నుండి తీవ్రమైన"
                }
            },
            "Common Cold": {
                 "remedies": {
                    "english": [
                        "Drink plenty of warm fluids (water, herbal tea, soup)",
                        "Get adequate rest (7-9 hours per night)",
                        "Use saline nasal drops or spray to relieve congestion",
                        "Gargle with warm salt water 2-3 times daily",
                        "Use a humidifier to moisten dry air in your room",
                        "Apply petroleum jelly to soothe irritated nose"
                    ],
                    "hindi": [
                        "भरपूर मात्रा में गर्म तरल पदार्थ पिएं (पानी, हर्बल चाय, सूप)",
                        "पर्याप्त आराम करें (रात में 7-9 घंटे)",
                        "कंजेशन से राहत के लिए सलाइन नेजल ड्रॉप्स या स्प्रे का उपयोग करें",
                        "दिन में 2-3 बार गर्म नमक के पानी से गरारे करें",
                        "अपने कमरे में सूखी हवा को नम करने के लिए ह्यूमिडिफायर का उपयोग करें",
                        "जलन वाली नाक को शांत करने के लिए पेट्रोलियम जेली लगाएं"
                    ],
                    "telugu": [
                        "పుష్కలంగా వెచ్చని ద్రవాలు త్రాగండి (నీరు, హెర్బల్ టీ, సూప్)",
                        "తగినంత విశ్రాంతి తీసుకోండి (రాత్రికి 7-9 గంటలు)",
                        "కంజెషన్ నుండి ఉపశమనం కోసం సైలిన్ నాసికా డ్రాప్స్ లేదా స్ప్రే ఉపయోగించండి",
                        "రోజుకు 2-3 సార్లు వేడి ఉప్పు నీటితో గొంతు శుభ్రం చేయండి",
                        "మీ గదిలో పొడి గాలిని తేమగా ఉంచడానికి హ్యూమిడిఫైయర్ ఉపయోగించండి",
                        "చికాకు కలిగించే ముక్కును శాంతపరచడానికి పెట్రోలియం జెల్లీ వేయండి"
                    ]
                },
                "medicines": {
                     "english": [
                        "Paracetamol - 500mg every 6 hours as needed for fever/pain",
                        "Chlorpheniramine - 4mg every 4-6 hours for allergies/runny nose",
                        "Phenylephrine - 10mg every 4 hours as decongestant",
                        "Dextromethorphan - 10-20mg every 4-6 hours for cough",
                        "Zinc supplements - 50-100mg daily for immune support",
                        "https://youtu.be/qjisqhL-XQo", # Cleveland Clinic
                        "https://www.mayoclinic.org/diseases-conditions/common-cold/symptoms-causes/syc-20351605"
                    ],
                    "hindi": [
                        "पैरासिटामोल - बुखार/दर्द के लिए आवश्यकतानुसार हर 6 घंटे में 500mg",
                        "क्लोरफेनिरामाइन - एलर्जी/बहती नाक के लिए हर 4-6 घंटे में 4mg",
                        "फेनिलेफ्राइन - डिकंजेस्टेंट के रूप में हर 4 घंटे में 10mg",
                        "डेक्सट्रोमेथॉर्फन - खांसी के लिए हर 4-6 घंटे में 10-20mg",
                        "जिंक सप्लीमेंट्स - प्रतिरक्षा समर्थन के लिए दैनिक 50-100mg",
                        "https://youtu.be/xyz456", # Hindi Health Tips
                        "https://www.onlymyhealth.com/hindi/common-cold-treatment-123" # Example link
                    ],
                    "telugu": [
                        "పారాసిటమోల్ - జ్వరం/నొప్పి కోసం అవసరమైనప్పుడు ప్రతి 6 గంటలకు 500mg",
                        "క్లోర్ఫెనిరామిన్ - అలెర్జీ/రన్నీ నోస్ కోసం ప్రతి 4-6 గంటలకు 4mg",
                        "ఫెనైలెఫ్రిన్ - డికంజెస్టెంట్గా ప్రతి 4 గంటలకు 10mg",
                        "డెక్స్ట్రోమెథోర్ఫాన్ - దగ్గు కోసం ప్రతి 4-6 గంటలకు 10-20mg",
                        "జింక్ సప్లిమెంట్స్ - రోగనిరోధక మద్దతు కోసం రోజువారీ 50-100mg",
                        "https://youtu.be/def789", # Telugu Health
                        "https://telugu.samayam.com/health/common-cold-treatment-123" # Example link
                    ]
                },
                "severity": {
                    "english": "Mild", "hindi": "हल्का", "telugu": "తేలికపాటి"
                }
            },
            "Migraine": {
                "remedies": {
                    "english": ["Rest in a dark, quiet room", "Apply cold compress to forehead", "Stay hydrated", "Avoid triggers (certain foods, stress)"],
                    "hindi": ["अंधेरे, शांत कमरे में आराम करें", "माथे पर ठंडा सेक लगाएं", "हाइड्रेटेड रहें", "ट्रिगर्स से बचें (कुछ खाद्य पदार्थ, तनाव)"],
                    "telugu": ["చీకటి, నిశ్శబ్ద గదిలో విశ్రాంతి తీసుకోండి", "నుదిటిపై చల్లని కంప్రెస్ వేయండి", "హైడ్రేటెడ్‌గా ఉండండి", "ట్రిగ్గర్‌లను నివారించండి (కొన్ని ఆహారాలు, ఒత్తిడి)"]
                },
                "medicines": {
                    "english": ["Sumatriptan (prescription)", "Ibuprofen/Naproxen", "Anti-nausea medication (if needed)", "https://www.mayoclinic.org/diseases-conditions/migraine-headache/diagnosis-treatment/drc-20360207"],
                    "hindi": ["सुमाट्रिप्टान (प्रिस्क्रिप्शन)", "इबुप्रोफेन/नेप्रोक्सन", "मतली-रोधी दवा (यदि आवश्यक हो)", "https://www.onlymyhealth.com/hindi/migraine-treatment-123"], # Example
                    "telugu": ["సుమాట్రిప్టాన్ (ప్రిస్క్రిప్షన్)", "ఇబుప్రోఫెన్/నాప్రోక్సెన్", "వికారం నిరోధక మందు (అవసరమైతే)", "https://telugu.samayam.com/health/migraine-treatment-123"] # Example
                },
                "severity": {"english": "Moderate to Severe", "hindi": "मध्यम से गंभीर", "telugu": "మధ్యస్థం నుండి తీవ్రమైన"}
            },
            "Heart Condition": {
                 "remedies": {
                    "english": ["Follow doctor's advice strictly", "Maintain healthy diet (low salt, low fat)", "Regular, gentle exercise (as approved)", "Stress management techniques"],
                    "hindi": ["डॉक्टर की सलाह का सख्ती से पालन करें", "स्वस्थ आहार बनाए रखें (कम नमक, कम वसा)", "नियमित, हल्का व्यायाम (अनुमोदित)", "तनाव प्रबंधन तकनीक"],
                    "telugu": ["వైద్యుని సలహాను ఖచ్చితంగా పాటించండి", "ఆరోగ్యకరమైన ఆహారం తీసుకోండి (తక్కువ ఉప్పు, తక్కువ కొవ్వు)", "క్రమం తప్పకుండా, సున్నితమైన వ్యాయామం (ఆమోదించినట్లు)", "ఒత్తిడి నిర్వహణ పద్ధతులు"]
                },
                "medicines": {
                    "english": ["Varies greatly (Aspirin, Statins, Beta-blockers, etc. - prescription only)", "Consult cardiologist", "https://www.cdc.gov/heartdisease/prevention.htm", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3D4Z4S-L3Y5jY7"], # Placeholder YT
                    "hindi": ["बहुत भिन्न होता है (एस्पिरिन, स्टैटिन, बीटा-ब्लॉकर्स, आदि - केवल प्रिस्क्रिप्शन)", "कार्डियोलॉजिस्ट से सलाह लें", "https://www.google.com/search?q=https://www.apollohospitals.com/hi/diseases-and-conditions/heart-disease/", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3D4Z4S-L3Y5jY7"],
                    "telugu": ["చాలా మారుతూ ఉంటుంది (ఆస్పిరిన్, స్టాటిన్స్, బీటా-బ్లాకర్స్, మొదలైనవి - ప్రిస్క్రిప్షన్ మాత్రమే)", "కార్డియాలజిస్ట్‌ను సంప్రదించండి", "https://telugu.oneindia.com/health/heart-disease-prevention-123", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3D4Z4S-L3Y5jY7"] # Placeholder YT, Example link
                },
                "severity": {"english": "Varies (Often Serious)", "hindi": "भिन्न होता है (अक्सर गंभीर)", "telugu": "మారుతూ ఉంటుంది (తరచుగా తీవ్రమైనది)"}
            },
            "Motion Sickness": {
                "remedies": {
                    "english": ["Look at the horizon", "Get fresh air", "Avoid heavy meals before travel", "Acupressure bands"],
                    "hindi": ["क्षितिज को देखें", "ताजी हवा लें", "यात्रा से पहले भारी भोजन से बचें", "एक्यूप्रेशर बैंड"],
                    "telugu": ["హోరిజోన్‌ను చూడండి", "తాజా గాలి పీల్చుకోండి", "ప్రయాణానికి ముందు భారీ భోజనం మానుకోండి", "ఆక్యుప్రెషర్ బ్యాండ్లు"]
                },
                "medicines": {
                    "english": ["Dimenhydrinate (Dramamine)", "Meclizine (Bonine)", "Scopolamine patch (prescription)", "https://www.google.com/search?q=https://www.nidcd.nih.gov/health/motion-sickness", "http://www.youtube.com/watch?v=gKhE3CMz7Sk"],
                    "hindi": ["डाइमेनहाइड्रिनेट (ड्रामामाइन)", "मेक्लिज़िन (बोनाइन)", "स्कोपोलामाइन पैच (प्रिस्क्रिप्शन)", "https://www.google.com/search?q=https://www.askapollo.com/hi/diseases-conditions/motion-sickness", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM2"],
                    "telugu": ["డైమెన్‌హైడ్రినేట్ (డ్రామామైన్)", "మెక్లిజైన్ (బోనైన్)", "స్కోపోలమైన్ ప్యాచ్ (ప్రిస్క్రిప్షన్)", "https://www.google.com/search?q=https://www.practo.com/healthfeed/prayana-anarogyam-motion-sickness-nivarana-mariyu-chikitsa-in-telugu-43756", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM1"]
                },
                "severity": {"english": "Mild to Moderate", "hindi": "हल्का से मध्यम", "telugu": "తేలికపాటి నుండి మధ్యస్థం"}
            },
            "Inflammation": { # Note: Inflammation is often a symptom
                "remedies": {
                    "english": ["Anti-inflammatory diet (fruits, vegetables, fish)", "Cold/hot compress", "Rest affected area", "Identify and treat underlying cause"],
                    "hindi": ["एंटी-इंफ्लेमेटरी आहार (फल, सब्जियां, मछली)", "ठंडा/गर्म सेक", "प्रभावित क्षेत्र को आराम दें", "मूल कारण की पहचान और उपचार करें"],
                    "telugu": ["యాంటీ ఇన్ఫ్లమేటరీ డైట్ (పండ్లు, కూరగాయలు, చేపలు)", "చల్లని/వేడి కంప్రెస్", "ప్రభావిత ప్రాంతానికి విశ్రాంతి ఇవ్వండి", "అంతర్లీన కారణాన్ని గుర్తించి చికిత్స చేయండి"]
                },
                "medicines": {
                    "english": ["Ibuprofen/Naproxen (NSAIDs)", "Consult doctor for underlying cause", "https://www.google.com/search?q=https://www.niams.nih.gov/health-topics/inflammation", "http://www.youtube.com/watch?v=fwv4lp8vxEY"],
                    "hindi": ["इबुप्रोफेन/नेप्रोक्सन (NSAIDs)", "मूल कारण के लिए डॉक्टर से सलाह लें", "https://www.google.com/search?q=https://www.askapollo.com/hi/diseases-conditions/inflammation", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM5"],
                    "telugu": ["ఇబుప్రోఫెన్/నాప్రోక్సెన్ (NSAIDs)", "అంతర్లీన కారణం కోసం వైద్యుడిని సంప్రదించండి", "https://www.google.com/search?q=https://www.practo.com/healthfeed/vapu-inflammation-karanalu-lakshanalu-mariyu-chikitsa-in-telugu-43788", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM4"]
                },
                "severity": {"english": "Varies (Depends on cause)", "hindi": "भिन्न होता है (कारण पर निर्भर करता है)", "telugu": "మారుతూ ఉంటుంది (కారణంపై ఆధారపడి ఉంటుంది)"}
            },
            "Conjunctivitis": { # Pink Eye
                "remedies": {
                    "english": ["Warm compress", "Avoid touching eyes", "Wash hands frequently", "Discard used tissues", "Avoid sharing towels/makeup"],
                    "hindi": ["गर्म सेक", "आंखों को छूने से बचें", "बार-बार हाथ धोएं", "इस्तेमाल किए गए टिश्यू फेंक दें", "तौलिए/मेकअप साझा करने से बचें"],
                    "telugu": ["వెచ్చని కంప్రెస్", "కళ్లను తాకడం మానుకోండి", "తరచుగా చేతులు కడుక్కోండి", "ఉపయోగించిన టిష్యూలను పారవేయండి", "టవల్స్/మేకప్ పంచుకోవడం మానుకోండి"]
                },
                "medicines": {
                    "english": ["Antibiotic eye drops (if bacterial)", "Antihistamine eye drops (if allergic)", "Artificial tears", "https://www.cdc.gov/conjunctivitis/index.html", "http://www.youtube.com/watch?v=qEg7sJKRhXI"],
                    "hindi": ["एंटीबायोटिक आई ड्रॉप्स (यदि बैक्टीरियल)", "एंटीहिस्टामाइन आई ड्रॉप्स (यदि एलर्जिक)", "आर्टिफिशियल टियर्स", "https://www.google.com/search?q=https://www.askapollo.com/hi/diseases-conditions/conjunctivitis", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM8"],
                    "telugu": ["యాంటీబయాటిక్ ఐ డ్రాప్స్ (బ్యాక్టీరియా అయితే)", "యాంటీహిస్టమైన్ ఐ డ్రాప్స్ (అలెర్జీ అయితే)", "ఆర్టిఫిషియల్ టియర్స్", "https://www.google.com/search?q=https://www.practo.com/healthfeed/kandlakalaka-conjunctivitis-karanalu-lakshanalu-mariyu-chikitsa-in-telugu-43642", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3Drbo94OIFNeM7"]
                },
                "severity": {"english": "Mild to Moderate", "hindi": "हल्का से मध्यम", "telugu": "తేలికపాటి నుండి మధ్యస్థం"}
            },
            "Ear Infection": {
                "remedies": {
                    "english": ["Warm compress on the ear", "Keep ear dry", "Rest", "Avoid inserting objects into ear"],
                    "hindi": ["कान पर गर्म सेक", "कान को सूखा रखें", "आराम करें", "कान में वस्तुएं डालने से बचें"],
                    "telugu": ["చెవిపై వెచ్చని కంప్రెస్", "చెవిని పొడిగా ఉంచండి", "విశ్రాంతి", "చెవిలో వస్తువులు చొప్పించడం మానుకోండి"]
                },
                "medicines": {
                    "english": ["Pain relievers (Acetaminophen/Ibuprofen)", "Antibiotic ear drops (if bacterial, prescribed)", "Decongestants (sometimes)", "https://www.nidcd.nih.gov/health/ear-infections-children", "http://www.youtube.com/watch?v=XtgimNDHz7s"],
                    "hindi": ["दर्द निवारक (एसिटामिनोफेन/इबुप्रोफेन)", "एंटीबायोटिक इयर ड्रॉप्स (यदि बैक्टीरियल, निर्धारित)", "डिकंजेस्टेंट्स (कभी-कभी)", "https://www.google.com/search?q=https://www.askapollo.com/hi/diseases-conditions/ear-infection", "http://www.youtube.com/watch?v=XtgimNDHz7s"], # Reusing YT link
                    "telugu": ["నొప్పి నివారణలు (ఎసిటమైనోఫెన్/ఇబుప్రోఫెన్)", "యాంటీబయాటిక్ ఇయర్ డ్రాప్స్ (బ్యాక్టీరియా అయితే, సూచించిన)", "డికంజెస్టెంట్లు (కొన్నిసార్లు)", "https://www.google.com/search?q=https://www.practo.com/healthfeed/chevi-infection-karanalu-lakshanalu-mariyu-chikitsa-in-telugu-43638", "https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3DbP4vj-PWG0o0"]
                },
                "severity": {"english": "Mild to Moderate", "hindi": "हल्का से मध्यम", "telugu": "తేలికపాటి నుండి మధ్యస్థం"}
            },
            "Dehydration": {
                 "remedies": {
                    "english": ["Drink plenty of water", "Oral rehydration solutions (ORS)", "Avoid caffeine and alcohol", "Eat water-rich foods (fruits, vegetables)"],
                    "hindi": ["खूब पानी पिएं", "ओरल रिहाइड्रेशन सॉल्यूशंस (ORS)", "कैफीन और शराब से बचें", "पानी युक्त खाद्य पदार्थ खाएं (फल, सब्जियां)"],
                    "telugu": ["పుష్కలంగా నీరు త్రాగండి", "ఓరల్ రీహైడ్రేషన్ సొల్యూషన్స్ (ORS)", "కెఫిన్ మరియు ఆల్కహాల్ మానుకోండి", "నీరు అధికంగా ఉండే ఆహారాలు తినండి (పండ్లు, కూరగాయలు)"]
                },
                "medicines": {
                    "english": ["Usually treated with fluids", "IV fluids in severe cases", "Treat underlying cause (vomiting, diarrhea)", "https://www.google.com/search?q=https://www.mayoclinic.org/diseases-conditions/dehydration/diagnosis-treatment/drc-20355589", "http://www.youtube.com/watch?v=4Rcb0ZTGPek"],
                    "hindi": ["आमतौर पर तरल पदार्थों से इलाज किया जाता है", "गंभीर मामलों में IV तरल पदार्थ", "मूल कारण का इलाज करें (उल्टी, दस्त)", "https://www.google.com/search?q=https://www.askapollo.com/hi/diseases-conditions/dehydration", "http://www.youtube.com/watch?v=4Rcb0ZTGPek"], # Reusing YT link
                    "telugu": ["సాధారణంగా ద్రవాలతో చికిత్స చేస్తారు", "తీవ్రమైన సందర్భాల్లో IV ద్రవాలు", "అంతర్లీన కారణానికి చికిత్స చేయండి (వాంతులు, విరేచనాలు)", "https://www.google.com/search?q=https://www.practo.com/healthfeed/dehydration-sareeramlo-neeti-koratha-karanalu-lakshanalu-mariyu-chikitsa-in-telugu-43644", "http://www.youtube.com/watch?v=S2_jtNJUKe0"]
                },
                "severity": {"english": "Mild to Severe", "hindi": "हल्का से गंभीर", "telugu": "తేలికపాటి నుండి తీవ్రమైన"}
            },
            "General Illness": { # Fallback
                "remedies": {
                    "english": [
                        "Monitor symptoms closely for any worsening",
                        "Get plenty of rest (7-9 hours per night)",
                        "Maintain good hydration with water and electrolytes",
                        "Eat nutritious, easily digestible foods",
                        "Practice good hygiene to prevent spread"
                    ],
                    "hindi": [
                        "किसी भी बिगड़ती स्थिति के लिए लक्षणों की बारीकी से निगरानी करें",
                        "भरपूर आराम करें (रात में 7-9 घंटे)",
                        "पानी और इलेक्ट्रोलाइट्स के साथ अच्छी हाइड्रेशन बनाए रखें",
                        "पौष्टिक, आसानी से पचने वाले खाद्य पदार्थ खाएं",
                        "फैलने से रोकने के लिए अच्छी स्वच्छता का अभ्यास करें"
                    ],
                    "telugu": [
                        "ఏదైనా మరింత అధ్వాన్నమయ్యే లక్షణాలను జాగ్రత్తగా పర్యవేక్షించండి",
                        "పుష్కలంగా విశ్రాంతి తీసుకోండి (రాత్రికి 7-9 గంటలు)",
                        "నీరు మరియు ఎలక్ట్రోలైట్‌లతో మంచి హైడ్రేషన్ నిర్వహించండి",
                        "పోషకాహారం, సులభంగా జీర్ణమయ్యే ఆహారాలు తినండి",
                        "వ్యాప్తి నిరోధించడానికి మంచి హైజీన్ పాటించండి"
                    ]
                },
                "medicines": {
                    "english": [
                        "Consult doctor for proper diagnosis and treatment",
                        "Paracetamol - 500mg every 6 hours if fever/pain present",
                        "Antihistamines if allergic symptoms present",
                        "Oral rehydration solutions if dehydration possible",
                        "https://www.who.int/health-topics",
                        "https://www.youtube.com/results?search_query=best%20videos%20for%20common%20cold&sp=EgIQAQ%253D%253D"
                    ],
                    "hindi": [
                        "उचित निदान और उपचार के लिए डॉक्टर से परामर्श करें",
                        "पैरासिटामोल - बुखार/दर्द होने पर हर 6 घंटे में 500mg",
                        "एंटीहिस्टामाइन यदि एलर्जी के लक्षण मौजूद हों",
                        "ओरल रिहाइड्रेशन सॉल्यूशन यदि डिहाइड्रेशन संभव हो",
                        "https://www.google.com/search?q=https://www.nhp.gov.in/health-topics",
                        "https://m.youtube.com/watch?v=3HegYcUJohs&pp=ygUOI2ludGVncmF0ZWR5b2c%3D"
                    ],
                    "telugu": [
                        "సరైన రోగ నిర్ధారణ మరియు చికిత్స కోసం వైద్యుడిని సంప్రదించండి",
                        "పారాసిటమోల్ - జ్వరం/నొప్పి ఉంటే ప్రతి 6 గంటలకు 500mg",
                        "అలెర్జీ లక్షణాలు ఉంటే యాంటీహిస్టమైన్‌లు",
                        "నిర్జలీకరణ సాధ్యమైతే నోటి పునర్జలకరణ ద్రావణాలు",
                        "https://www.google.com/search?q=https://arogyakeralam.gov.in/index.php/information/health-education/",
                        "https://m.youtube.com/watch?v=HV9yz2izQWU"
                    ]
                },
                "severity": {
                    "english": "Mild to Moderate", "hindi": "हल्का से मध्यम", "telugu": "తేలికపాటి నుండి మధ్యస్థం"
                }
            }
             # --- Add other diseases as needed ---
        }
        # --- UPDATED LINKS END HERE ---


    def update_language(self):
        """Updates the UI text elements based on the selected language."""
        lang = self.language.get()

        # Update window title and header
        self.root.title(f"{self.translations['title'][lang]} - KG Reddy College")
        if hasattr(self, 'title_label'):
            self.title_label.config(text=self.translations["title"][lang])

        # Update frame labels
        if hasattr(self, 'left_frame'):
            self.left_frame.config(text=self.translations["patient_info"][lang])
        if hasattr(self, 'right_frame'):
            self.right_frame.config(text=self.translations["diagnosis_report"][lang])
        if hasattr(self, 'symptoms_frame'):
            self.symptoms_frame.config(text=self.translations["symptoms"][lang])
        if hasattr(self, 'remedies_frame'):
            self.remedies_frame.config(text=self.translations["remedies"][lang])
        if hasattr(self, 'medicines_frame'):
            self.medicines_frame.config(text=self.translations["medicines"][lang])
        # --- Update new frame labels ---
        if hasattr(self, 'search_frame'): # Check if search_frame exists
             self.search_frame['text'] = self.translations["search_patient_title"][lang]
        if hasattr(self, 'patient_details_frame'): # Check if patient_details_frame exists
             self.patient_details_frame['text'] = self.translations["patient_details_title"][lang]


        # Update patient form labels (using stored references)
        if hasattr(self, 'patient_name_label'):
            self.patient_name_label.config(text=self.translations["patient_name_label"][lang])
        if hasattr(self, 'age_label'):
            self.age_label.config(text=self.translations["age_label"][lang])
        if hasattr(self, 'sex_label'):
            self.sex_label.config(text=self.translations["sex_label"][lang])
        if hasattr(self, 'phone_label'):
            self.phone_label.config(text=self.translations["phone_label"][lang])
        # --- Update new search labels ---
        if hasattr(self, 'search_id_label'):
             self.search_id_label.config(text=self.translations["patient_id_label"][lang])


        # Update symptom checkbox labels
        for symptom_key, checkbox in self.symptom_checkboxes:
            translated_name = self.predictor.get_symptom_name(symptom_key, lang)
            checkbox.config(text=translated_name)

        # Update button labels
        if hasattr(self, 'diagnose_btn'):
            self.diagnose_btn.config(text=self.translations["diagnose"][lang])
        if hasattr(self, 'save_btn'):
            self.save_btn.config(text=self.translations["save_records"][lang])
        # --- Update new button labels ---
        if hasattr(self, 'clear_btn'):
             self.clear_btn.config(text=self.translations["clear_button"][lang])
        if hasattr(self, 'search_btn'):
             self.search_btn.config(text=self.translations["search_button"][lang])


        # Update report labels (clear existing text if no diagnosis yet)
        if hasattr(self, 'disease_label'):
             predicted_text = self.translations['predicted_condition'][lang]
             if self.current_diagnosis:
                 predicted_text += self.current_diagnosis
             self.disease_label.config(text=predicted_text)

        if hasattr(self, 'severity_label'):
            severity_text = self.translations['severity'][lang]
            if self.current_diagnosis:
                 treatment = self.treatment_db.get(self.current_diagnosis, self.treatment_db["General Illness"])
                 severity = treatment.get("severity", {}).get(lang, "Unknown")
                 severity_text += severity
            self.severity_label.config(text=severity_text)

        # Update language selector label
        if hasattr(self, 'language_label_widget'):
            self.language_label_widget.config(text=self.translations["language_label"][lang])


        # Re-display diagnosis if one exists, to update remedy/medicine text
        if self.current_diagnosis:
            self.display_diagnosis(self.current_diagnosis)

    def diagnose_patient(self):
        """Performs disease prediction based on selected symptoms."""
        # Basic input validation - Use patient_name_entry now
        if not self.patient_name_entry.get():
            messagebox.showwarning("Input Error", "Please enter patient name or load existing patient.")
            return

        # Get selected symptoms
        symptoms = [var.get() for var in self.symptom_vars]
        if not any(symptoms): # Check if at least one symptom is selected
            messagebox.showwarning("Input Error", "Please select at least one symptom")
            return

        # Predict the disease
        disease = self.predictor.predict(symptoms)
        self.current_diagnosis = disease # Store the current diagnosis
        # Display the results
        self.display_diagnosis(disease)

        # Optionally set focus to the report area
        # self.remedies_text.focus_set()

    def display_diagnosis(self, disease):
        """Displays the predicted disease, remedies, and medicines in the report section."""
        lang = self.language.get()
        # Get treatment info for the predicted disease, fallback to General Illness
        treatment = self.treatment_db.get(disease, self.treatment_db["General Illness"])

        # Update disease label
        self.disease_label.config(
            text=f"{self.translations['predicted_condition'][lang]}{disease}"
        )

        # Update severity label
        severity = treatment.get("severity", {}).get(lang, "Unknown")
        self.severity_label.config(
            text=f"{self.translations['severity'][lang]}{severity}"
        )

        # Update remedies text area
        remedies = treatment.get("remedies", {}).get(lang, ["No information available"])
        self.remedies_text.config(state=tk.NORMAL) # Enable editing
        self.remedies_text.delete(1.0, tk.END) # Clear previous content
        # Insert remedies with bullet points
        for item in remedies:
            self.remedies_text.insert(tk.END, f"• {item}\n")
        self.remedies_text.config(state=tk.DISABLED) # Disable editing

        # Update medicines text area (using ClickableText)
        medicines = treatment.get("medicines", {}).get(lang, ["No information available"])
        self.medicines_text.config(state=tk.NORMAL) # Enable editing
        self.medicines_text.delete(1.0, tk.END) # Clear previous content
        self.medicines_text.links.clear() # Clear previous links
        # Insert medicines and add links for URLs
        for item in medicines:
            if item.startswith(("http://", "https://", "www.")):
                # If it's a URL, make it clickable
                link_text = f"• {item}\n"
                start_index = self.medicines_text.index(tk.INSERT)
                self.medicines_text.insert(tk.END, link_text)
                # Calculate indices more robustly
                # Start index for the tag is after the bullet point and space
                tag_start = f"{start_index} + 2c"
                # End index for the tag is before the newline
                tag_end = f"{self.medicines_text.index(tk.INSERT)} - 1c"
                self.medicines_text.add_link(tag_start, tag_end, item)
            else:
                # Otherwise, insert as plain text
                self.medicines_text.insert(tk.END, f"• {item}\n")
        self.medicines_text.config(state=tk.DISABLED) # Disable editing

    def save_to_records(self):
        """Saves the current patient info and diagnosis to the database."""
        # Check if there is a diagnosis to save
        if not self.current_diagnosis:
            messagebox.showwarning("Error", "No diagnosis to save. Please run Diagnose first.")
            return

        # Get patient details from entry fields
        name = self.patient_name_entry.get()
        age = self.patient_age_entry.get()
        sex = self.patient_sex_combo.get()
        phone = self.patient_phone_entry.get() # Get phone number

        # Validate required fields (at least name)
        if not name:
            messagebox.showwarning("Error", "Patient name is required to save record.")
            return

        # --- Logic to handle existing vs new patient ---
        patient_id_to_save = self.current_patient_id # Use loaded ID if available

        if not patient_id_to_save: # If no patient was loaded via search, add new
             # Add patient to the database
             patient_id_to_save = self.db.add_patient(
                 name=name,
                 age=age, # db function handles validation
                 sex=sex,
                 phone=phone
                 # Add address and email later if needed
             )
             # Check if patient was added successfully
             if not patient_id_to_save:
                 # Error message is shown by add_patient
                 return
             else:
                 # Update the search field with the new ID and store it
                 self.patient_id_entry.delete(0, tk.END)
                 self.patient_id_entry.insert(0, str(patient_id_to_save))
                 self.current_patient_id = patient_id_to_save
                 messagebox.showinfo("Patient Added", f"New patient added with ID: {patient_id_to_save}")
        # --- End existing/new patient logic ---


        # Get selected symptoms in the current language
        selected_symptoms = [
            self.predictor.get_symptom_name(self.predictor.symptoms[i], self.language.get())
            for i, var in enumerate(self.symptom_vars)
            if var.get() == 1
        ]

        # Get remedies and medicines text
        remedies = self.remedies_text.get(1.0, tk.END).strip()
        # Get medicines text (without link tags, just the text content)
        medicines = self.medicines_text.get(1.0, tk.END).strip()

        # Format the treatment string
        treatment_details = f"Remedies:\n{remedies}\n\nMedicines:\n{medicines}"

        # Add the medical record to the database using the determined patient ID
        record_id = self.db.add_medical_record(
            patient_id=patient_id_to_save,
            symptoms=", ".join(selected_symptoms), # Save symptoms as comma-separated string
            diagnosis=self.current_diagnosis,
            treatment=treatment_details
        )

        # Show success or error message
        if record_id:
            messagebox.showinfo("Success", f"Medical record saved successfully for patient ID: {patient_id_to_save}")
            # Optionally clear only symptoms and diagnosis after saving
            # self.clear_diagnosis_fields()
        else:
            messagebox.showerror("Error", "Failed to save medical record")

    # --- NEW: Search Patient Method ---
    def search_patient(self):
        """Searches for a patient by ID and loads their details."""
        lang = self.language.get()
        patient_id_str = self.patient_id_entry.get()

        if not patient_id_str.isdigit():
            messagebox.showwarning("Input Error", self.translations["enter_patient_id"][lang])
            return

        patient_id = int(patient_id_str)
        patient_data = self.db.get_patient(patient_id)

        if patient_data:
            # Patient found, populate fields
            # Indices based on get_patient SELECT *:
            # 0: patient_id, 1: name, 2: age, 3: sex, 4: address, 5: phone, 6: email, 7: reg_date
            self.clear_fields() # Clear everything first

            # Repopulate search ID
            self.patient_id_entry.insert(0, str(patient_data[0]))

            # Populate details
            self.patient_name_entry.insert(0, patient_data[1] or "")
            self.patient_age_entry.insert(0, str(patient_data[2] or ""))
            self.patient_sex_combo.set(patient_data[3] or "")
            self.patient_phone_entry.insert(0, patient_data[5] or "")
            # Store the loaded patient ID
            self.current_patient_id = patient_data[0]
            messagebox.showinfo("Patient Found", self.translations["patient_loaded"][lang])

        else:
            # Patient not found
            messagebox.showwarning("Not Found", self.translations["patient_not_found"][lang])
            # Clear details form but keep the searched ID
            self.clear_fields(keep_search_id=True)


    # --- UPDATED: Clear Fields Method ---
    def clear_fields(self, keep_search_id=False):
         """Clears all input fields and the report section."""
         # Clear patient details
         if not keep_search_id:
             self.patient_id_entry.delete(0, tk.END)
             self.current_patient_id = None # Reset loaded patient ID

         self.patient_name_entry.delete(0, tk.END)
         self.patient_age_entry.delete(0, tk.END)
         self.patient_sex_combo.set('') # Clear combobox
         self.patient_phone_entry.delete(0, tk.END)

         # Deselect all symptom checkboxes
         for var in self.symptom_vars:
             var.set(0)

         # Clear report section
         self.current_diagnosis = None
         lang = self.language.get()
         self.disease_label.config(text=self.translations['predicted_condition'][lang])
         self.severity_label.config(text=self.translations['severity'][lang])

         self.remedies_text.config(state=tk.NORMAL)
         self.remedies_text.delete(1.0, tk.END)
         self.remedies_text.config(state=tk.DISABLED)

         self.medicines_text.config(state=tk.NORMAL)
         self.medicines_text.delete(1.0, tk.END)
         self.medicines_text.links.clear()
         self.medicines_text.config(state=tk.DISABLED)


    def run(self):
        """Starts the Tkinter main event loop and closes the database on exit."""
        self.root.mainloop()
        # Ensure database connection is closed when the app exits
        self.db.close()

# Main execution block
if __name__ == "__main__":
    root = tk.Tk()
    app = HospitalApp(root)
    app.run()
