"""
AstroVital - Módulo de IA

Detección de anomalías con Isolation Forest (scikit-learn):
  1. Al arrancar, el modelo aprende cómo se ven los signos vitales de un
     astronauta SANO (datos sintéticos basados en rangos fisiológicos normales).
  2. Cada lectura nueva recibe una puntuación: cuanto más "rara" respecto a lo
     aprendido, más baja es. La IA detecta combinaciones inusuales, no solo
     valores sueltos fuera de rango.
  3. El estado final combina la IA con límites médicos básicos, y se toma el
     más grave de los dos (así una falla del modelo nunca oculta una emergencia).
"""
import numpy as np
from sklearn.ensemble import IsolationForest

UMBRAL_PRECAUCION = -0.04  # puntuación IA por debajo de esto -> precaución (patrón inusual)
UMBRAL_ALERTA = -0.25      # puntuación IA por debajo de esto -> alerta (patrón muy extremo)
# Las emergencias "clásicas" (pulso > 120, SpO2 < 90, fiebre...) las cubren los
# límites médicos de _severidad_reglas; la IA aporta la alerta temprana.


def _datos_sanos(n=4000, semilla=42):
    rng = np.random.default_rng(semilla)
    mov = rng.uniform(-0.1, 1.1, n)                    # un poco más ancho que 0-1 para no castigar los bordes
    hr = 68 + 30 * mov + rng.normal(0, 3, n)           # más actividad -> más pulso
    spo2 = np.clip(rng.normal(97.8, 0.8, n), 93.5, 100)
    temp = rng.normal(36.6, 0.2, n)
    return np.column_stack([hr, spo2, temp, mov])


_modelo = IsolationForest(n_estimators=200, random_state=42)
_modelo.fit(_datos_sanos())


def _severidad_reglas(hr, spo2, temp):
    """0 = normal, 1 = precaución, 2 = alerta (límites médicos básicos)."""
    if hr > 120 or hr < 45 or spo2 < 90 or temp > 38.5 or temp < 35.0:
        return 2
    if hr > 100 or hr < 55 or spo2 < 95 or temp > 37.5 or temp < 36.0:
        return 1
    return 0


def _severidad_ia(puntuacion):
    if puntuacion < UMBRAL_ALERTA:
        return 2
    if puntuacion < UMBRAL_PRECAUCION:
        return 1
    return 0


def _causas(hr, spo2, temp):
    c = []
    if hr > 100:
        c.append("ritmo cardiaco elevado")
    if hr < 55:
        c.append("ritmo cardiaco bajo")
    if spo2 < 95:
        c.append("oxígeno bajo")
    if temp > 37.5:
        c.append("temperatura alta")
    if temp < 36.0:
        c.append("temperatura baja")
    return c


ESTADOS = ["normal", "precaucion", "alerta"]


def evaluar(hr, spo2, temp, mov):
    """Devuelve (estado, recomendacion, puntuacion_ia)."""
    x = np.array([[hr, spo2, temp, mov]])
    puntuacion = float(_modelo.decision_function(x)[0])
    nivel = max(_severidad_reglas(hr, spo2, temp), _severidad_ia(puntuacion))
    estado = ESTADOS[nivel]
    causas = _causas(hr, spo2, temp)
    detalle = ", ".join(causas) if causas else "patrón inusual en los signos vitales"

    if estado == "normal":
        reco = "Signos vitales estables. Continúe con su rutina."
    elif estado == "precaucion":
        reco = f"Atención: {detalle}. Descanse, respire profundo y vuelva a medir en unos minutos."
    else:
        reco = f"Emergencia: {detalle}. Siga el protocolo médico y contacte a la Tierra."
    return estado, reco, round(puntuacion, 4)
