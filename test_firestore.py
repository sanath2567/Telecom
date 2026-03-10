import db_utils
import firebase_admin
from firebase_admin import credentials

# Mock initialization for testing
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

print("Firebase initialized.")
try:
    db_utils.init_db()
    print("init_db success.")
    db_utils.sync_user('test_uid', 'test@example.com')
    print("sync_user success.")
    usage = db_utils.get_usage('test_uid')
    print("get_usage:", usage)
except Exception as e:
    print("Error:", e)
