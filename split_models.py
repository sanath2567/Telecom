import joblib
import os

# Create folders
os.makedirs('models/forecast', exist_ok=True)

print("Loading giant model... (646MB)")
d = joblib.load('telecom_models_dictionary.pkl')
print(f"Loaded dictionary with {len(d)} keys.")

for key, value in d.items():
    filename = f"models/forecast/{key}.pkl"
    joblib.dump(value, filename)
    print(f"Saved: {filename}")

print("\nDone! Now you can delete the 646MB file and use individual files.")
