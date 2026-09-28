import requests
from datetime import datetime, timezone
from supabase import create_client, Client

# ==========================================
# CONFIGURATION
# ==========================================

SUPABASE_URL = "https://xglbbrcjsuuomnjkvhmx.supabase.co"
SUPABASE_KEY = "TA_CLE_SUPABASE"

URL_STATIONS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_information.json"
URL_STATUS = "https://gbfs.partners.fifteen.eu/gbfs/epinal/fr/station_status.json"

HEADERS = {
    "User-Agent": "InfoVivolt/1.0",
    "Accept": "application/json"
}


# ==========================================
# COLLECTE DES DONNÉES
# ==========================================

def collecter_donnees():

    try:
        supabase: Client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        # Récupération des noms des stations
        res_info = requests.get(
            URL_STATIONS,
            headers=HEADERS,
            timeout=15
        )

        print("INFO :", res_info.status_code)

        # Récupération des disponibilités
        res_status = requests.get(
            URL_STATUS,
            headers=HEADERS,
            timeout=15
        )

        print("STATUS :", res_status.status_code)

        # Vérification
        if res_info.status_code != 200:
            print(
                f"❌ station_information refusé : "
                f"{res_info.status_code}"
            )
            return

        if res_status.status_code != 200:
            print(
                f"❌ station_status refusé : "
                f"{res_status.status_code}"
            )
            return

        # Lecture des données
        info_json = res_info.json()
        status_json = res_status.json()

        stations_info = {
            station["station_id"]: station["name"]
            for station in info_json["data"]["stations"]
        }

        stations_status = status_json["data"]["stations"]

        maintenant = datetime.now(
            timezone.utc
        ).isoformat()

        enregistrements = []

        # Préparation des données pour Supabase
        for station in stations_status:

            station_id = station["station_id"]

            nom = stations_info.get(
                station_id,
                f"Station {station_id}"
            )

            velos = station.get(
                "num_bikes_available",
                0
            )

            docks = station.get(
                "num_docks_available",
                0
            )

            enregistrements.append({
                "station_id": station_id,
                "nom_station": nom,
                "velos_disponibles": velos,
                "places_libres": docks,
                "date_releve": maintenant
            })

        # Envoi vers Supabase
        if enregistrements:

            supabase \
                .table("releves_vilvolt") \
                .insert(enregistrements) \
                .execute()

            print(
                f"✅ {len(enregistrements)} stations "
                f"envoyées à Supabase"
            )

    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur HTTP : {e}")

    except Exception as e:
        print(f"❌ Erreur : {e}")


# ==========================================
# LANCEMENT
# ==========================================

if __name__ == "__main__":
    collecter_donnees()
