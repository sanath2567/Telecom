import joblib
import pandas as pd
import os

path = 'd:/sp/p-2/codes/telecom_models_dictionary.pkl'
print(f"Inspecting dictionary at {path}...")
try:
    data = joblib.load(path)
    keys = list(data.keys())
    print(f"Num Keys: {len(keys)}")
    first_key = keys[0]
    print(f"Example Key: {first_key}")
    item = data[first_key]
    print(f"Item Keys: {list(item.keys()) if isinstance(item, dict) else 'Not a dict'}")
    
    if isinstance(item, dict) and 'model_results' in item:
        model = item['model_results']
        print(f"Model Type: {type(model)}")
        if hasattr(model, 'forecast'):
             print("Model has 'forecast' method")
        elif hasattr(model, 'predict'):
             print("Model has 'predict' method")
             
    if 'last_date' in item:
        print(f"Last Date in {first_key}: {item['last_date']}")

except Exception as e:
    print(f"Error: {e}")
