from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import projects, equipment, points, control  # control router'ı eklendi
from app.services.bms_engine import bms_engine

app = FastAPI(
    title="Fieldnote BMS Studio",
    description="React, FastAPI, SQLite backed local-first HVAC & BMS Assistant",
    version="1.1.0"
)

# Frontend (Vite) entegrasyonu için CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mevcut rotalar ve yeni eklenen Canlı Kontrol (Control) rotası
app.include_router(projects.router)
app.include_router(equipment.router)
app.include_router(points.router)
app.include_router(control.router)  # <-- Rota buraya bağlandı

@app.on_event("shutdown")
async def shutdown_event():
    """Uygulama kapanırken aktif Modbus TCP/RTU seri port ve soket bağlantılarını temizler"""
    print("[BMS Engine] Kapatılıyor, tüm aktif adaptör bağlantıları kesiliyor...")
    await bms_engine.shutdown()

@app.get("/")
def read_root():
    return {"status": "online", "system": "Fieldnote BMS Studio"}
