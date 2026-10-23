"""
AstroVital - API (FastAPI)
Recibe lecturas del ESP32 (Wokwi), las evalúa con la IA y las guarda en Supabase.

Variables de entorno (se configuran en Render, NUNCA en el código):
    SUPABASE_URL         ej: https://abcd1234.supabase.co
    SUPABASE_SECRET_KEY  la clave SECRETA de Supabase (sb_secret_... o service_role)
    API_KEY              clave simple que debe enviar Wokwi en el header x-api-key
"""
import os
from typing import Optional

import requests
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from modelo import evaluar

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SECRET_KEY", "")
API_KEY = os.getenv("API_KEY", "")

app = FastAPI(title="AstroVital API", version="1.0")


class Lectura(BaseModel):
    astronauta: str = "Astronauta 1"
    ritmo_cardiaco: float = Field(ge=20, le=250)
    spo2: float = Field(ge=50, le=100)
    temperatura: float = Field(ge=30, le=45)
    movimiento: float = Field(default=0, ge=0, le=1)
    estado_local: Optional[str] = None  # lo calcula el ESP32 para sus LEDs; aquí se ignora


def guardar_en_supabase(fila: dict) -> None:
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    # Las claves nuevas (sb_secret_...) van solo en "apikey"; las antiguas (JWT) también en Authorization
    if not SUPABASE_KEY.startswith("sb_"):
        headers["Authorization"] = f"Bearer {SUPABASE_KEY}"
    r = requests.post(f"{SUPABASE_URL}/rest/v1/lecturas", json=fila, headers=headers, timeout=10)
    if not r.ok:
        raise HTTPException(status_code=502, detail=f"Supabase respondió {r.status_code}: {r.text[:200]}")


@app.get("/")
def estado_servicio():
    """Sirve para despertar la API en Render antes de la demo."""
    return {
        "servicio": "AstroVital API",
        "estado": "ok",
        "supabase_configurado": bool(SUPABASE_URL and SUPABASE_KEY),
        "api_key_configurada": bool(API_KEY),
    }


@app.post("/lecturas")
def recibir_lectura(lectura: Lectura, x_api_key: Optional[str] = Header(default=None)):
    if API_KEY and x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="x-api-key inválida")

    estado, recomendacion, puntuacion = evaluar(
        lectura.ritmo_cardiaco, lectura.spo2, lectura.temperatura, lectura.movimiento
    )

    fila = {
        "astronauta": lectura.astronauta,
        "ritmo_cardiaco": lectura.ritmo_cardiaco,
        "spo2": lectura.spo2,
        "temperatura": lectura.temperatura,
        "movimiento": lectura.movimiento,
        "estado": estado,
        "recomendacion": recomendacion,
    }

    guardado = False
    if SUPABASE_URL and SUPABASE_KEY:
        guardar_en_supabase(fila)
        guardado = True

    return {"estado": estado, "recomendacion": recomendacion, "puntuacion_ia": puntuacion, "guardado": guardado}
