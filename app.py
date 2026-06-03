import re

import pandas as pd
import streamlit as st
from main import run_simulation

SCENARIOS = ["Normal Day", "Concert/Match Event"]
CAR_TYPES = ["Regular", "Electric", "Disabled", "LPG"]

# Sidebar controls
selected_scenario = st.sidebar.selectbox("Simülasyon Senaryosu", SCENARIOS)
highlight_types = st.sidebar.multiselect(
    "Araç Türlerini Vurgula",
    CAR_TYPES,
    default=["Electric", "Disabled", "LPG"]
)
search_keyword = st.sidebar.text_input("Log Ara")
selected_floor = "All"


@st.cache_data
def get_simulation_data(scenario):
    return run_simulation(scenario)


# Load simulation data
data, logs, occupancy_history, spot_events = get_simulation_data(selected_scenario)

# Floor options
floors = sorted({spot["floor"] for spot in data["spots"]})
floor_options = ["All"] + [str(floor) for floor in floors]
selected_floor = st.sidebar.selectbox("Kat Filtrele", floor_options)

# Page header
st.title("Akıllı Otopark Simülasyon Sistemi")
st.markdown(f"**Seçilen Senaryo:** {selected_scenario}")
st.markdown(f"**Simülasyon Süresi:** {data['scenario_summary']['sim_duration']} dk")

# Time slider
max_time = float(data["scenario_summary"]["sim_duration"])
current_time = st.slider("Zaman (dk)", 0.0, max_time, 0.0, step=0.1)


# Helpers

def get_spot_status_at_time(time):
    status_map = {
        spot["id"]: {
            "status": "empty",
            "car_type": None,
            "payment_type": None,
            "visit_reason": None,
            "floor": spot["floor"],
        }
        for spot in data["spots"]
    }

    for event in sorted(spot_events, key=lambda e: e["time"]):
        if event["time"] <= time:
            spot_state = status_map[event["spot_id"]]
            if event["status"] == "empty":
                spot_state["status"] = "empty"
                spot_state["car_type"] = None
                spot_state["payment_type"] = None
                spot_state["visit_reason"] = None
            else:
                spot_state["status"] = event["status"]
                spot_state["car_type"] = event.get("car_type")
                spot_state["payment_type"] = event.get("payment_type")
                spot_state["visit_reason"] = event.get("visit_reason")
            spot_state["floor"] = event.get("floor", spot_state["floor"])

    return status_map


def render_metric_card(title, value, subtitle, background):
    return f"""
<div style='padding:14px; border-radius:12px; background:{background}; min-width:160px; min-height:100px; color:#fff; display:flex; flex-direction:column; justify-content:space-between; overflow:hidden;'>
  <div style='font-size:13px; opacity:0.9; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{title}</div>
  <div style='font-size:24px; font-weight:700; margin:6px 0 6px 0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{value}</div>
  <div style='font-size:12px; opacity:0.85; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{subtitle}</div>
</div>
"""


def render_spot_card(spot_id, spot_info, is_highlight):
    # Minimal, clean card for each spot
    status = spot_info.get("status", "empty")
    car_type = spot_info.get("car_type")

    if status == "empty":
        emoji = "🟢"
        detail = "Boş"
        bg = "#f3f4f6"
        text_color = "#111111"
    elif car_type == "Electric":
        emoji = "⚡"
        detail = f"Elektrik / {spot_info.get('payment_type', '')}"
        bg = "#1f4c8d"
        text_color = "#ffffff"
    elif car_type == "Disabled":
        emoji = "♿"
        detail = f"Engelli / {spot_info.get('payment_type', '')}"
        bg = "#214f80"
        text_color = "#ffffff"
    else:
        emoji = "🚗"
        detail = f"Normal / {spot_info.get('payment_type', '')}"
        bg = "#2d6ca3"
        text_color = "#ffffff"

    border = "3px solid #ffbf00" if is_highlight else "1px solid #d1d5db"

    return f"""
<div style='padding:12px; margin:6px; border:{border}; border-radius:10px; background:{bg}; color:{text_color}; text-align:center; min-height:110px;'>
  <div style='font-size:22px;'>{emoji}</div>
  <div style='font-weight:700; margin-top:6px;'>Yer {spot_id}</div>
  <div style='font-size:12px; margin-top:4px;'>{detail}</div>
  <div style='font-size:11px; opacity:0.8; margin-top:6px;'>Kat {spot_info.get('floor', '')}</div>
</div>
"""


def parse_leave_duration(message):
    match = re.search(r"Süre: (\d+) dk", message)
    return int(match.group(1)) if match else 0


# Build filtered spot lists
current_status = get_spot_status_at_time(current_time)
selected_floor_value = None if selected_floor == "All" else int(selected_floor)
filtered_spots = sorted(
    [spot for spot in data["spots"] if selected_floor_value is None or spot["floor"] == selected_floor_value],
    key=lambda s: s["id"],
)
filtered_ids = {spot["id"] for spot in filtered_spots}
filtered_status = {spot_id: status for spot_id, status in current_status.items() if spot_id in filtered_ids}

filtered_total_spots = len(filtered_spots)
filtered_occupied = sum(1 for state in filtered_status.values() if state["status"] == "occupied")
filtered_electric = sum(1 for state in filtered_status.values() if state["status"] == "occupied" and state.get("car_type") == "Electric")
filtered_disabled = sum(1 for state in filtered_status.values() if state["status"] == "occupied" and state.get("car_type") == "Disabled")
filtered_occupancy_rate = filtered_occupied / filtered_total_spots if filtered_total_spots else 0
filtered_carbon_saved = filtered_electric * 0.75

# Top metrics (single neat row)
st.subheader("Üst Düzey Metrikler")
metric_cols = st.columns(5)
metric_items = [
    ("Toplam Kapasite", filtered_total_spots, "Seçili kat için toplam yer", "#0f172a"),
    ("Doluluk Oranı", f"{filtered_occupancy_rate * 100:.1f}%", "Mevcut doluluk", "#1d4ed8"),
    ("Elektrikli Araçlar", filtered_electric, "Bu kat üzerinde park etmiş", "#2563eb"),
    ("Engelli Araçlar", filtered_disabled, "Ayırılmış engelli alanları", "#1e40af"),
    ("Tahmini Karbon Tasarrufu", f"{filtered_carbon_saved:.1f} kg", "Elektrik araçları ile sağlandı", "#3b82f6"),
]
for col, item in zip(metric_cols, metric_items):
    col.markdown(render_metric_card(*item), unsafe_allow_html=True)

# Parking grid
st.subheader("Park Yeri Haritası")

if selected_floor_value is None:
    st.info("All seçildi: her kat ayrı ayrı gösterilir.")
    for floor in floors:
        st.markdown(f"#### Floor {floor}")
        floor_spots = sorted([spot for spot in filtered_spots if spot["floor"] == floor], key=lambda s: s["id"])
        # Ensure exactly 5 top and 5 bottom positions per floor in sequential order
        top_row = [s for s in floor_spots if s.get("y") == 0]
        bottom_row = [s for s in floor_spots if s.get("y") == 1]

        # Render rows using 5 columns each
        top_cols = st.columns(5)
        for col, spot in zip(top_cols, top_row[:5]):
            spot_info = filtered_status.get(spot["id"], {"status": "empty", "floor": spot["floor"]})
            col.markdown(render_spot_card(spot["id"], spot_info, spot_info.get("car_type") in highlight_types), unsafe_allow_html=True)

        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        bottom_cols = st.columns(5)
        for col, spot in zip(bottom_cols, bottom_row[:5]):
            spot_info = filtered_status.get(spot["id"], {"status": "empty", "floor": spot["floor"]})
            col.markdown(render_spot_card(spot["id"], spot_info, spot_info.get("car_type") in highlight_types), unsafe_allow_html=True)

        st.markdown("<hr style='margin:18px 0;'>", unsafe_allow_html=True)
else:
    floor_spots = sorted(filtered_spots, key=lambda s: s["id"])
    top_row = [s for s in floor_spots if s.get("y") == 0]
    bottom_row = [s for s in floor_spots if s.get("y") == 1]

    top_cols = st.columns(5)
    for col, spot in zip(top_cols, top_row[:5]):
        spot_info = filtered_status.get(spot["id"], {"status": "empty", "floor": spot["floor"]})
        col.markdown(render_spot_card(spot["id"], spot_info, spot_info.get("car_type") in highlight_types), unsafe_allow_html=True)

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

    bottom_cols = st.columns(5)
    for col, spot in zip(bottom_cols, bottom_row[:5]):
        spot_info = filtered_status.get(spot["id"], {"status": "empty", "floor": spot["floor"]})
        col.markdown(render_spot_card(spot["id"], spot_info, spot_info.get("car_type") in highlight_types), unsafe_allow_html=True)

# Occupancy chart
st.subheader("Doluluk Oranı Grafiği")
history_up_to_now = [entry for entry in occupancy_history if entry["time"] <= current_time]
if history_up_to_now:
    history_df = pd.DataFrame(history_up_to_now).set_index("time")
    st.line_chart(history_df["occupancy_rate"])
else:
    st.write("Henüz veri yok")

# Logs
st.subheader("İşlem Kayıtları")
logs_up_to_now = [entry for entry in logs if entry["time"] <= current_time]
filtered_logs = []
for entry in logs_up_to_now:
    search_lower = search_keyword.lower().strip()
    if search_lower:
        searchable = [
            str(entry.get("message", "")),
            str(entry.get("car_type", "")),
            str(entry.get("payment_type", "")),
            str(entry.get("payment_method", "")),
            str(entry.get("visit_reason", "")),
            str(entry.get("spot_id", "")),
            str(entry.get("floor", "")),
        ]
        if not any(search_lower in item.lower() for item in searchable):
            continue

    if highlight_types and entry.get("car_type") and entry["car_type"] not in highlight_types:
        continue

    filtered_logs.append(f"{entry['time']:.2f} - {entry['message']}")

if not filtered_logs:
    filtered_logs = ["Filtrelere uyan kayıt yok."]

st.text_area("Kayıtlar", "\n".join(filtered_logs), height=250)

# Summary / reports (collapsed)
with st.expander("Final Simülasyon Raporu", expanded=True):
    transaction_metrics = data.get("simulation_metrics", {})
    leave_events = [entry for entry in logs if entry.get("event") == "left"]
    payment_counts = pd.Series([entry.get("payment_type", "Unknown") for entry in leave_events]).value_counts()
    method_counts = pd.Series([entry.get("payment_method", "Unknown") for entry in leave_events]).value_counts()
    type_counts = pd.Series([entry.get("car_type", "Unknown") for entry in leave_events]).value_counts()

    total_revenue = transaction_metrics.get("revenue", 0.0)
    prepaid_count = transaction_metrics.get("prepaid_reservations", 0)

    st.markdown(f"**Toplam Simülasyon Geliri:** {total_revenue:.2f} TL")
    st.markdown(f"**Rezervasyonlu / Abonent Giriş Sayısı:** {prepaid_count}")
    report_cols = st.columns(2)
    report_cols[0].write("**Ödeme Türü Dağılımı**")
    report_cols[0].bar_chart(payment_counts)
    report_cols[1].write("**Ödeme Metodu Dağılımı**")
    report_cols[1].bar_chart(method_counts)

    summary_df = pd.DataFrame({
        "Özellik": ["Toplam Çıkış Yapan Araç", "Toplam Elektrikli Araç", "Toplam Engelli Araç"],
        "Değer": [len(leave_events), filtered_electric, filtered_disabled]
    })
    st.dataframe(summary_df, width=600)


with st.expander("📊 Özet Raporu", expanded=False):
    txn = data.get("simulation_metrics", {})
    rev = txn.get("revenue", 0.0)
    prepaid = txn.get("prepaid_reservations", 0)
    method_counts = txn.get("payment_method_counts", {})

    exp_cols = st.columns(3)
    exp_cols[0].markdown(render_metric_card("Toplam Gelir", f"{rev:.2f} TL", "Tahsilat", "#0f172a"), unsafe_allow_html=True)
    exp_cols[1].markdown(render_metric_card("Rezervasyonlu Giriş", prepaid, "Abonent Giriş", "#1d4ed8"), unsafe_allow_html=True)
    payment_lines = [f"{m}: {c}" for m, c in method_counts.items()]
    exp_cols[2].markdown(render_metric_card("Ödeme Türleri", "<br/>".join(payment_lines) if payment_lines else "Yok", "Dağılım", "#2563eb"), unsafe_allow_html=True)

    st.markdown("---")
    st.write("**İşlem Detayları**")
    leave_events = [entry for entry in logs if entry.get("event") == "left"]
    if leave_events:
        df = pd.DataFrame(leave_events)
        st.dataframe(df[["time", "spot_id", "floor", "car_type", "payment_type", "payment_method", "payment_amount"]].fillna("-"), use_container_width=True)
