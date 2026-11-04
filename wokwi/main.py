# AstroVital - Simulación IoT en Wokwi (MicroPython, ESP32). Datos educativos, no clínicos.
# Controles:
#   Potenciómetro   = actividad física (sube pulso y suma minutos de ejercicio)
#   Botón amarillo  = ESTRÉS          -> precaución
#   Botón azul      = FIEBRE          -> alerta
#   Botón rojo      = HIPOXIA         -> alerta
#   Botón blanco    = TORMENTA SOLAR  -> radiación alta
#   (basta pulsar; cada escenario dura unos 16 s). Los LEDs muestran el estado OFICIAL de la IA.
import json
import random
import time

import network
from machine import ADC, PWM, Pin

try:
    import urequests as requests
except ImportError:
    import requests

API_URL = "https://astrovital.onrender.com/lecturas"
API_KEY = "astrovital-2026"   # igual que API_KEY en Render
ASTRONAUTA = "Astronauta 1"
INTERVALO_S = 2

pot_actividad = ADC(Pin(34))
try:
    pot_actividad.atten(ADC.ATTN_11DB)
except Exception:
    pass

BOTONES = {
    "estres": Pin(18, Pin.IN, Pin.PULL_UP),
    "fiebre": Pin(19, Pin.IN, Pin.PULL_UP),
    "hipoxia": Pin(21, Pin.IN, Pin.PULL_UP),
    "tormenta": Pin(22, Pin.IN, Pin.PULL_UP),
}
led_verde = Pin(25, Pin.OUT)
led_amarillo = Pin(26, Pin.OUT)
led_rojo = Pin(27, Pin.OUT)
buzzer = PWM(Pin(14))
buzzer.freq(1200)


def sonar(on):
    try:
        buzzer.duty_u16(32768 if on else 0)
    except AttributeError:
        buzzer.duty(512 if on else 0)


sonar(False)


def actividad():
    try:
        return pot_actividad.read_u16() / 65535
    except AttributeError:
        return pot_actividad.read() / 4095


def ruido(a):
    return (random.random() - 0.5) * 2 * a


def clasificar(hr, spo2, temp):
    if hr > 120 or hr < 45 or spo2 < 90 or temp > 38.5:
        return "alerta"
    if hr > 100 or hr < 55 or spo2 < 95 or temp > 37.5:
        return "precaucion"
    return "normal"


def mostrar(estado):
    led_verde.value(estado == "normal")
    led_amarillo.value(estado == "precaucion")
    led_rojo.value(estado == "alerta")


def conectar_wifi():
    sta = network.WLAN(network.STA_IF)
    sta.active(True)
    if not sta.isconnected():
        sta.connect("Wokwi-GUEST", "")
        for _ in range(100):
            if sta.isconnected():
                break
            time.sleep(0.2)
    print("Wi-Fi:", sta.isconnected())


def enviar(payload):
    """Envía la lectura; devuelve el estado oficial de la IA (o None si falla)."""
    r = None
    try:
        r = requests.post(API_URL, data=json.dumps(payload),
                          headers={"Content-Type": "application/json", "x-api-key": API_KEY})
        print("   API:", r.status_code)
        if r.status_code == 200:
            return r.json().get("estado")
        print("   ", r.text[:120])
    except Exception as e:
        print("   Error al enviar:", e)
    finally:
        if r is not None:
            r.close()
    return None


print("=== AstroVital: monitor de salud (simulación) ===")
conectar_wifi()
hr, spo2, temp, sueno = 72.0, 98.0, 36.6, 7.2
ejercicio = 0.0
escenario, restante = None, 0
pulsados = {k: False for k in BOTONES}
ultimo = time.ticks_ms()

while True:
    for k, pin in BOTONES.items():          # revisar botones varias veces por segundo
        if pin.value() == 0:
            pulsados[k] = True
    time.sleep(0.05)
    if time.ticks_diff(time.ticks_ms(), ultimo) < INTERVALO_S * 1000:
        continue
    ultimo = time.ticks_ms()

    act = actividad()
    obj_hr, obj_spo2, obj_temp = 68 + act * 30, 98.0, 36.6
    obj_sueno, obj_estres, radiacion = 7.2, 20 + 15 * act, 18 + ruido(3)   # ~18 µSv/h: orden de magnitud de órbita baja (simulado)

    for k in pulsados:
        if pulsados[k]:
            escenario, restante = k, 8
    pulsados = {k: False for k in BOTONES}

    if restante > 0:
        restante -= 1
        if escenario == "estres":
            obj_hr, obj_temp, obj_spo2, obj_estres, obj_sueno = 108, 37.6, 96, 85, 5.4
        elif escenario == "fiebre":
            obj_hr, obj_temp, obj_spo2, obj_estres = 126, 39.1, 95, 60
        elif escenario == "hipoxia":
            obj_hr, obj_temp, obj_spo2, obj_estres = 112, 36.8, 86, 60
        elif escenario == "tormenta":
            obj_hr, obj_estres, radiacion = 92, 62, 140 + ruido(10)

    hr += (obj_hr - hr) * 0.6 + ruido(1.5)
    spo2 = min(spo2 + (obj_spo2 - spo2) * 0.6 + ruido(0.3), 100.0)
    temp += (obj_temp - temp) * 0.6 + ruido(0.05)
    sueno += (obj_sueno - sueno) * 0.3 + ruido(0.05)
    estres = max(0, min(100, obj_estres + ruido(3)))
    if act > 0.6:                           # 1 lectura de esfuerzo = 1 min simulado de ejercicio
        ejercicio = min(180, ejercicio + 1)

    local = clasificar(hr, spo2, temp)
    mostrar(local)
    print("[{:<10}] FC={:5.1f} SpO2={:5.1f} T={:4.1f} sueño={:.1f} estrés={:.0f} ejer={:.0f} rad={:.0f}".format(
        local, hr, spo2, temp, sueno, estres, ejercicio, radiacion))

    oficial = enviar({
        "astronauta": ASTRONAUTA,
        "ritmo_cardiaco": round(hr, 1), "spo2": round(spo2, 1),
        "temperatura": round(temp, 2), "movimiento": round(act, 2),
        "sueno_horas": round(sueno, 1), "estres": round(estres, 1),
        "ejercicio_min": round(ejercicio, 1), "radiacion": round(radiacion, 1),
        "estado_local": local,
    })
    estado = oficial if oficial in ("normal", "precaucion", "alerta") else local
    mostrar(estado)
    if estado == "alerta":
        sonar(True)
        time.sleep(0.3)
        sonar(False)
