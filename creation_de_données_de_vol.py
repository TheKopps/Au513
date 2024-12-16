import numpy as np
import pandas as pd
import os

# Créer un dossier pour sauvegarder les fichiers
output_folder = "flights"
os.makedirs(output_folder, exist_ok=True)

def simulate_detailed_flight(flight_id, duration_s, scenario=None):
    """
    Simule un vol réaliste avec ou sans crash, en ajoutant plus de paramètres issus des boîtes noires.
    """
    time_steps = np.arange(0, duration_s, 0.001)  # Données toutes les millisecondes
    num_points = len(time_steps)

    # Initialisation des paramètres
    altitude = np.zeros(num_points)
    speed = np.zeros(num_points)
    vertical_speed = np.zeros(num_points)
    aoa = np.zeros(num_points)  # Angle d'attaque
    pitch = np.zeros(num_points)  # Assiette
    roll = np.zeros(num_points)  # Roulis
    yaw = np.zeros(num_points)  # Lacet
    engine_rpm = np.ones(num_points) * 90  # Régime moteur (%)
    egt = np.ones(num_points) * 400  # Température des gaz d'échappement (°C)
    flaps = np.zeros(num_points)  # Position des volets (%)
    gear = np.zeros(num_points)  # Position du train d'atterrissage (0 ou 1)
    autopilot = np.ones(num_points)  # Engagement du pilote automatique (0 ou 1)
    hydraulic_pressure = np.ones(num_points) * 3000  # Pression hydraulique (psi)
    stall_warning = np.zeros(num_points)  # Alarme de décrochage (0 ou 1)
    icing_warning = np.zeros(num_points)  # Alarme de givrage (0 ou 1)
    alarms = np.zeros(num_points)  # Alarmes générales (0 ou 1)

    # Répartition des phases
    takeoff_duration = duration_s / 3
    cruise_duration = duration_s / 3
    landing_duration = duration_s / 3

    # Simulation des phases normales de vol
    for i in range(1, num_points):
        t = time_steps[i]
        dt = 0.001  # Intervalle de temps (1 ms)

        # Phase de décollage
        if t <= takeoff_duration:
            speed[i] = min(231.4, speed[i - 1] + (231.4 / takeoff_duration) * dt)
            vertical_speed[i] = min(12.7, vertical_speed[i - 1] + (12.7 / (takeoff_duration / 2)) * dt)
            altitude[i] = altitude[i - 1] + vertical_speed[i] * dt
            aoa[i] = min(15, aoa[i - 1] + (15 / (takeoff_duration / 2)) * dt)
            flaps[i] = 10 if t < takeoff_duration / 2 else 0
            gear[i] = 1 if t < takeoff_duration / 2 else 0
            autopilot[i] = 0

        # Phase de croisière
        elif t <= takeoff_duration + cruise_duration:
            speed[i] = 231.4
            vertical_speed[i] = 0
            altitude[i] = altitude[i - 1]
            aoa[i] = 2
            autopilot[i] = 1

        # Phase d'atterrissage
        else:
            speed[i] = max(70.6, speed[i - 1] - ((231.4 - 70.6) / landing_duration) * dt)
            vertical_speed[i] = max(-15.24, vertical_speed[i - 1] - (15.24 / (landing_duration / 2)) * dt)
            altitude[i] = max(0, altitude[i - 1] + vertical_speed[i] * dt)
            aoa[i] = max(0, aoa[i - 1] - (10 / (landing_duration / 2)) * dt)
            flaps[i] = 20 if t > takeoff_duration + cruise_duration + landing_duration / 2 else 0
            gear[i] = 1

        # Commandes
        pitch[i] = aoa[i] * 0.5
        roll[i] = np.sin(t / 10) * 5
        yaw[i] = np.cos(t / 10) * 5

    # Intégration des scénarios de crash
    if scenario:
        crash_start = int(num_points * 0.7)
        for i in range(crash_start, num_points):
            if scenario == "pitot_failure":
                speed[i] = 0 if i % 2 == 0 else speed[i - 1] * np.random.uniform(0.9, 1.1)
                alarms[i] = 1
            elif scenario == "stall":
                aoa[i] = 25
                vertical_speed[i] = min(-30, vertical_speed[i - 1] - 1)
                stall_warning[i] = 1
                pitch[i] = 20
            elif scenario == "hydraulic_failure":
                hydraulic_pressure[i] = 0
                pitch[i] = np.random.uniform(-10, 10)
                roll[i] = np.random.uniform(-15, 15)
                yaw[i] = np.random.uniform(-5, 5)
                alarms[i] = 1
            elif scenario == "icing":
                icing_warning[i] = 1
                engine_rpm[i] *= 0.8
                speed[i] = max(50, speed[i - 1] - 10 * dt)
            elif scenario == "engine_failure":
                engine_rpm[i] = 0
                speed[i] = max(0, speed[i - 1] - 5)
                altitude[i] = max(0, altitude[i - 1] + vertical_speed[i] * dt)
                alarms[i] = 1

    # Assembler les données
    flight_data = pd.DataFrame({
        "flight_id": flight_id,
        "time_step (s)": time_steps,
        "altitude (m)": altitude,
        "speed (m/s)": speed,
        "vertical_speed (m/s)": vertical_speed,
        "aoa (°)": aoa,
        "pitch (°)": pitch,
        "roll (°)": roll,
        "yaw (°)": yaw,
        "engine_rpm (%)": engine_rpm,
        "egt (°C)": egt,
        "flaps (%)": flaps,
        "gear": gear,
        "autopilot": autopilot,
        "hydraulic_pressure (psi)": hydraulic_pressure,
        "stall_warning": stall_warning,
        "icing_warning": icing_warning,
        "alarms": alarms,
        "crash": 1 if scenario else 0
    })

    return flight_data

# Générer des vols avec répartition des crashs
scenarios = ["pitot_failure", "stall", "hydraulic_failure", "icing", "engine_failure"]
num_flights = 100  # Nombre total de vols
crash_flights = int(num_flights * 0.2)
normal_flights = num_flights - crash_flights

for flight_id in range(num_flights):
    if flight_id < crash_flights:
        scenario = scenarios[flight_id % len(scenarios)]  # Répartition équitable des scénarios
    else:
        scenario = None  # Vol normal
    flight_data = simulate_detailed_flight(flight_id, 3600, scenario)
    file_name = os.path.join(output_folder, f"flight_{flight_id}.csv")
    flight_data.to_csv(file_name, index=False)
    print(f"Vol {flight_id} sauvegardé dans {file_name} avec crash={bool(scenario)} ({scenario if scenario else 'normal'})")
