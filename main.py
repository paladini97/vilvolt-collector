import requests
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = "https://xglbbrcjsuuomnjkvhmx.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhnbGJicmNqc3V1b21uamt2aG14Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1MzgwMTIsImV4cCI6MjEwNjExNDAxMn0.rxKnU1XYH0smwsnjXtYQpNsZzol-Tg5Ik8ZK-SaiPF4"

URL_STATIONS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_information.json"
URL_STATUS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_status.json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def collecter_donnees():
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

        res_info = requests.get(URL_STATIONS, headers=HEADERS, timeout=10)
        res_status = requests.get(URL_STATUS, headers=HEADERS, timeout=10)

        if res_info.status_code != 200 or res_status.status_code != 200:
            print(f"Erreur API GBFS: Info={res_info.status_code}, Status={res_status.status_code}")
            raise Exception("L'API GBFS n'a pas répondu avec un code 200.")

        stations_info = {s['station_id']: s['name'] for s in res_info.json()['data']['stations']}
        stations_status = res_status.json()['data']['stations']

        maintenant = datetime.now(timezone.utc).isoformat()

        enregistrements = []
        for station in stations_status:
            s_id = station['station_id']
            nom = stations_info.get(s_id, f"Station {s_id}")
            velos = station.get('num_bikes_available', 0)
            docks = station.get('num_docks_available', 0)

            enregistrements.append({
                "station_id": s_id,
                "nom_station": nom,
                "velos_disponibles": velos,
                "places_libres": docks,
                "date_releve": maintenant
            })

        if enregistrements:
            supabase.table("releves_vilvolt").insert(enregistrements).execute()
            print(f"Succès ! {len(enregistrements)} stations insérées à {maintenant}")

    # Exemple de modification dans ton bloc de vérification :
if response_stations.status_code != 200 or response_status.status_code != 200:
    print(f"⚠️ Le serveur Vilvolt est en maintenance ou injoignable (Status: {response_status.status_code}). Le script s'arrête en douceur.")
    exit(0)  # Arrête le script proprement sans faire échouer GitHub Actions en rouge

if __name__ == "__main__":
    collecter_donnees()
