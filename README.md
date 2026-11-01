# HvacBMS_assistant
Local-first HVAC and building management studio with React, FastAPI, SQLite, and simulated equipment monitoring.

# Fieldnote BMS Studio (HvacBMS_assistant)

React, FastAPI ve SQLite altyapısı üzerine kurulu, yerel öncelikli (local-first) bir HVAC ve Bina Yönetim Sistemi (BMS) kontrol stüdyosudur. Proje; simüle edilmiş ve gerçek zamanlı endüstriyel saha ekipmanlarının izlenmesi, yönetilmesi ve öncelik tabanlı kontrol işlemlerinin (Read/Write) merkezi bir mimariden yürütülmesini sağlar.

## 🗂️ Proje Yapısı (Layout)

```text
HvacBMS_assistant/
├── backend/                  # FastAPI Backend Servisi
│   └── app/
│       ├── main.py           # Uygulamanın ana giriş noktası & API entegrasyonu
│       ├── adapters/         # Endüstriyel Protokol Adaptörleri (Read/Write)
│       │   ├── base.py       # Standart PointValue şeması ve Soyut Adaptör Sınıfı
│       │   ├── simulator.py  # Canlı bellek içi (In-Memory) ekipman simülatörü
│       │   └── modbus.py     # Asenkron Modbus TCP ve RTU (RS-485) adaptörleri
│       ├── routers/          # API Endpoint/Rota tanımlamaları
│       │   ├── projects.py   # Proje yönetim servisleri
│       │   ├── equipment.py  # Saha ekipmanları yönetimi
│       │   ├── points.py     # Nokta (Point) konfigürasyonları
│       │   └── control.py    # Canlı veri okuma ve öncelik tabanlı yazma (Write) rotası
│       └── services/         # BMS Motoru ve Merkezi Yönetim
│           └── bms_engine.py # Adaptör yaşam döngüsü ve bağlantı yöneticisi
└── src/                      # Frontend (React + TypeScript + Vite)
```

## 🛠️ Sistem Gereksinimleri

- **Python:** 3.10 veya üzeri
- **Node.js:** 20 veya üzeri

## 🚀 Yerel Kurulum ve Çalıştırma

### 1. Frontend (Arayüz) Kurulumu
Projenin kök dizininde bir terminal açarak Vite sunucusunu başlatın:
```powershell
npm install
npm run dev
```

### 2. Backend (FastAPI API) Kurulumu
İkinci bir terminal açarak sanal ortamı kurun ve API sunucusunu başlatın:
```powershell
# Sanal ortam oluşturma ve aktif etme
py -m venv .venv
.\.venv\Scripts\activate

# Bağımlılıkların yüklenmesi
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# API dizinine geçiş ve sunucunun başlatılması
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

- **Uygulama Arayüzü:** Frontend terminalinde gösterilen yerel Vite URL'si üzerinden (Varsayılan: `http://localhost:5173`) erişilebilir.
- **Backend API:** `http://127.0.0.1:8000` adresinde aktiftir.
- **İnteraktif API Dokümantasyonu (Swagger):** `http://127.0.0` adresinden test edilebilir.

*Not: SQLite veritabanı dosyası ilk başlatmada otomatik olarak `backend/data/bms.db` yolunda oluşturulur. Farklı bir konum belirtmek için `BMS_DB_PATH` ortam değişkenini kullanabilirsiniz.*

## 🎯 Mevcut Kapsam ve Yetenekler

### 🖥️ Dashboard & İzleme
- Gerçek zamanlı ekipman nokta değerleri (Point Values) ve simüle edilmiş trend takipleri.
- Yerel proje, site, zon ve ekipman hiyerarşisi oluşturma/listeleme işlemleri.

### 🔌 Genişletilebilir Adaptör Mimarisi (`BaseAdapter`)
- **PointValue Standardizasyonu:** Her veri noktası `value`, `timestamp`, `quality` ("good", "uncertain", "bad") ve `unit` şemasıyla taşınır.
- **Simülatör Adaptörü:** Test senaryoları için dinamik dalgalanma üreten hafıza tabanlı okuma/yazma desteği.
- **Modbus TCP Adaptörü:** `pymodbus` tabanlı asenkron holding/input register ve coil/discrete input operasyonları.
- **Modbus RTU Adaptörü:** Seri port (RS-485) tabanlı saha elemanları için optimize edilmiş asenkron bağlantı desteği.

### 🎛️ Kontrol ve Yazma (Write) Operasyonları
- `routers/control.py` rotası üzerinden sahaya veya simülatöre doğrudan müdahale kabiliyeti.
- BACnet standartlarıyla uyumlu **Priority (Öncelik Seviyesi - Default: 8)** mekanizması desteği.

## 🗺️ Gelecek Planlaması (Roadmap)

- [ ] **BACnet/IP Adaptörü:** `bacpypes` tabanlı priority array uyumlu nesne kontrolü.
- [ ] **MQTT & Home Assistant Entegrasyonu:** IoT tabanlı edge cihazlar için broker bağlantısı.
- [ ] **Sequence Execution Engine:** Koşullu mantık (IF/THEN) ve zaman tabanlı senaryo (Scheduling) çalıştırma motoru.
- [ ] **Gelişmiş Alarm Yönetimi:** Kritik eşik aşımlarında anlık durum loglama ve WebSocket güncellemeleri.
