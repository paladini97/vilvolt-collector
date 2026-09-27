import requests
import os
from supabase import create_client, Client

# Récupération sécurisée des accès
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("Les clés SUPABASE_URL ou SUPABASE_KEY sont manquantes.")

supabase: Client = create_client(URL, KEY)

# Flux officiel GBFS Vilvolt Épinal
GBFS_URL = "https://gbfs.partners.fifteen.eu/gbfs/epinal/station_status.json"

def collecter_donnees():
    response = requests.get(GBFS_URL)
    
    if response.status_code == 200:
        data = response.json()
        stations = data['data']['stations']
        
        lignes_a_inserer = []
        
        for station in stations:
            lignes_a_inserer.append({
                "station_id": str(station.get('station_id')),
                "velos_disponibles": station.get('num_bikes_available', 0),
                "places_libres": station.get('num_docks_available', 0)
            })
        
        if lignes_a_inserer:
            supabase.table("releves_vilvolt").insert(lignes_a_inserer).execute()
            print(f"Succès : {len(lignes_a_inserer)} stations enregistrées !")
    else:
        print(f"Erreur HTTP : {response.status_code}")

if __name__ == "__main__":
    collecter_donnees()
