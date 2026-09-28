import requests
from datetime import datetime, timezone
from supabase import create_client, Client

SUPABASE_URL = "https://xglbbrcjsuuomnjkvhmx.supabase.co"
SUPABASE_KEY = "TON_ANON_KEY"

URL_STATIONS = "URL_STATION_INFORMATION"
URL_STATUS = "URL_STATION_STATUS"

HEADERS = {
    "User-Agent": "InfoVivolt/1.0",
    "Accept": "application/json"
}


def collecter_donnees():

    try:
        supabase: Client = create_client(
            SUPABASE_URL,
            SUPABASE_KEY
        )

        # ============================
        # 1. Informations des stations
        # ============================

        res_info = requests.get(
            URL_STATIONS,
            headers=HEADERS,
            timeout=15
        )

        print(
            "INFO :",
            res_info.status_code,
            res_info.text[:300]
        )

        # ============================
        # 2. Statut des stations
        # ============================

        res_status = requests.get(
            URL_STATUS,
            headers=HEADERS,
            timeout=15
        )

        print(
            "STATUS :",
            res_status.status_code,
            res_status.text[:300]
        )

        # ============================
        # Vérification API
        # ============================

        if res_info.status_code != 200:
            print(
                f"⚠️ station_information refusé : "
                f"{res_info.status_code}"
            )
            return

        if res_status.status_code != 200:
            print(
                f"⚠️ station_status refusé : "
                f"{res_status.status_code}"
            )
            return

        # ============================
        # Lecture JSON
        # ============================

        info_json = res_info.json()
        status_json = res_status.json()

        stations_info = {
            s["station_id"]: s["name"]
            for s in info_json["data"]["stations"]
        }

        stations_status = status_json["data"]["stations"]

        maintenant = datetime.now(
            timezone.utc
        ).isoformat()

        # ============================
        # Préparation Supabase
        # ============================

        enregistrements = []

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

        # ============================
        # Insertion Supabase
        # ============================

        if enregistrements:

            result = (
                supabase
                .table("releves_vilvolt")
                .insert(enregistrements)
                .execute()
            )

            print(
                f"✅ {len(enregistrements)} stations "
                f"insérées à {maintenant}"
            )

    except requests.exceptions.Timeout:
        print("⚠️ Timeout : Vilvolt n'a pas répondu assez rapidement.")

    except requests.exceptions.RequestException as e:
        print(f"⚠️ Erreur HTTP : {e}")

    except Exception as e:
        print(f"❌ Erreur : {e}")


if __name__ == "__main__":
    collecter_donnees()
