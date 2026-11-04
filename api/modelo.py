"""
AstroVital - Módulo de IA (v2)

1) Isolation Forest aprende cómo se ven los signos de un astronauta SANO
   (FC, SpO2, temperatura, movimiento, sueño y estrés; datos sintéticos).
2) Reglas por CATEGORÍA (cardiovascular, respiratoria, térmica, conductual,
   radiación) con límites básicos. Los umbrales de sueño, estrés y radiación
   son valores de referencia simulados: ajústalos con los Resources de la NASA.
3) El estado global es el más grave entre la IA y las categorías, así una
   falla del modelo nunca oculta una emergencia.
"""
import numpy as np
from sklearn.ensemble import IsolationForest

UMBRAL_PRECAUCION = -0.04
UMBRAL_ALERTA = -0.25
ESTADOS = ["normal", "precaucion", "alerta"]


def _datos_sanos(n=4000, semilla=42):
    rng = np.random.default_rng(semilla)
    mov = rng.uniform(-0.1, 1.1, n)
    hr = 68 + 30 * mov + rng.normal(0, 3, n)
    spo2 = np.clip(rng.normal(97.8, 0.8, n), 93.5, 100)
    temp = rng.normal(36.6, 0.2, n)
    sueno = np.clip(rng.normal(7.2, 0.9, n), 5.0, 10.0)
    estres = np.clip(rng.normal(25, 12, n), 0, 60)
    return np.column_stack([hr, spo2, temp, mov, sueno, estres])


_modelo = IsolationForest(n_estimators=200, random_state=42)
_modelo.fit(_datos_sanos())


def _nivel(valor, prec, alerta, mayor=True):
    """Devuelve 0/1/2 según cruce de umbrales (mayor=True: peor si sube)."""
    if mayor:
        return 2 if valor > alerta else 1 if valor > prec else 0
    return 2 if valor < alerta else 1 if valor < prec else 0


def categorias(hr, spo2, temp, sueno, estres, radiacion):
    return {
        "cardiovascular": max(_nivel(hr, 100, 120), _nivel(hr, 55, 45, mayor=False)),
        "respiratoria": _nivel(spo2, 95, 90, mayor=False),
        "termica": max(_nivel(temp, 37.5, 38.5), _nivel(temp, 36.0, 35.0, mayor=False)),
        "conductual": max(_nivel(sueno, 6, 4, mayor=False), _nivel(estres, 60, 80)),
        "radiacion": _nivel(radiacion, 40, 100),
    }


def _severidad_ia(p):
    return 2 if p < UMBRAL_ALERTA else 1 if p < UMBRAL_PRECAUCION else 0


ACCIONES = {
    "cardiovascular": "ritmo cardiaco fuera de rango: reposo y monitoreo continuo",
    "respiratoria": "oxígeno bajo: revisar ventilación y respirar profundo",
    "termica": "temperatura anormal: hidratación y control térmico del módulo",
    "conductual": "sueño o estrés fuera de rango: descanso y pausa guiada",
    "radiacion": "radiación elevada: moverse a la zona blindada",
}


def evaluar(hr, spo2, temp, mov, sueno=7.2, estres=25, radiacion=18):
    """Devuelve (estado, recomendacion, puntuacion_ia, categorias_por_nombre)."""
    p = float(_modelo.decision_function(np.array([[hr, spo2, temp, mov, sueno, estres]]))[0])
    cats = categorias(hr, spo2, temp, sueno, estres, radiacion)
    nivel = max(max(cats.values()), _severidad_ia(p))
    estado = ESTADOS[nivel]
    activas = [ACCIONES[k] for k, v in cats.items() if v == nivel and v > 0]
    detalle = "; ".join(activas) if activas else "patrón inusual en los signos vitales"
    if estado == "normal":
        reco = "Signos vitales estables. Continúe con su rutina."
    elif estado == "precaucion":
        reco = f"Atención: {detalle}. Vuelva a medir en unos minutos."
    else:
        reco = f"Emergencia: {detalle}. Siga el protocolo médico y contacte a la Tierra."
    return estado, reco, round(p, 4), {k: ESTADOS[v] for k, v in cats.items()}
