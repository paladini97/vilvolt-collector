<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Statistiques & Réservation Minute par Minute — Vilvolt</title>
  
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>

  <style>
    body { font-family: 'Segoe UI', system-ui, sans-serif; margin: 0; padding: 20px; background: #f4f6f8; color: #333; }
    .container { max-width: 950px; margin: 20px auto; background: white; padding: 30px; border-radius: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.06); }
    h1 { color: #0d6efd; margin-top: 0; margin-bottom: 8px; font-size: 1.8rem; }
    p.subtitle { color: #6c757d; margin-bottom: 20px; font-size: 0.95rem; }
    #map { height: 320px; width: 100%; border-radius: 10px; margin-bottom: 25px; border: 1px solid #dee2e6; }
    
    .controls { display: flex; gap: 15px; margin-bottom: 20px; flex-wrap: wrap; }
    .control-group { flex: 1; min-width: 160px; }
    label { display: block; font-weight: 600; margin-bottom: 6px; color: #495057; font-size: 0.88rem; }
    select { width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #ced4da; font-size: 0.95rem; background-color: #fff; }
    
    .reservation-box {
      background: #e7f1ff;
      border-left: 5px solid #0d6efd;
      padding: 16px 20px;
      border-radius: 8px;
      margin-bottom: 25px;
      transition: all 0.3s ease;
    }
    .reservation-box.critical { background: #f8d7da; border-left-color: #dc3545; }
    .reservation-box.warning { background: #fff3cd; border-left-color: #ffc107; }
    .reservation-box h3 { margin: 0 0 6px 0; font-size: 1.1rem; color: #084298; }
    .reservation-box.critical h3 { color: #842029; }
    .reservation-box.warning h3 { color: #664d03; }
    .reservation-box p { margin: 0; font-size: 0.95rem; color: #212529; line-height: 1.5; }
    .highlight { font-weight: bold; color: #0d6efd; }
    .alert-warn { color: #b02a37; font-weight: bold; }
    
    .chart-box { position: relative; margin-top: 15px; }
  </style>
</head>
<body>

<div class="container">
  <h1>🚲 Vilvolt Épinal — Prédiction & Réservation Minute par Minute</h1>
  <p class="subtitle">Analyse en temps réel des pics de prise de vélos et ajustement algorithmique de votre stratégie de réservation.</p>

  <div id="map"></div>

  <div class="controls">
    <div class="control-group" style="flex: 2; min-width: 200px;">
      <label for="stationSelect">Station :</label>
      <select id="stationSelect" onchange="changerStationDepuisSelect()"></select>
    </div>

    <div class="control-group">
      <label for="jourSelect">Jour :</label>
      <select id="jourSelect" onchange="chargerGraphique()">
        <option value="1">Lundi</option>
        <option value="2">Mardi</option>
        <option value="3">Mercredi</option>
        <option value="4">Jeudi</option>
        <option value="5">Vendredi</option>
        <option value="6">Samedi</option>
        <option value="0">Dimanche</option>
      </select>
    </div>

    <div class="control-group">
      <label for="heureSelect">Heure :</label>
      <select id="heureSelect" onchange="calculerConseilMinute()"></select>
    </div>

    <div class="control-group">
      <label for="minuteSelect">Minute (0-59) :</label>
      <select id="minuteSelect" onchange="calculerConseilMinute()"></select>
    </div>

    <div class="control-group">
      <label for="delaiSelect">Anticipation minimale :</label>
      <select id="delaiSelect" onchange="calculerConseilMinute()">
        <option value="1">1 min avant</option>
        <option value="2">2 min avant</option>
        <option value="3" selected>3 min avant (ex: fin de cours)</option>
        <option value="4">4 min avant</option>
        <option value="5">5 min avant (max appli)</option>
      </select>
    </div>
  </div>

  <div id="boxConseil" class="reservation-box">
    <h3>⏱️ Analyse & Stratégie de Réservation Dynamique</h3>
    <p id="conseilTexte">Sélectionnez une station et un horaire pour afficher la stratégie.</p>
  </div>

  <div class="chart-box">
    <canvas id="monGraphique"></canvas>
  </div>
</div>

<script>
  const SUPABASE_URL = "https://xglbbrcjsuuomnjkvhmx.supabase.co";
  const SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhnbGJicmNqc3V1b21uamt2aG14Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTA1MzgwMTIsImV4cCI6MjEwNjExNDAxMn0.rxKnU1XYH0smwsnjXtYQpNsZzol-Tg5Ik8ZK-SaiPF4"; // REMPLACE PAR TA CLÉ ANON

  const supabaseClient = supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  let chart;
  let map;
  let marqueurs = {};
  let donneesGlobales = [];

  const COORDONNEES_STATIONS = {
    "Gare": [48.1732, 6.4423],
    "Place des Vosges": [48.1746, 6.4505],
    "Port": [48.1780, 6.4450],
    "BMI": [48.1725, 6.4488],
    "4 nations": [48.1740, 6.4470],
    "Arches-Gare": [48.1189, 6.5270],
    "Archettes": [48.1250, 6.5350],
    "Avrinsart": [48.1500, 6.4600],
    "Blancs Champs": [48.1800, 6.4600]
  };

  function remplirHeuresEtMinutes() {
    const selectH = document.getElementById('heureSelect');
    const selectM = document.getElementById('minuteSelect');

    for (let h = 0; h < 24; h++) {
      const opt = document.createElement('option');
      opt.value = h;
      opt.textContent = `${String(h).padStart(2, '0')} h`;
      selectH.appendChild(opt);
    }

    for (let m = 0; m < 60; m++) {
      const opt = document.createElement('option');
      opt.value = m;
      opt.textContent = `${String(m).padStart(2, '0')} min`;
      selectM.appendChild(opt);
    }

    const maintenant = new Date();
    selectH.value = maintenant.getHours();
    selectM.value = maintenant.getMinutes();
  }

  function initialiserCarte() {
    map = L.map('map').setView([48.1742, 6.4496], 13);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '© OpenStreetMap'
    }).addTo(map);
  }

  async function initialiser() {
    initialiserCarte();
    remplirHeuresEtMinutes();

    const jourActuel = new Date().getDay();
    document.getElementById('jourSelect').value = jourActuel;

    const { data: stations, error } = await supabaseClient
      .from('moyennes_5min')
      .select('nom_station');

    if (error) {
      console.error("Erreur Supabase :", error);
      return;
    }

    const stationsUniques = [...new Set(stations.map(s => s.nom_station))].sort();
    const selectStation = document.getElementById('stationSelect');

    stationsUniques.forEach((nom) => {
      const option = document.createElement('option');
      option.value = nom;
      option.textContent = nom;
      selectStation.appendChild(option);

      const coords = COORDONNEES_STATIONS[nom] || [48.1742, 6.4496];
      const marker = L.marker(coords).addTo(map);
      marker.bindPopup(`<b>${nom}</b>`);

      marker.on('click', () => {
        selectStation.value = nom;
        chargerGraphique();
      });

      marqueurs[nom] = marker;
    });

    if (stationsUniques.length > 0) {
      changerStationDepuisSelect();
    }
  }

  function changerStationDepuisSelect() {
    const stationNom = document.getElementById('stationSelect').value;
    const marker = marqueurs[stationNom];

    if (marker) {
      map.panTo(marker.getLatLng());
      marker.openPopup();
    }

    chargerGraphique();
  }

  async function chargerGraphique() {
    const station = document.getElementById('stationSelect').value;
    const jour = parseInt(document.getElementById('jourSelect').value);

    if (!station) return;

    const { data, error } = await supabaseClient
      .from('moyennes_5min')
      .select('heure, minute, moyenne_velos')
      .eq('nom_station', station)
      .eq('jour_semaine', jour)
      .order('heure', { ascending: true })
      .order('minute', { ascending: true });

    if (error) {
      console.error("Erreur graphique :", error);
      return;
    }

    donneesGlobales = data;

    const labels = data.map(d => `${String(d.heure).padStart(2, '0')}:${String(d.minute).padStart(2, '0')}`);
    const valeurs = data.map(d => d.moyenne_velos);

    if (chart) chart.destroy();

    const ctx = document.getElementById('monGraphique').getContext('2d');
    chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: `Vélos disponibles à ${station}`,
          data: valeurs,
          borderColor: '#0d6efd',
          backgroundColor: 'rgba(13, 110, 253, 0.08)',
          fill: true,
          tension: 0.25,
          pointRadius: 3
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true, ticks: { stepSize: 1 }, title: { display: true, text: 'Vélos disponibles' } },
          x: { title: { display: true, text: 'Créneaux de 5 min' } }
        }
      }
    });

    calculerConseilMinute();
  }

  // Interpolation linéaire fine minute par minute
  function estimerVelosAMinute(h, m) {
    if (!donneesGlobales || donneesGlobales.length === 0) return 0;

    const mBase = Math.floor(m / 5) * 5;
    const mSuiv = (mBase + 5) % 60;
    const hSuiv = mBase === 55 ? (h + 1) % 24 : h;

    const d1 = donneesGlobales.find(d => d.heure === h && d.minute === mBase);
    const d2 = donneesGlobales.find(d => d.heure === hSuiv && d.minute === mSuiv);

    const v1 = d1 ? d1.moyenne_velos : 0;
    const v2 = d2 ? d2.moyenne_velos : v1;

    const fraction = (m - mBase) / 5;
    return v1 + (v2 - v1) * fraction;
  }

  // ALGORITHME DYNAMIQUE : Analyse de la vitesse de disparition des vélos (Dérivée locale)
  function calculerConseilMinute() {
    const hVise = parseInt(document.getElementById('heureSelect').value);
    const mVise = parseInt(document.getElementById('minuteSelect').value);
    const delaiMin = parseInt(document.getElementById('delaiSelect').value);
    const station = document.getElementById('stationSelect').value;
    const boxEl = document.getElementById('boxConseil');

    if (!donneesGlobales || donneesGlobales.length === 0) return;

    // 1. Estimation de la quantité au moment désiré
    const velosVises = estimerVelosAMinute(hVise, mVise);

    // 2. Calcul du taux de variation sur la fenêtre [m-10, m+5] (Vélos consommés par minute)
    let mPrecedente = mVise - 10;
    let hPrecedente = hVise;
    if (mPrecedente < 0) {
      mPrecedente += 60;
      hPrecedente = (hVise - 1 + 24) % 24;
    }
    const velosAvant = estimerVelosAMinute(hPrecedente, mPrecedente);
    const debitConsommation = (velosAvant - velosVises) / 10; // Positif si pic de prise (vélos qui diminuent)

    // 3. Ajustement dynamique de la minute d'anticipation recommandée
    let delaiRecommande = delaiMin;

    if (debitConsommation > 0.3) {
      // Pic très sévère : forcer l'anticipation maximale possible (max 5 min sur l'appli Vilvolt)
      delaiRecommande = Math.min(5, delaiMin + 2);
    } else if (debitConsommation > 0.15) {
      // Pic modéré : ajouter 1 min de marge
      delaiRecommande = Math.min(5, delaiMin + 1);
    }

    // 4. Calcul de l'heure précise de déclenchement recommandée
    let mResa = mVise - delaiRecommande;
    let hResa = hVise;
    if (mResa < 0) {
      mResa += 60;
      hResa = (hVise - 1 + 24) % 24;
    }
    const velosResa = estimerVelosAMinute(hResa, mResa);

    const txtVise = `${String(hVise).padStart(2, '0')}:${String(mVise).padStart(2, '0')}`;
    const txtResa = `${String(hResa).padStart(2, '0')}:${String(mResa).padStart(2, '0')}`;

    // Reset styles
    boxEl.className = "reservation-box";

    let conseilHTML = `🎯 <b>À ${txtVise} :</b> ~<b>${velosVises.toFixed(1)} vélo(s)</b> théoriquement disponibles à ${station}.<br>`;

    // Case 1: Station vide / Risque élevé
    if (velosVises <= 0.6) {
      boxEl.classList.add("critical");
      conseilHTML += `🚨 <span class="alert-warn">CRITIQUE — STATION PRESQUE VIDE !</span><br>`;
      conseilHTML += `Le flux de demande indique une pénurie totale autour de ${txtVise}. <br>`;
      conseilHTML += `👉 <b>Action :</b> Ouvrez l'application dès <span class="highlight">${txtResa}</span> (${delaiRecommande} min avant) et réservez à la seconde exacte où un vélo est restitué.`;
    } 
    // Case 2: Gros pic de prises (Débit fort)
    else if (debitConsommation > 0.2) {
      boxEl.classList.add("warning");
      const perteTotale = (debitConsommation * 5).toFixed(1);
      conseilHTML += `⚠️ <b>RUSH DÉTECTÉ (Pic d'utilisation) :</b> La station perd ~<b>${perteTotale} vélos toutes les 5 min</b> sur ce créneau.<br>`;
      if (delaiRecommande > delaiMin) {
        conseilHTML += `⚡ <b>Ajustement automatique :</b> L'algorithme a augmenté votre anticipation de <b>${delaiMin} à ${delaiRecommande} min</b> pour devancer la vague d'utilisateurs.<br>`;
      }
      conseilHTML += `👉 <b>Action :</b> Lancez la réservation précisément à <span class="highlight">${txtResa}</span> (~<b>${velosResa.toFixed(1)} vélos</b> encore dispos) pour sécuriser le vôtre avant la rupture.`;
    } 
    // Case 3: Situation calme / Stable
    else {
      conseilHTML += `✅ <b>FLUX STABLE :</b> Pas de pic brutal détecté à cet horaire (variation de ~${Math.abs(debitConsommation).toFixed(2)} vélo/min).<br>`;
      conseilHTML += `👉 <b>Action :</b> Vous pouvez réserver sereinement à <span class="highlight">${txtResa}</span> (${delaiRecommande} min avant). Votre vélo restera bloqué jusqu'à votre arrivée.`;
    }

    document.getElementById('conseilTexte').innerHTML = conseilHTML;
  }

  initialiser();
</script>

</body>
</html>
