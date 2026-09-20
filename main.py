import os
import sqlite3
from datetime import datetime, timezone
from typing import Optional
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Kayal Smart Watering System", version="2.6.0")

# Enable CORS for flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static directory for optional local assets
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

DB_FILE = os.environ.get("DATABASE_PATH", "watering_system.db")

# Background Image URL from Environment Variable (or optional local file)
CUSTOM_BG_URL = os.environ.get("BACKGROUND_IMAGE_URL", "")
if not CUSTOM_BG_URL and os.path.exists(os.path.join(STATIC_DIR, "we_bg.jpg")):
    CUSTOM_BG_URL = "/static/we_bg.jpg"

# -----------------------------
# Database Setup
# -----------------------------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS moisture_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moisture INTEGER NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS watering_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            duration INTEGER NOT NULL,
            triggered_by TEXT DEFAULT 'manual',
            timestamp TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -----------------------------
# In-Memory Command State
# -----------------------------
water_command = {
    "water": False,
    "duration": 3,
    "stop_pump": False,
    "requested_at": None
}

# -----------------------------
# Data Models
# -----------------------------
class SensorData(BaseModel):
    moisture: int

class WaterNowRequest(BaseModel):
    duration: Optional[int] = 3

class WateringData(BaseModel):
    duration: int
    triggered_by: Optional[str] = "esp32"

# -----------------------------
# Web Dashboard HTML
# -----------------------------
def get_dashboard_html(bg_url: str) -> str:
    bg_css_val = f"url('{bg_url}')" if bg_url else "none"
    bg_gradient_val = "linear-gradient(180deg, rgba(11, 19, 43, 0.85) 0%, rgba(15, 23, 42, 0.95) 100%)" if bg_url else "radial-gradient(at 10% 10%, rgba(236, 72, 153, 0.2) 0px, transparent 40%), radial-gradient(at 90% 90%, rgba(6, 182, 212, 0.2) 0px, transparent 40%)"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Kayal 🌹 - Our Baby Plant Care System</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-primary: #0b132b;
            --bg-secondary: #1c2541;
            --bg-card: rgba(15, 23, 42, 0.78);
            --accent-green: #10b981;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-pink: #ec4899;
            --accent-rose: #f43f5e;
            --accent-red: #ef4444;
            --accent-warning: #f59e0b;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --border: rgba(255, 255, 255, 0.12);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Outfit', sans-serif;
            -webkit-tap-highlight-color: transparent;
        }}

        body {{
            background-color: var(--bg-primary);
            background-image: {bg_gradient_val}, {bg_css_val};
            background-attachment: fixed;
            background-size: cover;
            background-position: center;
            color: var(--text-primary);
            min-height: 100vh;
            padding: 1.5rem 1rem;
            overflow-x: hidden;
            transition: background 0.8s ease;
        }}

        body.watering-love-bg {{
            background-image: 
                radial-gradient(circle at center, rgba(236, 72, 153, 0.35) 0%, rgba(15, 23, 42, 0.88) 100%),
                {bg_css_val};
        }}

        .container {{
            max-width: 1240px;
            margin: 0 auto;
        }}

        header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.75rem;
            padding-bottom: 1.25rem;
            border-bottom: 1px solid var(--border);
            gap: 1rem;
            background: rgba(15, 23, 42, 0.55);
            backdrop-filter: blur(12px);
            padding: 1rem 1.25rem;
            border-radius: 1.25rem;
        }}

        .logo-section {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .logo-icon {{
            font-size: 2.2rem;
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-rose));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            filter: drop-shadow(0 0 12px rgba(236, 72, 153, 0.6));
            animation: pulse-rose 3s infinite ease-in-out;
        }}

        @keyframes pulse-rose {{
            0%, 100% {{ transform: scale(1); }}
            50% {{ transform: scale(1.08); }}
        }}

        h1 {{
            font-size: 1.75rem;
            font-weight: 700;
            background: linear-gradient(to right, #ffffff, #f472b6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            line-height: 1.2;
        }}

        .subtitle {{
            font-size: 0.85rem;
            color: #cbd5e1;
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.4rem 1rem;
            border-radius: 9999px;
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.4);
            color: var(--accent-green);
            font-size: 0.85rem;
            font-weight: 500;
            white-space: nowrap;
        }}

        .pulse-dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background-color: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }}
            70% {{ transform: scale(1); box-shadow: 0 0 0 8px rgba(16, 185, 129, 0); }}
            100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }}
        }}

        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 1.25rem;
            margin-bottom: 1.75rem;
        }}

        .card {{
            background: var(--bg-card);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid var(--border);
            border-radius: 1.25rem;
            padding: 1.35rem;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.45);
            transition: transform 0.25s ease, border-color 0.25s ease;
        }}

        .card:hover {{
            border-color: rgba(236, 72, 153, 0.4);
            transform: translateY(-2px);
        }}

        .card-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #cbd5e1;
            font-size: 0.85rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            margin-bottom: 0.85rem;
        }}

        .card-value {{
            font-size: 2.35rem;
            font-weight: 700;
            margin-bottom: 0.4rem;
            display: flex;
            align-items: baseline;
            gap: 0.5rem;
            flex-wrap: wrap;
        }}

        .card-unit {{
            font-size: 1.05rem;
            color: var(--accent-green);
            font-weight: 500;
        }}

        .card-footer {{
            font-size: 0.82rem;
            color: #94a3b8;
        }}

        .button-group {{
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }}

        .water-btn {{
            width: 100%;
            padding: 0.95rem 1rem;
            border: none;
            border-radius: 0.85rem;
            color: white;
            font-size: 0.95rem;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.6rem;
            transition: all 0.25s ease;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }}

        .btn-blue {{
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-cyan));
            box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
        }}

        .btn-blue:hover, .btn-blue:active {{
            background: linear-gradient(135deg, #db2777, #0891b2);
            box-shadow: 0 6px 24px rgba(236, 72, 153, 0.6);
            transform: translateY(-2px);
        }}

        .btn-red {{
            background: linear-gradient(135deg, #ef4444, #b91c1c);
            box-shadow: 0 4px 15px rgba(239, 68, 68, 0.4);
            border: 1px solid rgba(239, 68, 68, 0.5);
        }}

        .btn-red:hover, .btn-red:active {{
            background: linear-gradient(135deg, #dc2626, #991b1b);
            box-shadow: 0 6px 22px rgba(239, 68, 68, 0.65);
            transform: translateY(-2px);
        }}

        .btn-stop {{
            background: linear-gradient(135deg, #dc2626, #7f1d1d);
            box-shadow: 0 0 20px rgba(239, 68, 68, 0.7);
            border: 2px solid #f87171;
            animation: pulse-red 1.5s infinite;
        }}

        @keyframes pulse-red {{
            0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
            70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
            100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}

        .chart-container {{
            grid-column: 1 / -1;
            height: 380px;
            position: relative;
        }}

        .chart-header-container {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}

        .chart-header-stats {{
            display: flex;
            gap: 0.5rem;
            align-items: center;
            font-size: 0.8rem;
            color: #cbd5e1;
            flex-wrap: wrap;
        }}

        .stat-pill {{
            background: rgba(255, 255, 255, 0.08);
            padding: 0.25rem 0.65rem;
            border-radius: 9999px;
            border: 1px solid var(--border);
        }}

        .table-container {{
            grid-column: 1 / -1;
            overflow-x: auto;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 0.88rem;
        }}

        th {{
            color: #cbd5e1;
            padding: 0.75rem 0.85rem;
            border-bottom: 1px solid var(--border);
            font-weight: 600;
            white-space: nowrap;
        }}

        td {{
            padding: 0.85rem;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            white-space: nowrap;
        }}

        tr:hover td {{
            background: rgba(255, 255, 255, 0.04);
        }}

        .moisture-bar-bg {{
            width: 100%;
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            margin-top: 0.75rem;
        }}

        .moisture-bar-fill {{
            height: 100%;
            background: linear-gradient(90deg, var(--accent-warning), var(--accent-pink), var(--accent-cyan));
            width: 0%;
            transition: width 0.5s ease;
        }}

        .toast {{
            position: fixed;
            bottom: 2rem;
            left: 50%;
            transform: translateX(-50%);
            padding: 0.9rem 1.6rem;
            border-radius: 1rem;
            background: rgba(15, 23, 42, 0.95);
            backdrop-filter: blur(16px);
            border: 1px solid rgba(236, 72, 153, 0.5);
            color: var(--text-primary);
            box-shadow: 0 10px 35px rgba(236, 72, 153, 0.4);
            display: none;
            z-index: 1000;
            font-weight: 600;
            text-align: center;
            max-width: 90vw;
        }}

        /* Floating Love Particles Layer */
        .love-container {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            pointer-events: none;
            z-index: 999;
            overflow: hidden;
        }}

        .floating-heart {{
            position: absolute;
            bottom: -50px;
            font-size: 2.2rem;
            animation: floatUp 3.5s cubic-bezier(0.25, 0.46, 0.45, 0.94) forwards;
            filter: drop-shadow(0 0 12px rgba(236, 72, 153, 0.8));
            opacity: 1;
        }}

        @keyframes floatUp {{
            0% {{
                transform: translateY(0) scale(0.4) rotate(0deg);
                opacity: 1;
            }}
            50% {{
                opacity: 0.9;
                transform: translateY(-50vh) scale(1.3) rotate(180deg);
            }}
            100% {{
                transform: translateY(-110vh) scale(0.8) rotate(360deg);
                opacity: 0;
            }}
        }}

        /* Mobile Responsive */
        @media (max-width: 640px) {{
            body {{ padding: 1rem 0.6rem; }}
            header {{ flex-direction: column; align-items: flex-start; gap: 0.75rem; }}
            .status-badge {{ align-self: flex-start; }}
            h1 {{ font-size: 1.45rem; }}
            .logo-icon {{ font-size: 1.8rem; }}
            .card {{ padding: 1.1rem; border-radius: 1rem; }}
            .card-value {{ font-size: 2rem; }}
            .water-btn {{ font-size: 0.88rem; padding: 0.85rem 0.65rem; }}
            .chart-container {{ height: 320px; }}
            .chart-header-stats {{ gap: 0.35rem; font-size: 0.75rem; }}
            .stat-pill {{ padding: 0.2rem 0.5rem; }}
        }}
    </style>
</head>
<body>
    <!-- Floating Love Particles Layer -->
    <div class="love-container" id="love-layer"></div>

    <div class="container">
        <header>
            <div class="logo-section">
                <span class="logo-icon">🌹</span>
                <div>
                    <h1>Kayal 🌹</h1>
                    <p class="subtitle">Our Baby Rose Care System • Made with Love 💕</p>
                </div>
            </div>
            <div class="status-badge" id="sys-status">
                <div class="pulse-dot"></div>
                <span>Kayal Connected</span>
            </div>
        </header>

        <div class="grid">
            <!-- Soil Moisture Card -->
            <div class="card">
                <div class="card-header">
                    <span>KAYAL'S SOIL MOISTURE</span>
                    <span>🌱</span>
                </div>
                <div class="card-value">
                    <span id="moisture-val">--</span>
                    <span class="card-unit" id="moisture-status-text">Reading...</span>
                </div>
                <div class="moisture-bar-bg">
                    <div class="moisture-bar-fill" id="moisture-bar"></div>
                </div>
                <div class="card-footer" style="margin-top: 0.75rem;">
                    Last updated: <span id="last-sensor-time">Never</span>
                </div>
            </div>

            <!-- Last Watered Card -->
            <div class="card">
                <div class="card-header">
                    <span>LAST FED WITH WATER</span>
                    <span>🍼</span>
                </div>
                <div class="card-value" style="font-size: 1.65rem;" id="last-watered-val">
                    Never
                </div>
                <div class="card-footer" id="last-watered-detail">
                    Kayal hasn't drank water yet
                </div>
            </div>

            <!-- Quick Action Card -->
            <div class="card" style="display: flex; flex-direction: column; justify-content: space-between;">
                <div class="card-header">
                    <span>FEED KAYAL WITH LOVE 💕</span>
                    <span>⚡</span>
                </div>
                <div class="button-group" id="action-btn-container">
                    <button class="water-btn btn-blue" id="water-btn" onclick="triggerWatering(3)">
                        <span>💧</span> FEED KAYAL (3s)
                    </button>
                    <button class="water-btn btn-red" id="water-unlimited-btn" onclick="triggerWatering(60)">
                        <span>🚨</span> WATER INFINITELY (Max 1 Min)
                    </button>
                    <button class="water-btn btn-stop" id="stop-btn" onclick="stopWatering()" style="display: none;">
                        <span>🛑</span> STOP WATERING NOW
                    </button>
                </div>
                <div class="card-footer" id="pump-cmd-status" style="text-align: center; margin-top: 0.5rem;">
                    Ready to feed Kayal 🌹
                </div>
            </div>
        </div>

        <!-- Moisture Graph -->
        <div class="grid">
            <div class="card chart-container">
                <div class="chart-header-container">
                    <div class="card-header" style="margin:0;">
                        <span>KAYAL'S MOISTURE & WATERING HISTORY</span>
                    </div>
                    <div class="chart-header-stats">
                        <span class="stat-pill">Avg: <strong id="stat-avg">--</strong></span>
                        <span class="stat-pill">Min: <strong id="stat-min">--</strong></span>
                        <span class="stat-pill">Max: <strong id="stat-max">--</strong></span>
                    </div>
                </div>
                <canvas id="moistureChart"></canvas>
            </div>
        </div>

        <!-- Recent Logs Table -->
        <div class="grid">
            <div class="card table-container">
                <div class="card-header">
                    <span>KAYAL'S FEEDING LOGS</span>
                    <span>📜</span>
                </div>
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Timestamp</th>
                            <th>Duration (Sec)</th>
                            <th>Triggered By</th>
                        </tr>
                    </thead>
                    <tbody id="logs-table-body">
                        <tr><td colspan="4" style="text-align:center; color: var(--text-secondary);">No feeding logs yet</td></tr>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <div class="toast" id="toast">Feeding Kayal with love! 💋💕</div>

    <script>
        let moistureChart = null;

        function initChart() {{
            const ctx = document.getElementById('moistureChart').getContext('2d');
            
            const gradient = ctx.createLinearGradient(0, 0, 0, 300);
            gradient.addColorStop(0, 'rgba(236, 72, 153, 0.45)');
            gradient.addColorStop(0.6, 'rgba(6, 182, 212, 0.15)');
            gradient.addColorStop(1, 'rgba(15, 23, 42, 0.0)');

            moistureChart = new Chart(ctx, {{
                type: 'line',
                data: {{
                    labels: [],
                    datasets: [
                        {{
                            label: 'Soil Moisture',
                            data: [],
                            borderColor: '#ec4899',
                            borderWidth: 3,
                            backgroundColor: gradient,
                            fill: true,
                            tension: 0.4,
                            pointBackgroundColor: '#ec4899',
                            pointBorderColor: '#ffffff',
                            pointBorderWidth: 1.5,
                            pointRadius: 4,
                            pointHoverRadius: 8,
                            pointHoverBackgroundColor: '#06b6d4',
                            pointHoverBorderColor: '#ffffff'
                        }}
                    ]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {{ mode: 'index', intersect: false }},
                    scales: {{
                        x: {{
                            grid: {{ color: 'rgba(255, 255, 255, 0.04)', drawBorder: false }},
                            ticks: {{ 
                                color: '#94a3b8',
                                font: {{ family: "'Outfit', sans-serif", size: 10 }},
                                maxTicksLimit: 8,
                                maxRotation: 0,
                                autoSkip: true
                            }}
                        }},
                        y: {{
                            grid: {{ color: 'rgba(255, 255, 255, 0.04)', drawBorder: false }},
                            ticks: {{ 
                                color: '#94a3b8',
                                font: {{ family: "'Outfit', sans-serif", size: 10 }}
                            }},
                            beginAtZero: false
                        }}
                    }},
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: 'rgba(28, 37, 65, 0.95)',
                            titleColor: '#f8fafc',
                            bodyColor: '#ec4899',
                            titleFont: {{ family: "'Outfit', sans-serif", size: 12, weight: 'bold' }},
                            bodyFont: {{ family: "'Outfit', sans-serif", size: 13, weight: 'bold' }},
                            borderColor: 'rgba(236, 72, 153, 0.4)',
                            borderWidth: 1,
                            padding: 10,
                            displayColors: false,
                            callbacks: {{
                                label: function(context) {{ return 'Moisture: ' + context.parsed.y; }}
                            }}
                        }}
                    }}
                }}
            }});
        }}

        // Spawn Magical Floating Kisses & Hearts Particles
        function spawnLoveBurst() {{
            const container = document.getElementById('love-layer');
            const icons = ['💋', '💕', '🌹', '✨', '💖', '🥰', '💧', '🌺', '💌'];
            
            document.body.classList.add('watering-love-bg');
            setTimeout(() => {{
                document.body.classList.remove('watering-love-bg');
            }}, 4000);

            for (let i = 0; i < 35; i++) {{
                setTimeout(() => {{
                    const el = document.createElement('div');
                    el.className = 'floating-heart';
                    el.innerText = icons[Math.floor(Math.random() * icons.length)];
                    el.style.left = Math.random() * 95 + 'vw';
                    el.style.fontSize = (1.5 + Math.random() * 1.8) + 'rem';
                    el.style.animationDuration = (2.2 + Math.random() * 1.6) + 's';
                    container.appendChild(el);

                    setTimeout(() => {{ el.remove(); }}, 3600);
                }}, i * 90);
            }}
        }}

        async function triggerWatering(durationSeconds = 3) {{
            const isUnlimited = durationSeconds > 10;
            
            spawnLoveBurst();

            try {{
                const res = await fetch('/water-now', {{ 
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ duration: durationSeconds }})
                }});
                const data = await res.json();
                
                showToast(isUnlimited ? '💋 Feeding Kayal infinitely! 💕 (Max 1 min)' : '💋 Feeding Kayal with love & water! 🌹');
                
                // Show STOP button
                document.getElementById('stop-btn').style.display = 'flex';
                document.getElementById('water-btn').style.display = 'none';
                document.getElementById('water-unlimited-btn').style.display = 'none';
                document.getElementById('pump-cmd-status').innerText = isUnlimited ? 'Kayal is drinking water... Click STOP anytime!' : `Feeding Kayal (${{durationSeconds}}s)...`;

            }} catch (err) {{
                showToast('❌ Failed to send command');
            }}
        }}

        async function stopWatering() {{
            try {{
                const res = await fetch('/stop-watering', {{ method: 'POST' }});
                const data = await res.json();
                showToast('🛑 Stopped feeding Kayal.');
                
                document.getElementById('stop-btn').style.display = 'none';
                document.getElementById('water-btn').style.display = 'flex';
                document.getElementById('water-unlimited-btn').style.display = 'flex';
                document.getElementById('pump-cmd-status').innerText = 'Ready to feed Kayal 🌹';
            }} catch (err) {{
                showToast('❌ Failed to send stop command');
            }}
        }}

        function showToast(msg) {{
            const toast = document.getElementById('toast');
            toast.innerText = msg;
            toast.style.display = 'block';
            setTimeout(() => {{ toast.style.display = 'none'; }}, 3500);
        }}

        function formatRelativeTime(isoString) {{
            if (!isoString) return 'Never';
            const date = new Date(isoString);
            const now = new Date();
            const diffSec = Math.floor((now - date) / 1000);

            if (diffSec < 60) return `${{diffSec}} seconds ago`;
            if (diffSec < 3600) return `${{Math.floor(diffSec / 60)}} mins ago`;
            if (diffSec < 86400) return `${{Math.floor(diffSec / 3600)}} hours ago`;
            return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}});
        }}

        async function fetchStatus() {{
            try {{
                const res = await fetch('/api/status');
                const data = await res.json();

                if (data.moisture !== null && data.moisture !== undefined) {{
                    document.getElementById('moisture-val').innerText = data.moisture;
                    
                    let percent = Math.min(100, Math.max(0, Math.round((data.moisture / 4095) * 100)));
                    document.getElementById('moisture-bar').style.width = percent + '%';

                    let statusStr = "Optimal";
                    if (data.moisture < 1200) statusStr = "Thirsty 🏜️";
                    else if (data.moisture > 2800) statusStr = "Very Happy 💧";
                    else statusStr = "Healthy & Good 🌿";

                    document.getElementById('moisture-status-text').innerText = statusStr;
                }}

                if (data.last_sensor_timestamp) {{
                    document.getElementById('last-sensor-time').innerText = formatRelativeTime(data.last_sensor_timestamp);
                }}

                if (data.last_watered) {{
                    document.getElementById('last-watered-val').innerText = formatRelativeTime(data.last_watered);
                    document.getElementById('last-watered-detail').innerText = `${{new Date(data.last_watered).toLocaleTimeString([], {{hour: '2-digit', minute:'2-digit'}})}} (${{data.last_watered_duration || 3}}s)`;
                }}

                const stopBtn = document.getElementById('stop-btn');
                const waterBtn = document.getElementById('water-btn');
                const waterUnlBtn = document.getElementById('water-unlimited-btn');
                const cmdStatus = document.getElementById('pump-cmd-status');
                
                if (data.water_queued) {{
                    stopBtn.style.display = 'flex';
                    waterBtn.style.display = 'none';
                    waterUnlBtn.style.display = 'none';
                    cmdStatus.innerText = 'Kayal is drinking water... Click STOP to end.';
                }} else {{
                    stopBtn.style.display = 'none';
                    waterBtn.style.display = 'flex';
                    waterUnlBtn.style.display = 'flex';
                    cmdStatus.innerText = 'Ready to feed Kayal 🌹';
                }}

            }} catch (err) {{
                console.error("Error fetching status:", err);
            }}
        }}

        async function fetchHistory() {{
            try {{
                const res = await fetch('/api/history');
                const data = await res.json();

                if (moistureChart && data.moisture && data.moisture.length > 0) {{
                    const labels = data.moisture.map(item => {{
                        const d = new Date(item.timestamp);
                        return d.toLocaleTimeString([], {{ hour: '2-digit', minute: '2-digit', second: '2-digit' }});
                    }});
                    const values = data.moisture.map(item => item.moisture);

                    const sum = values.reduce((a, b) => a + b, 0);
                    const avg = Math.round(sum / values.length);
                    const min = Math.min(...values);
                    const max = Math.max(...values);

                    document.getElementById('stat-avg').innerText = avg;
                    document.getElementById('stat-min').innerText = min;
                    document.getElementById('stat-max').innerText = max;

                    const rangeMargin = Math.max(10, Math.round((max - min) * 0.2));
                    moistureChart.options.scales.y.suggestedMin = Math.max(0, min - rangeMargin);
                    moistureChart.options.scales.y.suggestedMax = max + rangeMargin;

                    moistureChart.data.labels = labels;
                    moistureChart.data.datasets[0].data = values;
                    moistureChart.update();
                }}

                const tbody = document.getElementById('logs-table-body');
                if (data.waterings && data.waterings.length > 0) {{
                    tbody.innerHTML = data.waterings.map(log => `
                        <tr>
                            <td>#${{log.id}}</td>
                            <td>${{new Date(log.timestamp).toLocaleString()}}</td>
                            <td><strong style="color: ${{log.duration > 10 ? 'var(--accent-red)' : 'var(--accent-pink)'}};">${{log.duration}}s</strong></td>
                            <td><span style="color: var(--accent-cyan); font-weight: 500;">${{log.triggered_by || 'manual'}}</span></td>
                        </tr>
                    `).join('');
                }}
            }} catch (err) {{
                console.error("Error fetching history:", err);
            }}
        }}

        window.addEventListener('DOMContentLoaded', () => {{
            initChart();
            fetchStatus();
            fetchHistory();
            setInterval(fetchStatus, 3000);
            setInterval(fetchHistory, 10000);
        }});
    </script>
</body>
</html>
"""

# -----------------------------
# Endpoints
# -----------------------------

@app.get("/", response_class=HTMLResponse)
def home():
    """Serves the interactive web UI dashboard."""
    return HTMLResponse(content=get_dashboard_html(CUSTOM_BG_URL), status_code=200)


@app.post("/sensor-data")
def receive_sensor_data(data: SensorData):
    """Receives soil moisture reading from ESP32 and stores in database."""
    now_iso = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO moisture_logs (moisture, timestamp) VALUES (?, ?)",
        (data.moisture, now_iso)
    )
    conn.commit()
    conn.close()

    return {
        "status": "received",
        "moisture": data.moisture,
        "timestamp": now_iso
    }


@app.get("/pump-command")
def pump_command():
    """ESP32 calls this endpoint to check if watering command or stop command is queued."""
    return {
        "water": water_command["water"],
        "duration": water_command["duration"],
        "stop_pump": water_command["stop_pump"]
    }


@app.post("/water-now")
def water_now(req: Optional[WaterNowRequest] = None):
    """Web UI calls this endpoint to queue a watering action."""
    duration = 3
    if req and req.duration:
        duration = min(60, max(1, req.duration)) # Cap at 60 seconds maximum safety cutoff

    water_command["water"] = True
    water_command["duration"] = duration
    water_command["stop_pump"] = False
    water_command["requested_at"] = datetime.now(timezone.utc).isoformat()

    return {
        "status": "water command sent",
        "duration": duration
    }


@app.post("/stop-watering")
def stop_watering():
    """Web UI calls this endpoint to immediately abort pump watering."""
    water_command["water"] = False
    water_command["stop_pump"] = True
    water_command["requested_at"] = None

    return {
        "status": "pump stop command sent"
    }


@app.post("/watering")
def watering(data: WateringData):
    """ESP32 calls this endpoint to report completed watering."""
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Reset water command flag
    water_command["water"] = False
    water_command["duration"] = 3
    water_command["stop_pump"] = False
    water_command["requested_at"] = None

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO watering_logs (duration, triggered_by, timestamp) VALUES (?, ?, ?)",
        (data.duration, data.triggered_by, now_iso)
    )
    conn.commit()
    conn.close()

    return {
        "status": "watering recorded",
        "duration": data.duration,
        "timestamp": now_iso
    }


@app.get("/plant-status")
@app.get("/api/status")
def get_plant_status():
    """Returns current status summary for web dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    # Get latest moisture
    cursor.execute("SELECT moisture, timestamp FROM moisture_logs ORDER BY id DESC LIMIT 1")
    latest_moisture_row = cursor.fetchone()

    # Get last watered
    cursor.execute("SELECT timestamp, duration FROM watering_logs ORDER BY id DESC LIMIT 1")
    last_watered_row = cursor.fetchone()

    conn.close()

    return {
        "moisture": latest_moisture_row["moisture"] if latest_moisture_row else None,
        "last_sensor_timestamp": latest_moisture_row["timestamp"] if latest_moisture_row else None,
        "last_watered": last_watered_row["timestamp"] if last_watered_row else None,
        "last_watered_duration": last_watered_row["duration"] if last_watered_row else None,
        "water_queued": water_command["water"],
        "water_duration": water_command["duration"]
    }


@app.get("/api/history")
def get_history(limit: int = 50):
    """Returns moisture & watering historical data for charts."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id, moisture, timestamp FROM moisture_logs ORDER BY id DESC LIMIT ?", (limit,))
    moisture_rows = cursor.fetchall()

    cursor.execute("SELECT id, duration, triggered_by, timestamp FROM watering_logs ORDER BY id DESC LIMIT ?", (limit,))
    watering_rows = cursor.fetchall()

    conn.close()

    # Reverse to return chronological order for charts
    moisture_data = [dict(row) for row in reversed(moisture_rows)]
    watering_data = [dict(row) for row in reversed(watering_rows)]

    return {
        "moisture": moisture_data,
        "waterings": watering_data
    }