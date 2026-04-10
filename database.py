import sqlite3
from sqlite3 import Error
from tkinter import messagebox # Required for error popups within the class

class Database:
    """Handles database operations for the hospital management system."""
    def __init__(self, db_file="hospital.db"):
        """Initializes the database connection and creates tables if they don't exist."""
        self.conn = None
        try:
            # Connect to the SQLite database (allow access from different threads if needed later)
            self.conn = sqlite3.connect(db_file, check_same_thread=False)
            # Enable foreign key constraint enforcement
            self.conn.execute("PRAGMA foreign_keys = ON")
            # Create necessary tables
            self.create_tables()
            print("Database connection successful and tables ensured.") # Debug print
        except Error as e:
            print(f"Database connection error: {e}") # Print error
            messagebox.showerror("Database Error", f"Error connecting to database: {e}")
            # Optionally raise the error or exit if connection fails
            # raise e

    def create_tables(self):
        """Creates the necessary tables in the database if they don't already exist."""
        if not self.conn:
            print("Cannot create tables: No database connection.")
            return
        # SQL commands to create tables if they don't exist
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
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id) ON DELETE SET NULL
            );""",
            # Added ON DELETE CASCADE/SET NULL for better data integrity
            """CREATE TABLE IF NOT EXISTS medical_history (
                record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                visit_date TEXT DEFAULT CURRENT_TIMESTAMP,
                symptoms TEXT,
                diagnosis TEXT,
                treatment TEXT,
                doctor_id INTEGER,
                FOREIGN KEY (patient_id) REFERENCES patients (patient_id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id) ON DELETE SET NULL
            );"""
        ]
        cursor = None
        try:
            cursor = self.conn.cursor()
            # Execute each SQL command to create tables
            for command in sql_commands:
                cursor.execute(command)
            # Commit the changes to the database
            self.conn.commit()
        except Error as e:
            print(f"Database Error creating tables: {e}")
            messagebox.showerror("Database Error", f"Error creating tables: {e}")
            # No rollback needed for CREATE TABLE IF NOT EXISTS
        finally:
             if cursor: cursor.close() # Ensure cursor is closed

    def add_patient(self, name, age=None, sex=None, address=None, phone=None, email=None):
        """Adds a new patient record to the database."""
        if not self.conn:
             messagebox.showerror("Database Error", "No database connection.")
             return None
        sql = "INSERT INTO patients(name, age, sex, address, phone, email) VALUES(?,?,?,?,?,?)"
        cursor = None # Initialize cursor
        try:
            cursor = self.conn.cursor()
            # Ensure age is an integer or None
            age_val = int(age) if age and str(age).isdigit() else None
            cursor.execute(sql, (name, age_val, sex, address, phone, email))
            self.conn.commit()
            last_id = cursor.lastrowid
            print(f"Patient added successfully with ID: {last_id}") # Debug print
            return last_id
        except ValueError:
             # This error occurs if age is not a valid number when converting
             messagebox.showerror("Input Error", "Age must be a number.")
             return None
        except Error as e:
            print(f"Database Error adding patient: {e}") # Debug print
            messagebox.showerror("Database Error", f"Error adding patient: {e}")
            if self.conn: self.conn.rollback() # Rollback changes on error
            return None
        finally:
            if cursor: cursor.close() # Ensure cursor is closed

    def get_patient(self, patient_id):
        """Retrieves a patient record by their ID."""
        if not self.conn:
             messagebox.showerror("Database Error", "No database connection.")
             return None
        sql = "SELECT * FROM patients WHERE patient_id = ?"
        cursor = None
        try:
            # Ensure patient_id is an integer before querying
            patient_id_int = int(patient_id)
            cursor = self.conn.cursor()
            cursor.execute(sql, (patient_id_int,))
            # Return the fetched patient data (ID, Name, Age, Sex, Address, Phone, Email, RegDate)
            return cursor.fetchone()
        except ValueError:
             # This error occurs if patient_id is not a valid number
             messagebox.showerror("Input Error", "Patient ID must be a number.")
             return None
        except Error as e:
            print(f"Database Error getting patient: {e}")
            messagebox.showerror("Database Error", f"Error getting patient: {e}")
            return None
        finally:
            if cursor: cursor.close()

    def add_medical_record(self, patient_id, symptoms, diagnosis, treatment, doctor_id=None):
        """Adds a new medical record for a patient."""
        if not self.conn:
             messagebox.showerror("Database Error", "No database connection.")
             return None
        sql = "INSERT INTO medical_history(patient_id, symptoms, diagnosis, treatment, doctor_id) VALUES(?,?,?,?,?)"
        cursor = None
        try:
            # --- Ensure patient_id is an integer ---
            patient_id_int = int(patient_id)
            print(f"Executing add_medical_record for patient_id: {patient_id_int}") # Debug
            cursor = self.conn.cursor()
            cursor.execute(sql, (patient_id_int, symptoms, diagnosis, treatment, doctor_id))
            self.conn.commit()
            last_id = cursor.lastrowid
            print(f"Medical record added successfully with ID: {last_id}") # Debug print
            return last_id
        except ValueError:
             # This error occurs if patient_id is not a valid integer
             print(f"Value Error: Patient ID '{patient_id}' could not be converted to integer.")
             messagebox.showerror("Internal Error", "Invalid Patient ID format for saving record.")
             if self.conn: self.conn.rollback() # Rollback if conversion failed before execute
             return None
        except Error as e:
            print(f"Database Error adding medical record: {e}") # Debug print
            messagebox.showerror("Database Error", f"Error adding medical record: {e}")
            if self.conn: self.conn.rollback() # Rollback changes on error
            return None
        finally:
            if cursor: cursor.close() # Ensure cursor is closed

    def get_medical_history(self, patient_id):
        """Retrieves all medical history records for a given patient ID."""
        if not self.conn:
            messagebox.showerror("Database Error", "No database connection.")
            return []
        sql = "SELECT visit_date, symptoms, diagnosis, treatment FROM medical_history WHERE patient_id = ? ORDER BY visit_date DESC"
        cursor = None
        try:
            patient_id_int = int(patient_id)
            cursor = self.conn.cursor()
            cursor.execute(sql, (patient_id_int,))
            # Return list of tuples: [(visit_date, symptoms, diagnosis, treatment), ...]
            return cursor.fetchall()
        except ValueError:
             messagebox.showerror("Input Error", "Patient ID must be a number to view history.")
             return []
        except Error as e:
            print(f"Database Error fetching medical history: {e}")
            messagebox.showerror("Database Error", f"Error fetching medical history: {e}")
            return []
        finally:
            if cursor: cursor.close()

    def close(self):
        """Closes the database connection."""
        if self.conn:
            print("Closing database connection.") # Debug print
            self.conn.close()
            self.conn = None # Ensure connection is marked as closed

# Example Usage (Optional - for testing the class directly)
if __name__ == '__main__':
    # This block will only run if database.py is executed directly
    print("Testing Database Class...")
    db = Database("test_hospital.db") # Use a test database file

    if db.conn: # Proceed only if connection was successful
        print("\nTesting add_patient...")
        new_id = db.add_patient(name="Test User", age="30", sex="Other", phone="1234567890")
        if new_id:
            print(f"Added patient with ID: {new_id}")

            print("\nTesting get_patient...")
            patient = db.get_patient(new_id)
            if patient:
                print(f"Retrieved patient: {patient}")
            else:
                print(f"Could not retrieve patient ID: {new_id}")

            print("\nTesting add_medical_record...")
            record_id = db.add_medical_record(
                patient_id=new_id,
                symptoms="Fever, Cough",
                diagnosis="Flu",
                treatment="Rest, Fluids"
            )
            if record_id:
                print(f"Added medical record with ID: {record_id}")

                print("\nTesting get_medical_history...")
                history = db.get_medical_history(new_id)
                if history:
                    print(f"Retrieved history for patient {new_id}:")
                    for record in history:
                        print(f" - {record}")
                else:
                    print(f"Could not retrieve history for patient ID: {new_id}")

            else:
                print("Could not add medical record.")

        else:
            print("Could not add patient.")

        # Clean up the test database (optional)
        # import os
        # db.close()
        # try:
        #     os.remove("test_hospital.db")
        #     print("\nRemoved test_hospital.db")
        # except OSError as e:
        #     print(f"Error removing test database: {e}")

    else:
        print("Database connection failed. Cannot run tests.")

