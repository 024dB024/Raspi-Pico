import subprocess
import sys
import time

import streamlit as st


# Fuehrt MicroPython-Code auf dem Pico ueber mpremote aus.
def run_on_pico(code: str, port: str = "auto", exec_timeout_s: float = 20.0):
    cmd = [sys.executable, "-m", "mpremote", "connect", port, "exec", code]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=exec_timeout_s)
    return proc.stdout.strip(), proc.stderr.strip(), proc.returncode


# Liest alle DS18B20-Sensoren am angegebenen DATA-Pin aus.
def read_ds18b20_temps(port: str = "auto", data_pin: int = 2):
    code = f'''
from machine import Pin
import onewire
import ds18x20
import time

ow = onewire.OneWire(Pin({data_pin}))
ds = ds18x20.DS18X20(ow)
roms = ds.scan()

if not roms:
    print("NO_SENSOR")
else:
    ds.convert_temp()
    time.sleep_ms(750)
    for idx, rom in enumerate(roms, start=1):
        temp_c = ds.read_temp(rom)
        print(f"{{idx}},{{temp_c:.2f}}")
'''

    out, err, rc = run_on_pico(code=code, port=port)

    if rc != 0 or err:
        raise RuntimeError(err or "Unbekannter mpremote-Fehler")

    if not out:
        raise RuntimeError("Keine Ausgabe vom Pico erhalten")

    lines = [line.strip() for line in out.splitlines() if line.strip()]

    if lines == ["NO_SENSOR"]:
        raise RuntimeError("Kein DS18B20 gefunden. Verkabelung und 4.7 kOhm Pull-up pruefen.")

    results = []
    for line in lines:
        idx_str, temp_str = line.split(",")
        results.append((int(idx_str), float(temp_str)))

    return results


st.set_page_config(page_title="Pico DS18B20 Live Temperatur", layout="wide")

st.title("Raspberry Pi Pico - DS18B20 Live Temperatur")
st.caption("Live-Messung mit Streamlit und mpremote")

port = st.sidebar.text_input("Port", value="auto")
data_pin = st.sidebar.number_input("Daten-Pin (GP)", min_value=0, max_value=28, value=2, step=1)
num_samples = st.sidebar.slider("Anzahl Messpunkte", min_value=10, max_value=600, value=60, step=10)
interval_s = st.sidebar.slider("Intervall (Sekunden)", min_value=0.2, max_value=5.0, value=1.0, step=0.1)

start = st.button("Messung starten")

if start:
    chart = st.empty()
    status = st.empty()
    table_placeholder = st.empty()
    progress = st.progress(0)

    sensor_history = {}

    for i in range(num_samples):
        try:
            measurements = read_ds18b20_temps(port=port, data_pin=int(data_pin))
        except Exception as exc:
            st.error(f"Messung fehlgeschlagen bei Punkt {i + 1}: {exc}")
            break

        current_values = {}
        for sensor_idx, temp_c in measurements:
            key = f"sensor_{sensor_idx}"
            sensor_history.setdefault(key, []).append(temp_c)
            current_values[key] = temp_c

        chart.line_chart(sensor_history)
        table_placeholder.dataframe(
            [{"Sensor": key, "Temperatur (°C)": value} for key, value in current_values.items()],
            use_container_width=True,
        )

        status.write(
            f"Punkt {i + 1}/{num_samples}: "
            + ", ".join([f"{key}={value:.2f} °C" for key, value in current_values.items()])
        )
        progress.progress(int(((i + 1) / num_samples) * 100))

        time.sleep(interval_s)
else:
    st.info("Pico per USB verbinden, DS18B20 anschliessen und dann auf 'Messung starten' klicken.")
