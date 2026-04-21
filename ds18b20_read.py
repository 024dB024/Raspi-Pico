from machine import Pin
import onewire
import ds18x20
import time

DATA_PIN = 2
INTERVAL_S = 1.0

ow = onewire.OneWire(Pin(DATA_PIN))
ds = ds18x20.DS18X20(ow)

roms = ds.scan()
print("Gefundene Sensoren:", roms)

if not roms:
    print("Kein DS18B20 gefunden. Verkabelung und 4.7 kOhm Pull-up pruefen.")
    raise SystemExit

print("Starte Messung. Abbruch mit Ctrl+C")

while True:
    ds.convert_temp()
    time.sleep_ms(750)

    for idx, rom in enumerate(roms, start=1):
        temp_c = ds.read_temp(rom)
        print("Sensor", idx, "Temp:", temp_c, "C")

    print("---")
    time.sleep(INTERVAL_S)