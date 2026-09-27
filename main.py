import os
import requests
from supabase import create_client, Client

# Configuration Supabase
SUPABASE_URL = "https://xglbbrcjsuuomnjkvhmx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhnbGJicmNqc3V1b21uamt2aG14Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1MzgwMTIsImV4cCI6MjEwNjExNDAxMn0.rxKnU1XYH0smwsnjXtYQpNsZzol-Tg5Ik8ZK-SaiPF4"

# URLs GBFS Vilvolt Epinal
URL_STATIONS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_information.json"
URL_STATUS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_status.json"

def collecter_donnees():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        # Récupération des infos des stations
        res_info = requests.get(URL_STATIONS, timeout=10)
        res_status = requests.get(URL_STATUS, timeout=10)

        if res_info.status_code != 200 or res_status.status_code != 200:
            print("Erreur de récupération des données GBFS")
            return

        stations_info = {s['station_id']: s['name'] for s in res_info.json()['data']['stations']}
        stations_status = res_status.json()['data']['stations']

        enregistrements = []
        for station in stations_status:
            s_id = station['station_id']
            nom = stations_info.get(s_id, f"Station {s_id}")
            velos = station.get('num_bikes_available', 0)

            enregistrements.append({
                "nom_station": nom,
                "velos_disponibles": velos
            })

        if enregistrements:
            data, count = supabase.table("releves_vilvolt").insert(enregistrements).execute()
            print(f"Succès : {len(enregistrements)} stations insérées dans Supabase.")

    except Exception as e:
        print(f"Erreur lors de la collecte : {e}")
        raise e

if __name__ == "__main__":
    collecter_donnees()
