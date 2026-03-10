import os
from datetime import datetime
import firebase_admin
from firebase_admin import firestore

def get_db():
    """Get Firestore client if Firebase is initialized, else None."""
    if not firebase_admin._apps:
        return None
    return firestore.client()

def init_db():
    """No schema initialization needed for Firestore. We can optionally seed an admin user."""
    db = get_db()
    if not db: return
    
    admin_ref = db.collection('users').document('admin_uid')
    if not admin_ref.get().exists:
        admin_ref.set({
            'uid': 'admin_uid', 
            'email': 'admin@telcoiq.com', 
            'role': 'ADMIN', 
            'created_at': firestore.SERVER_TIMESTAMP
        })
        db.collection('user_usage').document('admin_uid').set({
            'uid': 'admin_uid', 
            'subscription_status': 'ENTERPRISE', 
            'churn_trials': 0, 
            'forecast_trials': 0
        })

def sync_user(uid, email):
    db = get_db()
    if not db: return

    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()
    
    if not user_doc.exists:
        # Default role assignment for new users
        role = 'ADMIN' if email == 'admin@gmail.com' else 'OPERATOR'

        user_ref.set({
            'uid': uid,
            'email': email,
            'role': role,
            'created_at': firestore.SERVER_TIMESTAMP
        })
    else:
        # If user exists, but logs in via a general flow, ensure we don't accidentally wipe their ADMIN status
        current_data = user_doc.to_dict()
        if current_data.get('role') != 'ADMIN' and email == 'admin@gmail.com':
            user_ref.update({'role': 'ADMIN'})
    usage_ref = db.collection('user_usage').document(uid)
    if not usage_ref.get().exists:
        usage_ref.set({
            'uid': uid,
            'churn_trials': 0,
            'forecast_trials': 0,
            'subscription_status': 'FREE'
        })

def update_session(uid, ip_address):
    db = get_db()
    if not db: return
    
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    session_ref = db.collection('active_sessions').document(uid)
    
    # We fetch user to attach email/role to session for easy admin viewing
    user_doc = db.collection('users').document(uid).get()
    email = user_doc.to_dict().get('email', 'Unknown') if user_doc.exists else 'Unknown'
    role = user_doc.to_dict().get('role', 'OPERATOR') if user_doc.exists else 'OPERATOR'

    doc = session_ref.get()
    if doc.exists:
        session_ref.update({
            'last_activity': now_str,
            'ip_address': ip_address,
            'status': 'ONLINE',
            'email': email,
            'role': role
        })
    else:
        session_ref.set({
            'uid': uid,
            'login_time': now_str,
            'last_activity': now_str,
            'status': 'ONLINE',
            'ip_address': ip_address,
            'email': email,
            'role': role
        })

def get_user_role(uid):
    db = get_db()
    if not db: return 'ADMIN' # Fail open for DEMO mode
    
    doc = db.collection('users').document(uid).get()
    if doc.exists:
        return doc.to_dict().get('role', 'OPERATOR')
    return 'OPERATOR'

def get_session_data():
    db = get_db()
    if not db: return []
    
    docs = db.collection('active_sessions').order_by('last_activity', direction=firestore.Query.DESCENDING).get()
    return [doc.to_dict() for doc in docs]

def get_all_users():
    db = get_db()
    if not db: return []
    
    docs = db.collection('users').order_by('created_at', direction=firestore.Query.DESCENDING).get()
    users = []
    for doc in docs:
        d = doc.to_dict()
        # Handle firestore timestamp for JSON serialization
        if 'created_at' in d and hasattr(d['created_at'], 'strftime'):
            d['created_at'] = d['created_at'].strftime('%Y-%m-%d %H:%M:%S')
        users.append(d)
    return users

def get_admin_stats():
    db = get_db()
    if not db: return {"total_users": 0, "active_sessions": 0}
    
    # Since Firebase Firestore doesn't have a simple COUNT() in the basic client without aggregation queries,
    # we just get the length of the collections. This is fine for small/medium datasets.
    users = db.collection('users').get()
    sessions = db.collection('active_sessions').where('status', '==', 'ONLINE').get()
    
    return {
        "total_users": len(users),
        "active_sessions": len(sessions)
    }

def get_usage(uid):
    db = get_db()
    if not db:
        # Demo mode bypass
        return {"churn_trials": 0, "forecast_trials": 0, "subscription_status": "ENTERPRISE"}
        
    doc = db.collection('user_usage').document(uid).get()
    if doc.exists:
        return doc.to_dict()
    return {"churn_trials": 0, "forecast_trials": 0, "subscription_status": "FREE"}

def increment_usage(uid, trial_type):
    db = get_db()
    if not db: return
    
    ref = db.collection('user_usage').document(uid)
    if trial_type == "churn":
        ref.update({"churn_trials": firestore.Increment(1)})
    elif trial_type == "forecast":
        ref.update({"forecast_trials": firestore.Increment(1)})
