import joblib
import pandas as pd
import numpy as np

path = 'd:/sp/p-2/codes/telecom_models_dictionary.pkl'
print(f"\n--- Inspecting: {path} ---")
try:
    # Use mmap_mode to avoid loading the whole 646MB into memory if possible, 
    # but joblib.load usually needs enough RAM.
    data = joblib.load(path)
    print(f"Type: {type(data)}")
    if isinstance(data, dict):
        print(f"Keys: {list(data.keys())}")
        for k, v in data.items():
            print(f"Key: {k}, Type: {type(v)}")
            if hasattr(v, 'feature_names_in_'):
                print(f"  Features: {v.feature_names_in_.tolist()}")
    else:
        print(f"Data: {str(data)[:500]}")
except Exception as e:
    print(f"Error loading {path}: {e}")
