import joblib
import os

path = 'd:/sp/p-2/codes/telecom_models_dictionary.pkl'
if os.path.exists(path):
    try:
        data = joblib.load(path)
        first_key = list(data.keys())[0]
        print(f"KEY: {first_key}")
        item = data[first_key]
        print(f"ITEM TYPE: {type(item)}")
        if isinstance(item, dict):
            print(f"ITEM KEYS: {list(item.keys())}")
            # If it has a model, check features
            for k, v in item.items():
                if hasattr(v, 'feature_names_in_'):
                    print(f"FEATURES FOR {k}: {v.feature_names_in_.tolist()}")
                elif 'model' in k.lower() and hasattr(v, 'predict'):
                    print(f"MODEL FOUND: {k}")
                    if hasattr(v, 'feature_names_in_'):
                        print(f"FEATURES: {v.feature_names_in_.tolist()}")
        
    except Exception as e:
        print(f"ERROR: {e}")
else:
    print("FILE NOT FOUND")
