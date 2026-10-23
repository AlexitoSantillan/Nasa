# AstroVital - ESP32 en Wokwi (MicroPython)
# Lee sensores simulados, manda la lectura a la API en Render y enciende
# el LED según el estado que devuelve la IA.
import network, time, machine, urequests, ujson, random

# ====== CONFIGURA ESTO ======
API_URL = "https://TU-SERVICIO.onrender.com/lecturas"   # URL de Render + /lecturas
API_KEY = "la-misma-que-pusiste-en-Render"
ASTRONAUTA = "Astronauta 1"
INTERVALO_S = 2
# ============================

pot_mov = machine.ADC(machine.Pin(34))
pot_mov.atten(machine.ADC.ATTN_11DB)
btn_taqui = machine.Pin(25, machine.Pin.IN, machine.Pin.PULL_UP)   # mantener = taquicardia
btn_hipox = machine.Pin(26, machine.Pin.IN, machine.Pin.PULL_UP)   # mantener = oxígeno bajo
btn_fiebre = machine.Pin(27, machine.Pin.IN, machine.Pin.PULL_UP)  # mantener = fiebre
led_verde = machine.Pin(13, machine.Pin.OUT)
led_ambar = machine.Pin(12, machine.Pin.OUT)
led_rojo = machine.Pin(14, machine.Pin.OUT)


def leds(estado):
    led_verde.value(estado == "normal")
    led_ambar.value(estado == "precaucion")
    led_rojo.value(estado == "alerta")


def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Conectando a Wi-Fi", end="")
        wlan.connect("Wokwi-GUEST", "", 6)
        while not wlan.isconnected():
            print(".", end="")
            time.sleep(0.25)
    print("\nWi-Fi OK:", wlan.ifconfig()[0])


def leer_sensores():
    mov = pot_mov.read() / 4095            # 0 = reposo, 1 = ejercicio
    hr = 68 + 30 * mov + random.uniform(-3, 3)
    spo2 = 97.8 + random.uniform(-0.8, 0.8)
    temp = 36.6 + random.uniform(-0.2, 0.2)
    if btn_taqui.value() == 0:
        hr = 135 + random.uniform(-4, 4)
    if btn_hipox.value() == 0:
        spo2 = 86 + random.uniform(-1, 1)
    if btn_fiebre.value() == 0:
        temp = 39.0 + random.uniform(-0.2, 0.2)
    return round(hr, 1), round(min(spo2, 100), 1), round(temp, 2), round(mov, 2)


def estado_local(hr, spo2, temp):
    # Respaldo si no hay red: mismas reglas médicas básicas de la API
    if hr > 120 or hr < 45 or spo2 < 90 or temp > 38.5 or temp < 35:
        return "alerta"
    if hr > 100 or hr < 55 or spo2 < 95 or temp > 37.5 or temp < 36:
        return "precaucion"
    return "normal"


def enviar(hr, spo2, temp, mov):
    cuerpo = ujson.dumps({
        "astronauta": ASTRONAUTA,
        "ritmo_cardiaco": hr, "spo2": spo2,
        "temperatura": temp, "movimiento": mov,
    })
    r = urequests.post(API_URL, data=cuerpo,
                       headers={"Content-Type": "application/json", "x-api-key": API_KEY})
    try:
        if r.status_code == 200:
            return r.json()
        print("API respondió", r.status_code, r.text[:120])
    finally:
        r.close()
    return None


conectar_wifi()
leds("normal")
while True:
    hr, spo2, temp, mov = leer_sensores()
    print("HR", hr, "SpO2", spo2, "T", temp, "mov", mov)
    try:
        resp = enviar(hr, spo2, temp, mov)
        if resp:
            print("IA ->", resp["estado"], "| puntuación", resp["puntuacion_ia"])
            leds(resp["estado"])
        else:
            leds(estado_local(hr, spo2, temp))
    except Exception as e:
        print("Error de red:", e)
        leds(estado_local(hr, spo2, temp))   # el astronauta sigue protegido sin conexión
    time.sleep(INTERVALO_S)
