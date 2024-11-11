import cv2
import pickle
import time
import face_recognition
from gpiozero import Button
from rpi_lcd import LCD
from adafruit_fingerprint import Adafruit_Fingerprint
from gspread import service_account
from oauth2client.service_account import ServiceAccountCredentials

# Initialize LCD and button for manual intervention
lcd = LCD()
attendance_button = Button(17)

# Load user data (face encodings, fingerprints, etc.)
USER_DATA_DIR = "user_data"
users_file = os.path.join(USER_DATA_DIR, "users.pkl")
with open(users_file, 'rb') as f:
    users = pickle.load(f)

# Initialize fingerprint sensor
fingerprint_sensor = Adafruit_Fingerprint('/dev/ttyAMA0')

# Google Sheets setup
def authenticate_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open("Attendance").sheet1

# Function to recognize face and fingerprint
def recognize_user():
    # Initialize camera for face recognition
    cap = cv2.VideoCapture(0)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    while True:
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
        
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            detected_face = frame[y:y+h, x:x+w]
            
            # Use face_recognition to get encoding
            face_encoding = face_recognition.face_encodings(detected_face)
            if face_encoding:
                recognized = False
                for user_id, user_data in users.items():
                    # Compare face encodings
                    match = face_recognition.compare_faces([user_data["face_encoding"]], face_encoding[0])
                    if match[0]:
                        recognized = True
                        print(f"User {user_data['name']} recognized.")
                        # Log attendance to Google Sheets
                        sheet = authenticate_google_sheets()
                        sheet.append_row([user_data["name"], time.strftime("%Y-%m-%d %H:%M:%S")])
                        lcd.text(f"Welcome {user_data['name']}", 1)
                        time.sleep(2)
                        return
                if not recognized:
                    print("Face not recognized.")
                    lcd.text("Face not recognized", 1)
                    time.sleep(2)
        
        cv2.imshow("Face Recognition", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Function to check fingerprint
def check_fingerprint():
    fingerprint_sensor.get_image()
    result = fingerprint_sensor.image_2_tz(1)
    if result != fingerprint_sensor.OK:
        print("Failed to capture fingerprint image!")
        return

    result = fingerprint_sensor.finger_search()
    if result == fingerprint_sensor.OK:
        user_id = fingerprint_sensor.finger_id
        print(f"Fingerprint recognized for user {user_id}")
        user_data = users.get(str(user_id))
        if user_data:
            # Log attendance to Google Sheets
            sheet = authenticate_google_sheets()
            sheet.append_row([user_data["name"], time.strftime("%Y-%m-%d %H:%M:%S")])
            lcd.text(f"Welcome {user_data['name']}", 1)
            time.sleep(2)
        else:
            print("User not found!")
            lcd.text("User not found!", 1)
            time.sleep(2)
    else:
        print("Fingerprint not recognized.")
        lcd.text("Fingerprint not recognized", 1)
        time.sleep(2)

# Main attendance flow
def main():
    # Wait for class title input
    lcd.text("Enter Class Title", 1)
    class_title = input("Enter the class title: ")
    lcd.clear()
    lcd.text(f"Class: {class_title}", 1)
    
    # Wait for button press to start attendance
    lcd.text("Press button to start", 2)
    attendance_button.wait_for_press()
    lcd.clear()
    
    # Start attendance process
    while True:
        lcd.text("Scan Face or Finger", 1)
        lcd.text("Press button to quit", 2)
        
        # Wait for button press to quit
        if attendance_button.is_pressed:
            print("Exiting attendance system...")
            break
        
        # Recognize face or fingerprint
        recognize_user()
        # Optionally, check fingerprint here
        # check_fingerprint()

if __name__ == "__main__":
    main()
