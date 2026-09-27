import requests
import os
from supabase import create_client, Client

# Récupération des accès Supabase
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("Les clés SUPABASE_URL ou SUPABASE_KEY sont manquantes.")

supabase: Client = create_client(URL, KEY)

STATUS_URL = "https://gbfs.partners.fifteen.eu/gbfs/epinal/station_status.json"
INFO_URL = "https://gbfs.partners.fifteen.eu/gbfs/epinal/station_information.json"

def collecter_donnees():
    # 1. Récupération de la correspondance station_id -> nom
    res_info = requests.get(INFO_URL)
    noms_stations = {}
    if res_info.status_code == 200:
        data_info = res_info.json().get('data', {}).get('stations', [])
        for st in data_info:
            s_id = str(st.get('station_id', '')).strip()
            name = st.get('name')
            if s_id and name:
                noms_stations[s_id] = name

    # 2. Récupération de l'état en temps réel
    res_status = requests.get(STATUS_URL)
    if res_status.status_code == 200:
        stations = res_status.json().get('data', {}).get('stations', [])
        lignes_a_inserer = []
        
        for station in stations:
            s_id = str(station.get('station_id', '')).strip()
            nom = noms_stations.get(s_id, "Station inconnue")
            
            lignes_a_inserer.append({
                "station_id": s_id,
                "nom_station": nom,
                "velos_disponibles": station.get('num_bikes_available', 0),
                "places_libres": station.get('num_docks_available', 0)
            })
        
        if lignes_a_inserer:
            supabase.table("releves_vilvolt").insert(lignes_a_inserer).execute()
            print(f"Succès : {len(lignes_a_inserer)} stations insérées !")
    else:
        print(f"Erreur lors de la récupération des statuts: {res_status.status_code}")

if __name__ == "__main__":
    collecter_donnees()
