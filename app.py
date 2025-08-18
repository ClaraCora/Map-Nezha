
import os
import json as _json
import time
import base64
import logging
import threading
import ssl
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory, make_response, Response
from flask_cors import CORS
import requests
import websocket

# -------- Fast JSON (optional orjson) --------
try:
    import orjson
    def dumps(obj) -> str:
        return orjson.dumps(obj).decode()
except Exception:
    def dumps(obj) -> str:
        return _json.dumps(obj, separators=(",", ":"))

# -------- Bootstrap --------
load_dotenv()
logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")

# -------- Config --------
NEZHA_DASHBOARD_URL = os.getenv("NEZHA_DASHBOARD_URL", "https://your-nezha-panel.com").rstrip("/")
NEZHA_USERNAME = os.getenv("NEZHA_USERNAME", "your_username")
NEZHA_PASSWORD = os.getenv("NEZHA_PASSWORD", "your_password")

NGINX_BASIC_AUTH_USER = os.getenv("NGINX_BASIC_AUTH_USER", "")
NGINX_BASIC_AUTH_PASS = os.getenv("NGINX_BASIC_AUTH_PASS", "")

REFRESH_SECONDS = float(os.getenv("REFRESH_SECONDS", "1.0"))  # target refresh
HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "8.0"))
INSECURE_TLS = os.getenv("NEZHA_INSECURE", "false").lower() in {"1", "true", "yes"}

# -------- Country maps --------
COUNTRY_CODE_TO_NAME_MAP = {
    "SG": "Singapore", "DE": "Germany", "KR": "South Korea", "JP": "Japan",
    "US": "United States of America", "CN": "China", "HK": "Hong Kong",
    "TW": "Taiwan", "GB": "United Kingdom", "FR": "France", "AU": "Australia",
    "CA": "Canada", "NL": "Netherlands", "IT": "Italy", "ES": "Spain",
    "RU": "Russia", "SE": "Sweden", "NO": "Norway", "DK": "Denmark",
    "FI": "Finland", "CH": "Switzerland", "AT": "Austria", "BE": "Belgium",
    "PL": "Poland", "CZ": "Czech Republic", "HU": "Hungary", "RO": "Romania",
    "BG": "Bulgaria", "HR": "Croatia", "SI": "Slovenia", "SK": "Slovakia",
    "LT": "Lithuania", "LV": "Latvia", "EE": "Estonia", "IE": "Ireland",
    "PT": "Portugal", "GR": "Greece", "TR": "Turkey", "UA": "Ukraine",
    "BY": "Belarus", "MD": "Moldova", "RS": "Serbia", "BA": "Bosnia and Herzegovina",
    "ME": "Montenegro", "MK": "North Macedonia", "AL": "Albania", "XK": "Kosovo",
    "GE": "Georgia", "AM": "Armenia", "AZ": "Azerbaijan", "KZ": "Kazakhstan",
    "UZ": "Uzbekistan", "KG": "Kyrgyzstan", "TJ": "Tajikistan", "TM": "Turkmenistan",
    "AF": "Afghanistan", "PK": "Pakistan", "BD": "Bangladesh", "LK": "Sri Lanka",
    "NP": "Nepal", "BT": "Bhutan", "MV": "Maldives", "MY": "Malaysia",
    "TH": "Thailand", "VN": "Vietnam", "LA": "Laos", "KH": "Cambodia",
    "MM": "Myanmar", "PH": "Philippines", "ID": "Indonesia", "BN": "Brunei",
    "TL": "East Timor", "PG": "Papua New Guinea", "FJ": "Fiji", "NC": "New Caledonia",
    "VU": "Vanuatu", "SB": "Solomon Islands", "KI": "Kiribati", "TO": "Tonga",
    "WS": "Samoa", "TV": "Tuvalu", "NR": "Nauru", "PW": "Palau",
    "MH": "Marshall Islands", "FM": "Micronesia", "CK": "Cook Islands",
    "NU": "Niue", "TK": "Tokelau", "AS": "American Samoa", "GU": "Guam",
    "MP": "Northern Mariana Islands",
    "IN": "India", "AR": "Argentina", "BR": "Brazil", "CO": "Colombia",
    "CL": "Chile", "SA": "Saudi Arabia", "EG": "Egypt",
}
COUNTRY_COORDS = {
    "Singapore": [103.82, 1.35], "Germany": [10.45, 51.17], "South Korea": [127.98, 35.91],
    "Japan": [138.25, 36.20], "United States of America": [-95.71, 37.09],
    "China": [104.19, 35.86], "Hong Kong": [114.17, 22.32], "Taiwan": [120.96, 23.69],
    "United Kingdom": [-3.43, 55.37], "France": [2.35, 48.86],
    "Australia": [133.77, -25.27], "Canada": [-106.34, 56.13], "Netherlands": [5.29, 52.13],
    "Italy": [12.57, 41.87], "Spain": [-3.75, 40.46], "Russia": [105.32, 61.52],
    "Sweden": [18.06, 60.13], "Norway": [8.47, 60.39], "Denmark": [9.50, 56.26],
    "Finland": [26.27, 64.50], "Switzerland": [8.23, 46.82], "Austria": [14.55, 47.70],
    "Belgium": [4.35, 50.85], "Poland": [19.15, 51.92], "Czech Republic": [15.47, 49.82],
    "Hungary": [19.50, 47.16], "Romania": [24.97, 45.94], "Bulgaria": [25.48, 42.73],
    "Croatia": [16.17, 45.10], "Slovenia": [14.82, 46.15], "Slovakia": [19.70, 48.67],
    "Lithuania": [23.88, 55.17], "Latvia": [24.60, 56.88], "Estonia": [25.59, 58.38],
    "Ireland": [-8.24, 53.41], "Portugal": [-8.22, 39.40], "Greece": [21.82, 39.08],
    "Turkey": [35.24, 38.96], "Ukraine": [31.17, 48.38], "Belarus": [28.03, 53.71],
    "Moldova": [28.37, 47.41], "Serbia": [21.01, 44.02], "Bosnia and Herzegovina": [17.68, 44.17],
    "Montenegro": [19.37, 42.71], "North Macedonia": [21.73, 41.61], "Albania": [20.17, 41.33],
    "Kosovo": [20.90, 42.60], "Georgia": [43.36, 42.32], "Armenia": [44.82, 40.07],
    "Azerbaijan": [47.58, 40.14], "Kazakhstan": [66.92, 48.02], "Uzbekistan": [64.42, 41.38],
    "Kyrgyzstan": [74.77, 41.20], "Tajikistan": [71.28, 38.54], "Turkmenistan": [59.39, 38.97],
    "Afghanistan": [67.71, 33.94], "Pakistan": [69.35, 30.38], "Bangladesh": [90.36, 23.68],
    "Sri Lanka": [80.77, 7.87], "Nepal": [84.12, 28.39], "Bhutan": [90.51, 27.51],
    "Maldives": [73.22, 3.20], "Malaysia": [101.69, 3.14], "Thailand": [100.99, 15.87],
    "Vietnam": [108.28, 14.06], "Laos": [102.50, 19.86], "Cambodia": [104.99, 12.57],
    "Myanmar": [96.13, 21.91], "Philippines": [121.77, 12.88], "Indonesia": [106.85, -6.21],
    "Brunei": [114.73, 4.54], "East Timor": [125.73, -8.87], "Papua New Guinea": [143.16, -6.32],
    "Fiji": [178.07, -17.71], "New Caledonia": [165.62, -20.90], "Vanuatu": [167.22, -15.38],
    "Solomon Islands": [160.20, -9.65], "Kiribati": [-157.36, 1.87], "Tonga": [-175.20, -21.14],
    "Samoa": [-172.10, -13.76], "Tuvalu": [178.12, -8.52], "Nauru": [166.92, -0.52],
    "Palau": [134.56, 7.51], "Marshall Islands": [168.73, 7.13], "Micronesia": [158.21, 6.92],
    "Cook Islands": [-159.78, -21.23], "Niue": [-169.87, -19.05], "Tokelau": [-171.85, -9.20],
    "American Samoa": [-170.70, -14.31], "Guam": [144.79, 13.44], "Northern Mariana Islands": [145.75, 15.21],
    "India": [78.9629, 20.5937], "Argentina": [-63.6167, -38.4161], "Brazil": [-51.9253, -14.2350],
    "Colombia": [-74.2973, 4.5709], "Chile": [-71.542969, -35.675147], "Saudi Arabia": [45.0792, 23.8859],
    "Egypt": [30.8025, 26.8206],
}
COUNTRY_EMOJI_CN_MAP = {
    "Singapore": "🇸🇬 新加坡","Germany": "🇩🇪 德国","South Korea": "🇰🇷 韩国","Japan": "🇯🇵 日本",
    "United States of America": "🇺🇸 美国","China": "🇨🇳 中国","Hong Kong": "🇭🇰 中国香港","Taiwan": "🇹🇼 中国台湾",
    "United Kingdom": "🇬🇧 英国","France": "🇫🇷 法国","Australia": "🇦🇺 澳大利亚","Canada": "🇨🇦 加拿大",
    "Netherlands": "🇳🇱 荷兰","Italy": "🇮🇹 意大利","Spain": "🇪🇸 西班牙","Russia": "🇷🇺 俄罗斯","Sweden": "🇸🇪 瑞典",
    "Norway": "🇳🇴 挪威","Denmark": "🇩🇰 丹麦","Finland": "🇫🇮 芬兰","Switzerland": "🇨🇭 瑞士","Austria": "🇦🇹 奥地利",
    "Belgium": "🇧🇪 比利时","Poland": "🇵🇱 波兰","Czech Republic": "🇨🇿 捷克","Hungary": "🇭🇺 匈牙利",
    "Romania": "🇷🇴 罗马尼亚","Bulgaria": "🇧🇬 保加利亚","Croatia": "🇭🇷 克罗地亚","Slovenia": "🇸🇮 斯洛文尼亚",
    "Slovakia": "🇸🇰 斯洛伐克","Lithuania": "🇱🇹 立陶宛","Latvia": "🇱🇻 拉脱维亚","Estonia": "🇪🇪 爱沙尼亚",
    "Ireland": "🇮🇪 爱尔兰","Portugal": "🇵🇹 葡萄牙","Greece": "🇬🇷 希腊","Turkey": "🇹🇷 土耳其","Ukraine": "🇺🇦 乌克兰",
    "Belarus": "🇧🇾 白俄罗斯","Moldova": "🇲🇩 摩尔多瓦","Serbia": "🇷🇸 塞尔维亚","Bosnia and Herzegovina": "🇧🇦 波黑",
    "Montenegro": "🇲🇪 黑山","North Macedonia": "🇲🇰 北马其顿","Albania": "🇦🇱 阿尔巴尼亚","Kosovo": "🇽🇰 科索沃",
    "Georgia": "🇬🇪 格鲁吉亚","Armenia": "🇦🇲 亚美尼亚","Azerbaijan": "🇦🇿 阿塞拜疆","Kazakhstan": "🇰🇿 哈萨克斯坦",
    "Uzbekistan": "🇺🇿 乌兹别克斯坦","Kyrgyzstan": "🇰🇬 吉尔吉斯斯坦","Tajikistan": "🇹🇯 塔吉克斯坦","Turkmenistan": "🇹🇲 土库曼斯坦",
    "Afghanistan": "🇦🇫 阿富汗","Pakistan": "🇵🇰 巴基斯坦","Bangladesh": "🇧🇩 孟加拉国","Sri Lanka": "🇱🇰 斯里兰卡",
    "Nepal": "🇳🇵 尼泊尔","Bhutan": "🇧🇹 不丹","Maldives": "🇲🇻 马尔代夫","Malaysia": "🇲🇾 马来西亚","Thailand": "🇹🇭 泰国",
    "Vietnam": "🇻🇳 越南","Laos": "🇱🇦 老挝","Cambodia": "🇰🇭 柬埔寨","Myanmar": "🇲🇲 缅甸","Philippines": "🇵🇭 菲律宾",
    "Indonesia": "🇮🇩 印度尼西亚","Brunei": "🇧🇳 文莱","East Timor": "🇹🇱 东帝汶","Papua New Guinea": "🇵🇬 巴布亚新几内亚",
    "Fiji": "🇫🇯 斐济","New Caledonia": "🇳🇨 新喀里多尼亚","Vanuatu": "🇻🇺 瓦努阿图","Solomon Islands": "🇸🇧 所罗门群岛",
    "Kiribati": "🇰🇮 基里巴斯","Tonga": "🇹🇴 汤加","Samoa": "🇼🇸 萨摩亚","Tuvalu": "🇹🇻 图瓦卢","Nauru": "🇳🇷 瑙鲁",
    "Palau": "🇵🇼 帕劳","Marshall Islands": "🇲🇭 马绍尔群岛","Micronesia": "🇫🇲 密克罗尼西亚","Cook Islands": "🇨🇰 库克群岛",
    "Niue": "🇳🇺 纽埃","Tokelau": "🇹🇰 托克劳","American Samoa": "🇦🇸 美属萨摩亚","Guam": "🇬🇺 关岛",
    "Northern Mariana Islands": "🇲🇵 北马里亚纳群岛","India": "🇮🇳 印度","Argentina": "🇦🇷 阿根廷","Brazil": "🇧🇷 巴西",
    "Colombia": "🇨🇴 哥伦比亚","Chile": "🇨🇱 智利","Saudi Arabia": "🇸🇦 沙特阿拉伯","Egypt": "🇪🇬 埃及",
}

# -------- Utilities --------
def aggregate_servers_to_countries(servers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    countries_data: Dict[str, Dict[str, Any]] = {}
    for server in servers or []:
        host_info = (server.get("host") or server.get("Host") or {}) or {}
        status_info = (server.get("state") or server.get("State") or server.get("status") or {}) or {}

        code = (host_info.get("CountryCode") or server.get("country_code") or "")
        code = str(code).upper()
        if not code:
            continue

        name_en = COUNTRY_CODE_TO_NAME_MAP.get(code)
        if not name_en:
            continue

        if name_en not in countries_data:
            coords = COUNTRY_COORDS.get(name_en, [0, 0])
            countries_data[name_en] = {"uplinkSpeed": 0, "downlinkSpeed": 0, "coords": coords}

        net_out = status_info.get("net_out_speed", 0) or 0
        net_in = status_info.get("net_in_speed", 0) or 0
        countries_data[name_en]["uplinkSpeed"] += net_out
        countries_data[name_en]["downlinkSpeed"] += net_in

    output = []
    for name, d in countries_data.items():
        output.append({
            "countryNameEN": name,
            "countryNameEmojiCN": COUNTRY_EMOJI_CN_MAP.get(name, f"🌐 {name}"),
            "uplinkSpeed": round((d["uplinkSpeed"] * 8) / 1e6, 2),
            "downlinkSpeed": round((d["downlinkSpeed"] * 8) / 1e6, 2),
            "coords": d["coords"],
        })
    return output


class NezhaStreamer:
    """
    Persistent session + websocket to Nezha.
    Event-driven aggregation with <= 1s ceiling.
    Exposes hot JSON snapshot for HTTP handlers.
    """

    def __init__(self) -> None:
        self._session = requests.Session()
        self._need_basic = False
        self._jwt_cookie_name = "nz-jwt"
        self._last_servers: List[Dict[str, Any]] = []
        self._last_msg_ts: float = 0.0

        self._cache_json: str = "[]"
        self._cache_built_at: float = 0.0

        self._lock = threading.RLock()
        self._stop = threading.Event()

        # event-driven tick
        self._tick = threading.Event()
        self._dirty = False

        self._ws_thread: Optional[threading.Thread] = None
        self._agg_thread: Optional[threading.Thread] = None

    # ---------- Public ----------
    def start(self) -> None:
        if not (self._ws_thread and self._ws_thread.is_alive()):
            self._stop.clear()
            self._ws_thread = threading.Thread(target=self._ws_loop, name="NezhaWS", daemon=True)
            self._ws_thread.start()

        if not (self._agg_thread and self._agg_thread.is_alive()):
            self._agg_thread = threading.Thread(target=self._aggregate_loop, name="NezhaAgg", daemon=True)
            self._agg_thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._tick.set()

    def snapshot(self) -> Tuple[str, float, int, float]:
        """
        Returns: (cached_json, cache_age_seconds, server_count, last_msg_age)
        """
        with self._lock:
            now = time.time()
            cache_age = max(0.0, now - self._cache_built_at)
            last_msg_age = max(0.0, now - self._last_msg_ts) if self._last_msg_ts else float("inf")
            count = len(self._last_servers)
            return self._cache_json, cache_age, count, last_msg_age

    # ---------- Internal ----------
    def _login(self) -> bool:
        url = f"{NEZHA_DASHBOARD_URL}/api/v1/login"
        payload = {"username": NEZHA_USERNAME, "password": NEZHA_PASSWORD}
        logging.info("Nezha login: trying without nginx basic auth")
        try:
            r = self._session.post(url, json=payload, timeout=HTTP_TIMEOUT, verify=not INSECURE_TLS)
            if r.ok and (r.json().get("success") is True):
                self._need_basic = False
                logging.info("Nezha login ok without basic auth")
                return True
        except Exception as e:
            logging.warning(f"Nezha login without basic failed: {e}")

        if not (NGINX_BASIC_AUTH_USER and NGINX_BASIC_AUTH_PASS):
            logging.error("Nezha login failed and no nginx basic auth creds configured")
            return False

        logging.info("Nezha login: retry with nginx basic auth")
        try:
            r = self._session.post(
                url,
                json=payload,
                timeout=HTTP_TIMEOUT,
                verify=not INSECURE_TLS,
                auth=(NGINX_BASIC_AUTH_USER, NGINX_BASIC_AUTH_PASS),
            )
            if r.ok and (r.json().get("success") is True):
                self._need_basic = True
                logging.info("Nezha login ok with nginx basic auth")
                return True
            logging.error(f"Nezha login with basic auth failed: {r.status_code} {r.text[:200]}")
        except Exception as e:
            logging.error(f"Nezha login with basic auth exception: {e}")

        return False

    def _build_ws_headers(self) -> List[str]:
        jwt = self._session.cookies.get(self._jwt_cookie_name, "")
        headers = [f"Cookie: {self._jwt_cookie_name}={jwt}"]
        if self._need_basic:
            up = f"{NGINX_BASIC_AUTH_USER}:{NGINX_BASIC_AUTH_PASS}"
            b64 = base64.b64encode(up.encode()).decode()
            headers.insert(0, f"Authorization: Basic {b64}")
        return headers

    def _ws_loop(self) -> None:
        backoff = 1.0
        ws_url = NEZHA_DASHBOARD_URL.replace("http://", "ws://").replace("https://", "wss://") + "/api/v1/ws/server"
        while not self._stop.is_set():
            ws = None
            try:
                if not self._login():
                    time.sleep(min(10.0, backoff))
                    backoff = min(10.0, backoff * 1.7)
                    continue

                headers = self._build_ws_headers()
                sslopt = {"cert_reqs": ssl.CERT_NONE} if INSECURE_TLS else None
                logging.info(f"Connecting websocket: {ws_url}")
                ws = websocket.create_connection(
                    ws_url,
                    header=headers,
                    origin=NEZHA_DASHBOARD_URL,
                    sslopt=sslopt,
                    ping_interval=30,
                    ping_timeout=10,
                )
                logging.info("Websocket connected")
                backoff = 1.0

                # Receive loop
                while not self._stop.is_set():
                    msg = ws.recv()
                    if not msg:
                        raise RuntimeError("Empty websocket frame")
                    try:
                        data = _json.loads(msg)
                    except Exception:
                        continue
                    servers = data.get("servers") if isinstance(data, dict) else None
                    if isinstance(servers, list):
                        with self._lock:
                            self._last_servers = servers
                            self._last_msg_ts = time.time()
                            self._dirty = True
                        self._tick.set()
            except Exception as e:
                logging.warning(f"Websocket loop error: {e}. Reconnecting in {backoff:.1f}s")
                time.sleep(min(10.0, backoff))
                backoff = min(10.0, backoff * 1.7)
            finally:
                try:
                    if ws is not None:
                        ws.close()
                except Exception:
                    pass

    def _aggregate_loop(self) -> None:
        # Recompute immediately at start
        self._tick.set()
        while not self._stop.is_set():
            # Wait for new data or timeout to respect refresh ceiling
            self._tick.wait(timeout=REFRESH_SECONDS)
            self._tick.clear()
            with self._lock:
                # Always recompute to keep cache age <= REFRESH_SECONDS
                cached = aggregate_servers_to_countries(self._last_servers)
                new_json = dumps(cached)
                if new_json != self._cache_json:
                    self._cache_json = new_json
                # Update build timestamp even if content unchanged
                self._cache_built_at = time.time()
                self._dirty = False


# -------- Flask app --------
# Disable default static handler to avoid path confusion
app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": "*"}})

streamer = NezhaStreamer()
streamer.start()

# ---- API ----
@app.route("/test")
def test():
    return "Flask app is working!"

@app.route("/api/v1/test-connection")
def test_connection():
    body, cache_age, count, last_msg_age = streamer.snapshot()
    return jsonify({
        "status": "ok" if count > 0 else "stale",
        "server_count": count,
        "cache_age_seconds": round(cache_age, 3),
        "last_message_age_seconds": round(last_msg_age, 3) if last_msg_age != float("inf") else None,
        "refresh_seconds": REFRESH_SECONDS,
    })

@app.route("/api/v1/traffic-stats")
def traffic_stats():
    body, cache_age, _, _ = streamer.snapshot()
    resp = make_response(body, 200)
    resp.headers["Content-Type"] = "application/json"
    resp.headers["Cache-Control"] = "no-store"
    resp.headers["X-Data-Age-Seconds"] = f"{cache_age:.3f}"
    return resp

@app.route("/api/v1/traffic-stream")
def traffic_stream():
    """Server-Sent Events stream of the aggregated JSON. Emits only on change, with light debounce."""
    def gen():
        last = None
        while True:
            body, _, _, _ = streamer.snapshot()
            if body != last:
                yield f"data:{body}\n\n"
                last = body
            time.sleep(0.2)
    return Response(gen(), mimetype="text/event-stream")

# ---- Static and UI ----
def _send_from_two_layers(filename: str):
    """Try /static/<filename> first, then /static/static/<filename> for nested bundles."""
    root = app.root_path
    p1 = os.path.join(root, "static", filename)
    if os.path.isfile(p1):
        return send_from_directory(os.path.join(root, "static"), filename)
    p2_dir = os.path.join(root, "static", "static")
    p2 = os.path.join(p2_dir, filename)
    if os.path.isfile(p2):
        return send_from_directory(p2_dir, filename)
    return ("Not found", 404)

# Serve assets under /static/*
@app.route("/static/<path:filename>")
def serve_assets(filename: str):
    return _send_from_two_layers(filename)

# Index: /
@app.route("/")
def serve_root():
    # Prefer top-level static/index.html, fall back to nested static/static/index.html
    resp = _send_from_two_layers("index.html")
    if isinstance(resp, tuple):  # not found
        return jsonify({"message": "API server up. No UI bundled."})
    return resp

# Any other non-API path: try to serve as a file
@app.route("/<path:path>")
def serve_static(path: str):
    if path.startswith("api/"):
        return "API endpoint not found", 404
    return _send_from_two_layers(path)

if __name__ == "__main__":
    # Disable the werkzeug reloader to avoid double threads
    app.run(host="0.0.0.0", port=5001, use_reloader=False)
