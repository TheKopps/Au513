import pandas as pd
import glob

# Charger et concaténer tous les fichiers CSV générés
all_files = glob.glob("flight_*.csv")  # Charge tous les fichiers avec ce pattern
flights_combined = pd.concat((pd.read_csv(f) for f in all_files), ignore_index=True)

# Sauvegarder dans un fichier unique
flights_combined.to_csv("detailed_flight_data.csv", index=False)

print("Les vols ont été combinés et sauvegardés dans 'detailed_flight_data.csv'.")
