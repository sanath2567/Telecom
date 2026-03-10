import firebase_admin
from firebase_admin import credentials, auth, firestore
import os

# 1. Initialize Firebase
SA_KEY = "serviceAccountKey.json"
if os.path.exists(SA_KEY):
    cred = credentials.Certificate(SA_KEY)
    try:
        firebase_admin.initialize_app(cred)
    except ValueError:
        pass # Already initialized
else:
    print("Error: serviceAccountKey.json not found.")
    exit(1)

# 2. Setup Firebase User
email = "admin@gmail.com"
password = "admin123"

try:
    user = auth.get_user_by_email(email)
    print(f"User {email} already exists in Firebase Auth.")
except auth.UserNotFoundError:
    user = auth.create_user(
        email=email,
        password=password,
        display_name="Admin"
    )
    print(f"Created new user {email} in Firebase Auth.")

# 3. Update Firestore Database
db = firestore.client()

user_ref = db.collection('users').document(user.uid)
user_ref.set({
    'uid': user.uid,
    'email': email,
    'role': 'ADMIN',
    'created_at': firestore.SERVER_TIMESTAMP
}, merge=True)

usage_ref = db.collection('user_usage').document(user.uid)
usage_ref.set({
    'uid': user.uid,
    'churn_trials': 0,
    'forecast_trials': 0,
    'subscription_status': 'ENTERPRISE'
}, merge=True)

print(f"Firestore database updated. {email} is now an ADMIN with ENTERPRISE access.")
