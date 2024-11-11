import cv2
import pickle
import os
import time
import face_recognition
from adafruit_fingerprint import Adafruit_Fingerprint

# Initialize fingerprint sensor
fingerprint_sensor = Adafruit_Fingerprint('/dev/ttyAMA0')

# Directory to store user data locally
USER_DATA_DIR = "user_data"
if not os.path.exists(USER_DATA_DIR):
    os.makedirs(USER_DATA_DIR)

# Load existing users from a pickle file (if exists)
users_file = os.path.join(USER_DATA_DIR, "users.pkl")
if os.path.exists(users_file):
    with open(users_file, 'rb') as f:
        users = pickle.load(f)
else:
    users = {}

# Function to save user data
def save_user_data():
    with open(users_file, 'wb') as f:
        pickle.dump(users, f)

# Function to enroll fingerprint
def enroll_fingerprint(user_id):
    print("Starting fingerprint enrollment...")
    
    fingerprint_sensor.get_image()
    result = fingerprint_sensor.image_2_tz(1)
    if result != fingerprint_sensor.OK:
        print("Failed to capture fingerprint image!")
        return
    
    print("Fingerprint captured, please place again for confirmation...")
    fingerprint_sensor.get_image()
    result = fingerprint_sensor.image_2_tz(2)
    if result != fingerprint_sensor.OK:
        print("Failed to capture fingerprint image!")
        return
    
    result = fingerprint_sensor.create_model()
    if result != fingerprint_sensor.OK:
        print("Failed to create fingerprint model!")
        return
    
    print(f"Fingerprint enrolled successfully for ID: {user_id}")
    # Save the fingerprint template (store the fingerprint model)
    users[user_id]["fingerprint"] = fingerprint_sensor.finger_id
    save_user_data()

# Function to enroll face
def enroll_face(user_id):
    print("Starting face enrollment...")
    
    # Initialize camera and face detection
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    # Capture the user's face and save the encoding
    print(f"Please look at the camera for face enrollment (User ID: {user_id})")
    ret, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
    
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
        detected_face = frame[y:y+h, x:x+w]
        
        # Use face_recognition to get encoding
        face_encoding = face_recognition.face_encodings(detected_face)
        if face_encoding:
            users[user_id]["face_encoding"] = face_encoding[0]  # Save the face encoding
            print("Face enrolled successfully.")
    
    cap.release()
    cv2.destroyAllWindows()
    save_user_data()

# Main enrollment flow
def main():
    while True:
        user_id = input("Enter user ID for enrollment (or 'exit' to stop): ")
        if user_id.lower() == "exit":
            break
        name = input(f"Enter name for User ID {user_id}: ")
        
        # Initialize the user data
        users[user_id] = {"name": name}
        
        # Enroll fingerprint
        enroll_fingerprint(user_id)
        
        # Enroll face
        enroll_face(user_id)

if __name__ == "__main__":
    main()
