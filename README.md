# 🌹 Baby Rose - Smart Water System ("Water Online")

A cloud-hosted IoT Plant Watering & Moisture Tracking System built with **FastAPI**, **SQLite**, **Chart.js**, and **ESP32**. Designed for effortless deployment on [Railway](https://railway.app/).

---

## 🌟 Features

- 💧 **Remote Water Control**: Click **WATER NOW** from anywhere in the world to trigger your ESP32 pump relay.
- 📊 **Moisture Trend Graph**: Real-time line graph plotting soil moisture levels over time using Chart.js.
- 📜 **Watering Logs & Database**: SQLite database tracking timestamped moisture levels and watering history.
- ⚡ **Real-time Status Sync**: Visual gauge showing soil status (Dry, Optimal, Moist) and relative time of last watering.
- ☁️ **Railway Cloud Ready**: Deploy in minutes with included `Procfile` and `railway.json`.

---

## 🚀 How to Deploy on Railway

1. **Push to GitHub**:
   This repository is configured with Git pointing to `https://github.com/oorkuruvitube-spec/Kayal.git`.

2. **Deploy via Railway Dashboard**:
   - Go to [Railway.app](https://railway.app/) and sign in with GitHub.
   - Click **New Project** -> **Deploy from GitHub repo**.
   - Select the `Kayal` repository.
   - Railway will automatically detect Python, install dependencies from `requirements.txt`, and start the app using `Procfile`.

3. **Get your Public URL**:
   - In your Railway service settings, go to **Networking** -> **Generate Domain**.
   - Your site will be hosted at `https://<your-app-name>.up.railway.app`.

---

## 📟 ESP32 Configuration

1. Open `esp32/esp32_water_system.ino` in Arduino IDE.
2. Update the Wi-Fi credentials:
   ```cpp
   const char* ssid     = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
3. Update `serverDomain` to match your Railway domain:
   ```cpp
   const char* serverDomain = "https://<your-app-name>.up.railway.app";
   ```
4. Flash the code onto your ESP32 board.

---

## 🛠️ Hardware Connections

| Component | Pin on ESP32 |
|---|---|
| Soil Moisture Sensor (Analog Out) | `GPIO 32` |
| 5V Relay Module (Control Signal) | `GPIO 25` |

---

## 🧪 Local Testing

To test locally before deploying:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Access the dashboard at `http://localhost:8000`.
