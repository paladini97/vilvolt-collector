import requests
import os
from supabase import create_client, Client

# Récupération sécurisée des accès
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_KEY")

if not URL or not KEY:
    raise ValueError("Les clés SUPABASE_URL ou SUPABASE_KEY sont manquantes.")

supabase: Client = create_client(URL, KEY)

# URLs des flux GBFS Vilvolt
STATUS_URL = "https://gbfs.partners.fifteen.eu/gbfs/epinal/station_status.json"
INFO_URL = "https://gbfs.partners.fifteen.eu/gbfs/epinal/station_information.json"

def collecter_donnees():
    # 1. Récupération des noms de stations
    res_info = requests.get(INFO_URL)
    noms_stations = {}
    if res_info.status_code == 200:
        for st in res_info.json()['data']['stations']:
            noms_stations[str(st.get('station_id'))] = st.get('name')

    # 2. Récupération de l'état en temps réel
    res_status = requests.get(STATUS_URL)
    if res_status.status_code == 200:
        stations = res_status.json()['data']['stations']
        lignes_a_inserer = []
        
        for station in stations:
            s_id = str(station.get('station_id'))
            lignes_a_inserer.append({
                "station_id": s_id,
                "nom_station": noms_stations.get(s_id, "Inconnue"),
                "velos_disponibles": station.get('num_bikes_available', 0),
                "places_libres": station.get('num_docks_available', 0)
            })
        
        if lignes_a_inserer:
            supabase.table("releves_vilvolt").insert(lignes_a_inserer).execute()
            print(f"Succès : {len(lignes_a_inserer)} stations enregistrées avec leurs noms !")
    else:
        print(f"Erreur HTTP : {res_status.status_code}")

if __name__ == "__main__":
    collecter_donnees()
