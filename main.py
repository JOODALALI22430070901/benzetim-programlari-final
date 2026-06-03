import simpy
import random

def load_config():
    # Programmatically generate 30 parking spots and bypass JSON file loading
    spots = []
    for spot_id in range(1, 31):
        floor = (spot_id - 1) // 10
        floor_index = (spot_id - 1) % 10
        x = floor_index % 5
        y = floor_index // 5
        spots.append({
            "id": spot_id,
            "floor": floor,
            "x": x,
            "y": y,
            "status": "empty",
            "disabled_spot": floor_index in {0, 3, 6},
            "charger": floor_index in {1, 4, 7}
        })

    data = {
        "parking_lot_name": "Smart City Parking",
        "total_spots": len(spots),
        "spots": spots
    }
    return data

def choose_spot_for_car(car_type, spots_data):
    empty_spots = [spot for spot in spots_data if spot["status"] == "empty"]

    if car_type == "LPG":
        eligible = [spot for spot in empty_spots if spot["floor"] == 0]
        if eligible:
            return random.choice(eligible)
        return None

    if car_type == "Disabled":
        preferred = [spot for spot in empty_spots if spot.get("disabled_spot")]
        if preferred:
            return random.choice(preferred)

    if car_type == "Electric":
        preferred = [spot for spot in empty_spots if spot.get("charger")]
        if preferred:
            return random.choice(preferred)

    return random.choice(empty_spots) if empty_spots else None

def get_visit_reason_and_duration(scenario="Normal Day"):
    reasons = ["Quick Visit", "Leisure/Family Shopping", "Work/Business"]
    weights = [0.4, 0.35, 0.25]
    reason = random.choices(reasons, weights=weights, k=1)[0]
    if reason == "Quick Visit":
        duration = random.randint(15, 45)
    elif reason == "Leisure/Family Shopping":
        duration = random.randint(60, 180)
    else:
        duration = random.randint(240, 600)

    if scenario == "Heavy Rainy Day":
        duration = int(duration * 1.3)
    return reason, duration

def get_arrival_interval(now, scenario="Normal Day"):
    if scenario == "Concert/Match Event" and now < 30:
        return 0.5
    if 0 <= now < 20 or 60 <= now < 80:
        return 1.5
    return 5.0

def car(env, name, parking_lot, spots_data, logs, occupancy_history, spot_events, metrics, scenario="Normal Day"):
    arrival_time = env.now
    car_type = random.choice(["Regular", "Electric", "Disabled", "LPG"])
    payment_type = random.choice(["Abonent", "Bilet"])
    payment_method = random.choice(["Mobil Uygulama", "Kredi Kartı", "Nakit"])
    visit_reason, parking_duration = get_visit_reason_and_duration(scenario)

    logs.append({
        "time": arrival_time,
        "message": f"{name} ({car_type}, {payment_type}) otoparka geldi ve sebep: {visit_reason}",
        "car_type": car_type,
        "payment_type": payment_type,
        "payment_method": payment_method,
        "visit_reason": visit_reason,
        "spot_id": None,
        "floor": None,
        "event": "arrival"
    })

    # Uygun park yeri bulunana kadar bekler
    while True:
        assigned_spot = choose_spot_for_car(car_type, spots_data)
        if assigned_spot is not None:
            break

        waiting_message = f"{name} uygun park yeri arıyor... ({car_type})"
        if scenario == "Heavy Rainy Day":
            waiting_message = f"{name} girişte uzun kuyrukta bekliyor - kötü hava koşulları nedeniyle."

        logs.append({
            "time": env.now,
            "message": waiting_message,
            "car_type": car_type,
            "payment_type": payment_type,
            "visit_reason": visit_reason,
            "spot_id": None,
            "floor": None,
            "event": "waiting"
        })
        yield env.timeout(1)

    with parking_lot.request() as request:
        yield request

        assigned_spot["status"] = "occupied"
        spot_id = assigned_spot["id"]
        floor = assigned_spot["floor"]

        start_parking = env.now
        logs.append({
            "time": start_parking,
            "message": f"{name} ({car_type}, {payment_type}) Spot {spot_id} kat {floor} konumuna park etti",
            "car_type": car_type,
            "payment_type": payment_type,
            "visit_reason": visit_reason,
            "spot_id": spot_id,
            "floor": floor,
            "event": "parked"
        })
        spot_events.append({
            "time": start_parking,
            "spot_id": spot_id,
            "status": "occupied",
            "car_type": car_type,
            "payment_type": payment_type,
            "visit_reason": visit_reason,
            "floor": floor
        })

        occupied_count = sum(1 for s in spots_data if s["status"] == "occupied")
        occupancy_rate = occupied_count / len(spots_data)
        occupancy_history.append({
            "time": start_parking,
            "occupancy_rate": occupancy_rate
        })

        yield env.timeout(parking_duration)

        assigned_spot["status"] = "empty"
        leave_time = env.now
        payment_rate = {
            "Mobil Uygulama": 0.55,
            "Kredi Kartı": 0.50,
            "Nakit": 0.45
        }[payment_method]
        payment_amount = round(parking_duration * payment_rate, 2)
        metrics["revenue"] += payment_amount
        if payment_type == "Abonent":
            metrics["prepaid_reservations"] += 1
        metrics["payment_method_counts"][payment_method] += 1

        logs.append({
            "time": leave_time,
            "message": f"{name} ({car_type}, {payment_type}) ayrıldı (Süre: {parking_duration} dk, sebep: {visit_reason}, ödeme: {payment_method})",
            "car_type": car_type,
            "payment_type": payment_type,
            "payment_method": payment_method,
            "visit_reason": visit_reason,
            "spot_id": spot_id,
            "floor": floor,
            "event": "left",
            "payment_amount": payment_amount
        })
        spot_events.append({
            "time": leave_time,
            "spot_id": spot_id,
            "status": "empty",
            "car_type": car_type,
            "payment_type": payment_type,
            "visit_reason": visit_reason,
            "floor": floor
        })

        occupied_count = sum(1 for s in spots_data if s["status"] == "occupied")
        occupancy_rate = occupied_count / len(spots_data)
        occupancy_history.append({
            "time": leave_time,
            "occupancy_rate": occupancy_rate
        })

def traffic_generator(env, parking_lot, spots_data, logs, occupancy_history, spot_events, metrics, scenario="Normal Day"):
    car_count = 0
    while True:
        interval = get_arrival_interval(env.now, scenario)
        yield env.timeout(random.expovariate(1.0 / interval))
        car_count += 1
        env.process(car(env, f"Arac_{car_count}", parking_lot, spots_data, logs, occupancy_history, spot_events, metrics, scenario))

def run_simulation(scenario="Normal Day"):
    # Simülasyonu çalıştırır ve verileri döndürür
    data = load_config()
    env = simpy.Environment()
    capacity = data["total_spots"]
    parking_resource = simpy.Resource(env, capacity=capacity)
    
    logs = []
    occupancy_history = []
    spot_events = []
    metrics = {
        "revenue": 0.0,
        "prepaid_reservations": 0,
        "payment_method_counts": {
            "Mobil Uygulama": 0,
            "Kredi Kartı": 0,
            "Nakit": 0
        }
    }

    logs.append({
        "time": 0,
        "message": f"Senaryo: {scenario} ile simülasyon başladı.",
        "car_type": None,
        "payment_type": None,
        "visit_reason": None,
        "spot_id": None,
        "floor": None,
        "event": "scenario_start"
    })

    if scenario == "Concert/Match Event":
        sim_duration = 200
    else:
        sim_duration = 100

    env.process(traffic_generator(env, parking_resource, data["spots"], logs, occupancy_history, spot_events, metrics, scenario))
    env.run(until=sim_duration)

    data["scenario"] = scenario
    data["scenario_summary"] = {
        "sim_duration": sim_duration,
        "event_peak": scenario == "Concert/Match Event"
    }
    data["simulation_metrics"] = metrics
    
    return data, logs, occupancy_history, spot_events

# Eğer bu dosya doğrudan çalıştırılırsa, simülasyonu çalıştır
if __name__ == "__main__":
    data, logs, occupancy_history, spot_events = run_simulation()
    # Konsola logları yazdır (test için)
    for time, msg in logs:
        print(f"{time:.2f}: {msg}")
