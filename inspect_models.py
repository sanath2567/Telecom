import joblib
import pandas as pd
import numpy as np

model_paths = [
    'd:/sp/p-2/codes/rf_airtel_churn.pkl',
    'd:/sp/p-2/codes/rf_bsnl_churn.pkl',
    'd:/sp/p-2/codes/rf_jio_churn.pkl',
    'd:/sp/p-2/codes/rf_vi_churn.pkl'
]

for path in model_paths:
    print(f"\n--- Model: {path} ---")
    try:
        model = joblib.load(path)
        print(f"Type: {type(model)}")
        if hasattr(model, 'feature_names_in_'):
            print(f"Features: {model.feature_names_in_.tolist()}")
        elif hasattr(model, 'n_features_in_'):
            print(f"Num Features: {model.n_features_in_}")
        
        # Try to see classes
        if hasattr(model, 'classes_'):
            print(f"Classes: {model.classes_}")
            
    except Exception as e:
        print(f"Error loading {path}: {e}")
