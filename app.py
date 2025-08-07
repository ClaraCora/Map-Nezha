import flask
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
import websocket 
import json
import logging
import os
import base64
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# --- 1. 配置 ---
logging.basicConfig(level=logging.INFO)

# 从环境变量获取配置，如果没有则使用占位符
NEZHA_DASHBOARD_URL = os.getenv("NEZHA_DASHBOARD_URL", "https://your-nezha-panel.com")  # <-- 替换为你的新 Nezha 面板地址
NEZHA_USERNAME = os.getenv("NEZHA_USERNAME", "your_username")  # <-- 替换为 Nezha 登录用户名
NEZHA_PASSWORD = os.getenv("NEZHA_PASSWORD", "your_password")  # <-- 替换为 Nezha 登录密码

#  nginx basic auth 占位符      （如果不需要，请留空）
NGINX_BASIC_AUTH_USER = os.getenv("NGINX_BASIC_AUTH_USER", "")  # <-- 替换为 nginx basic auth 用户名
NGINX_BASIC_AUTH_PASS = os.getenv("NGINX_BASIC_AUTH_PASS", "")  # <-- 替换为 nginx basic auth 密码

# --- 2. 核心映射表 (请根据您的需求保持更新) ---
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
    "IN": "India",         # 🇮🇳 印度
    "AR": "Argentina",     # 🇦🇷 阿根廷
    "BR": "Brazil",        # 🇧🇷 巴西
    "CO": "Colombia",      # 🇨🇴 哥伦比亚
    "CL": "Chile",         # 🇨🇱 智利
    "SA": "Saudi Arabia",  # 🇸🇦 沙特阿拉伯
    "EG": "Egypt",         # 🇪🇬 埃及
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
    "India": [78.9629, 20.5937],
    "Argentina": [-63.6167, -38.4161],
    "Brazil": [-51.9253, -14.2350],
    "Colombia": [-74.2973, 4.5709],
    "Chile": [-71.542969, -35.675147],
    "Saudi Arabia": [45.0792, 23.8859],
    "Egypt": [30.8025, 26.8206],
}
# 国家 emoji+中文名映射
COUNTRY_EMOJI_CN_MAP = {
    "Singapore": "🇸🇬 新加坡",
    "Germany": "🇩🇪 德国",
    "South Korea": "🇰🇷 韩国",
    "Japan": "🇯🇵 日本",
    "United States of America": "🇺🇸 美国",
    "China": "🇨🇳 中国",
    "Hong Kong": "🇭🇰 中国香港",
    "Taiwan": "🇹🇼 中国台湾",
    "United Kingdom": "🇬🇧 英国",
    "France": "🇫🇷 法国",
    "Australia": "🇦🇺 澳大利亚",
    "Canada": "🇨🇦 加拿大",
    "Netherlands": "🇳🇱 荷兰",
    "Italy": "🇮🇹 意大利",
    "Spain": "🇪🇸 西班牙",
    "Russia": "🇷🇺 俄罗斯",
    "Sweden": "🇸🇪 瑞典",
    "Norway": "🇳🇴 挪威",
    "Denmark": "🇩🇰 丹麦",
    "Finland": "🇫🇮 芬兰",
    "Switzerland": "🇨🇭 瑞士",
    "Austria": "🇦🇹 奥地利",
    "Belgium": "🇧🇪 比利时",
    "Poland": "🇵🇱 波兰",
    "Czech Republic": "🇨🇿 捷克",
    "Hungary": "🇭🇺 匈牙利",
    "Romania": "🇷🇴 罗马尼亚",
    "Bulgaria": "🇧🇬 保加利亚",
    "Croatia": "🇭🇷 克罗地亚",
    "Slovenia": "🇸🇮 斯洛文尼亚",
    "Slovakia": "🇸🇰 斯洛伐克",
    "Lithuania": "🇱🇹 立陶宛",
    "Latvia": "🇱🇻 拉脱维亚",
    "Estonia": "🇪🇪 爱沙尼亚",
    "Ireland": "🇮🇪 爱尔兰",
    "Portugal": "🇵🇹 葡萄牙",
    "Greece": "🇬🇷 希腊",
    "Turkey": "🇹🇷 土耳其",
    "Ukraine": "🇺🇦 乌克兰",
    "Belarus": "🇧🇾 白俄罗斯",
    "Moldova": "🇲🇩 摩尔多瓦",
    "Serbia": "🇷🇸 塞尔维亚",
    "Bosnia and Herzegovina": "🇧🇦 波黑",
    "Montenegro": "🇲🇪 黑山",
    "North Macedonia": "🇲🇰 北马其顿",
    "Albania": "🇦🇱 阿尔巴尼亚",
    "Kosovo": "🇽🇰 科索沃",
    "Georgia": "🇬🇪 格鲁吉亚",
    "Armenia": "🇦🇲 亚美尼亚",
    "Azerbaijan": "🇦🇿 阿塞拜疆",
    "Kazakhstan": "🇰🇿 哈萨克斯坦",
    "Uzbekistan": "🇺🇿 乌兹别克斯坦",
    "Kyrgyzstan": "🇰🇬 吉尔吉斯斯坦",
    "Tajikistan": "🇹🇯 塔吉克斯坦",
    "Turkmenistan": "🇹🇲 土库曼斯坦",
    "Afghanistan": "🇦🇫 阿富汗",
    "Pakistan": "🇵🇰 巴基斯坦",
    "Bangladesh": "🇧🇩 孟加拉国",
    "Sri Lanka": "🇱🇰 斯里兰卡",
    "Nepal": "🇳🇵 尼泊尔",
    "Bhutan": "🇧🇹 不丹",
    "Maldives": "🇲🇻 马尔代夫",
    "Malaysia": "🇲🇾 马来西亚",
    "Thailand": "🇹🇭 泰国",
    "Vietnam": "🇻🇳 越南",
    "Laos": "🇱🇦 老挝",
    "Cambodia": "🇰🇭 柬埔寨",
    "Myanmar": "🇲🇲 缅甸",
    "Philippines": "🇵🇭 菲律宾",
    "Indonesia": "🇮🇩 印度尼西亚",
    "Brunei": "🇧🇳 文莱",
    "East Timor": "🇹🇱 东帝汶",
    "Papua New Guinea": "🇵🇬 巴布亚新几内亚",
    "Fiji": "🇫🇯 斐济",
    "New Caledonia": "🇳🇨 新喀里多尼亚",
    "Vanuatu": "🇻🇺 瓦努阿图",
    "Solomon Islands": "🇸🇧 所罗门群岛",
    "Kiribati": "🇰🇮 基里巴斯",
    "Tonga": "🇹🇴 汤加",
    "Samoa": "🇼🇸 萨摩亚",
    "Tuvalu": "🇹🇻 图瓦卢",
    "Nauru": "🇳🇷 瑙鲁",
    "Palau": "🇵🇼 帕劳",
    "Marshall Islands": "🇲🇭 马绍尔群岛",
    "Micronesia": "🇫🇲 密克罗尼西亚",
    "Cook Islands": "🇨🇰 库克群岛",
    "Niue": "🇳🇺 纽埃",
    "Tokelau": "🇹🇰 托克劳",
    "American Samoa": "🇦🇸 美属萨摩亚",
    "Guam": "🇬🇺 关岛",
    "Northern Mariana Islands": "🇲🇵 北马里亚纳群岛",
    "India": "🇮🇳 印度",
    "Argentina": "🇦🇷 阿根廷",
    "Brazil": "🇧🇷 巴西",
    "Colombia": "🇨🇴 哥伦比亚",
    "Chile": "🇨🇱 智利",
    "Saudi Arabia": "🇸🇦 沙特阿拉伯",
    "Egypt": "🇪🇬 埃及",
}

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])  # 启用跨域支持

@app.route('/test')
def test():
    return "Flask app is working!"

@app.route('/api/v1/test-connection')
def test_nezha_connection():
    """
    测试哪吒监控连接和认证状态
    """
    try:
        servers = get_nezha_data_via_websocket()
        if servers is None:
            return jsonify({
                "status": "error",
                "message": "无法连接到哪吒监控",
                "details": "请检查网络连接、哪吒面板地址和认证信息"
            }), 503
        
        return jsonify({
            "status": "success",
            "message": f"成功连接到哪吒监控，获取到 {len(servers)} 个服务器数据",
            "server_count": len(servers),
            "sample_data": servers[0] if servers else None
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"连接测试失败: {str(e)}"
        }), 500

@app.route('/api/v1/diagnose')
def diagnose_connection():
    """
    详细诊断哪吒监控连接问题
    """
    import socket
    from urllib.parse import urlparse
    
    results = {
        "config": {
            "dashboard_url": NEZHA_DASHBOARD_URL,
            "username": NEZHA_USERNAME,
            "password_set": bool(NEZHA_PASSWORD),
            "nginx_auth_user": NGINX_BASIC_AUTH_USER,
            "nginx_auth_pass": NGINX_BASIC_AUTH_PASS,
            "nginx_auth_configured": bool(NGINX_BASIC_AUTH_USER and NGINX_BASIC_AUTH_PASS)
        },
        "network_tests": {},
        "auth_tests": {},
        "recommendations": []
    }
    
    # 1. 网络连接测试
    try:
        parsed_url = urlparse(NEZHA_DASHBOARD_URL)
        host = parsed_url.hostname
        port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
        
        # DNS解析测试
        try:
            ip = socket.gethostbyname(host)
            results["network_tests"]["dns_resolution"] = {"status": "success", "ip": ip}
        except socket.gaierror as e:
            results["network_tests"]["dns_resolution"] = {"status": "error", "error": str(e)}
            results["recommendations"].append("DNS解析失败，请检查哪吒面板地址是否正确")
        
        # 端口连接测试
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                results["network_tests"]["port_connection"] = {"status": "success", "port": port}
            else:
                results["network_tests"]["port_connection"] = {"status": "error", "port": port, "error_code": result}
                results["recommendations"].append(f"端口 {port} 连接失败，请检查防火墙设置")
        except Exception as e:
            results["network_tests"]["port_connection"] = {"status": "error", "error": str(e)}
            
    except Exception as e:
        results["network_tests"]["url_parsing"] = {"status": "error", "error": str(e)}
        results["recommendations"].append("哪吒面板地址格式错误")
    
    # 2. HTTP连接测试
    try:
        import requests
        from requests.exceptions import RequestException
        
        # 测试基本HTTP连接
        try:
            resp = requests.get(NEZHA_DASHBOARD_URL, timeout=10, verify=False)
            results["network_tests"]["http_connection"] = {
                "status": "success", 
                "status_code": resp.status_code,
                "requires_auth": resp.status_code == 401
            }
        except RequestException as e:
            results["network_tests"]["http_connection"] = {"status": "error", "error": str(e)}
            results["recommendations"].append("HTTP连接失败，请检查网络连接")
        
        # 测试登录API
        login_url = f"{NEZHA_DASHBOARD_URL}/api/v1/login"
        login_payload = {"username": NEZHA_USERNAME, "password": NEZHA_PASSWORD}
        
        # 不带nginx auth的登录测试
        try:
            resp = requests.post(login_url, json=login_payload, timeout=10, verify=False)
            results["auth_tests"]["login_without_nginx"] = {
                "status": "success" if resp.status_code == 200 else "error",
                "status_code": resp.status_code,
                "response": resp.json() if resp.status_code == 200 else None
            }
        except RequestException as e:
            results["auth_tests"]["login_without_nginx"] = {"status": "error", "error": str(e)}
        
        # 带nginx auth的登录测试（如果配置了）
        if NGINX_BASIC_AUTH_USER and NGINX_BASIC_AUTH_PASS:
            try:
                resp = requests.post(
                    login_url, 
                    json=login_payload, 
                    timeout=10, 
                    verify=False,
                    auth=(NGINX_BASIC_AUTH_USER, NGINX_BASIC_AUTH_PASS)
                )
                results["auth_tests"]["login_with_nginx"] = {
                    "status": "success" if resp.status_code == 200 else "error",
                    "status_code": resp.status_code,
                    "response": resp.json() if resp.status_code == 200 else None
                }
            except RequestException as e:
                results["auth_tests"]["login_with_nginx"] = {"status": "error", "error": str(e)}
        else:
            results["auth_tests"]["login_with_nginx"] = {"status": "skipped", "reason": "nginx auth not configured"}
            
    except ImportError:
        results["auth_tests"]["error"] = "requests library not available"
    
    # 3. 生成建议
    if not NGINX_BASIC_AUTH_USER or not NGINX_BASIC_AUTH_PASS:
        results["recommendations"].append("nginx basic auth未配置，如果面板有nginx认证，请配置用户名和密码")
    
    if not NEZHA_PASSWORD:
        results["recommendations"].append("哪吒面板密码未配置")
    
    return jsonify(results)

def get_nezha_data_via_websocket():
    """
    通过 WebSocket 获取哪吒监控数据，自动检测是否需要nginx basic auth。
    """
    http_session = requests.Session()
    login_url = f"{NEZHA_DASHBOARD_URL}/api/v1/login"
    login_payload = {"username": NEZHA_USERNAME, "password": NEZHA_PASSWORD}

    # 1. 首先尝试不带nginx basic auth的HTTP登录
    try:
        logging.info("正在尝试不带nginx basic auth的HTTP登录...")
        login_resp = http_session.post(
            login_url,
            json=login_payload,
            timeout=10
        )
        login_resp.raise_for_status()
        if login_resp.json().get("success") == True:
            logging.info("登录成功（无需nginx basic auth）")
            nginx_auth_required = False
        else:
            logging.warning("登录失败，尝试带nginx basic auth...")
            nginx_auth_required = True
    except requests.RequestException as e:
        logging.warning(f"不带nginx basic auth的登录失败: {e}，尝试带认证...")
        nginx_auth_required = True

    # 2. 如果需要nginx basic auth，重新尝试
    if nginx_auth_required:
        try:
            logging.info("正在通过带nginx basic auth的HTTP登录...")
            login_resp = http_session.post(
                login_url,
                json=login_payload,
                timeout=10,
                auth=(NGINX_BASIC_AUTH_USER, NGINX_BASIC_AUTH_PASS)
            )
            login_resp.raise_for_status()
            if login_resp.json().get("success") != True:
                logging.error(f"带nginx basic auth的登录也失败: {login_resp.json().get('message', '未知错误')}")
                return None
            logging.info("带nginx basic auth的登录成功")
        except requests.RequestException as e:
            logging.error(f"带nginx basic auth的HTTP登录请求失败: {e}")
            return None

    # 3. 提取 JWT Cookie
    jwt_token = http_session.cookies.get("nz-jwt")
    if not jwt_token:
        logging.error("未能在登录响应中找到 nz-jwt cookie。")
        return None

    # 4. 建立 WebSocket 连接
    ws_url = NEZHA_DASHBOARD_URL.replace("http", "ws") + "/api/v1/ws/server"
    ws = None
    try:
        logging.info(f"正在连接到 WebSocket: {ws_url}")
        
        # 根据是否需要nginx basic auth设置headers
        if nginx_auth_required:
            # 生成 Basic Auth 头
            user_pass = f"{NGINX_BASIC_AUTH_USER}:{NGINX_BASIC_AUTH_PASS}"
            basic_auth = base64.b64encode(user_pass.encode()).decode()
            headers = [
                f"Authorization: Basic {basic_auth}",
                f"Cookie: nz-jwt={jwt_token}"
            ]
        else:
            # 不需要nginx basic auth
            headers = [
                f"Cookie: nz-jwt={jwt_token}"
            ]
            
        ws = websocket.create_connection(
            ws_url,
            header=headers,
            origin=NEZHA_DASHBOARD_URL
        )
        logging.info("WebSocket 连接成功！")
        # 5. 接收第一个数据包 (通常是包含所有服务器信息的初始数据)
        logging.info("正在等待接收服务器数据...")
        message = ws.recv()
        logging.info("已成功接收数据！")
        data = json.loads(message)
        logging.info(f"接收到的数据结构: {list(data.keys()) if isinstance(data, dict) else '非字典类型'}")
        # 根据经验，数据在 "servers" 键下
        servers = data.get("servers", [])
        logging.info(f"找到 {len(servers)} 个服务器")
        return servers

    except Exception as e:
        logging.error(f"WebSocket 操作失败: {e}")
        return None
    finally:
        if ws:
            ws.close()
            logging.info("WebSocket 连接已关闭。")


# 添加静态文件路由
@app.route('/')
def serve_react():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    if path.startswith('api/'):
        return "API endpoint not found", 404
    return send_from_directory('static', path)

@app.route('/api/v1/traffic-stats')
def get_traffic_stats():
    servers = get_nezha_data_via_websocket()
    if servers is None:
        return jsonify({"error": "无法从哪吒监控获取数据，请检查服务日志。"}), 503

    countries_data = {}
    # 数据结构从之前的 `server.get("Host")` 变为 `server.get("host")`，根据实际情况调整
    logging.info(f"开始处理 {len(servers)} 个服务器数据")
    for i, server in enumerate(servers):
        logging.info(f"处理服务器 {i+1}: {list(server.keys()) if isinstance(server, dict) else '非字典类型'}")
        
        # 尝试不同的数据结构
        host_info = server.get("host") or server.get("Host")
        status_info = server.get("state") or server.get("State") or server.get("status")
        
        if not host_info or not status_info:
            logging.warning(f"服务器 {i+1} 缺少必要信息")
            continue
        
        # 尝试从不同位置获取国家代码
        country_code = (host_info.get("CountryCode") or 
                       server.get("country_code") or 
                       "").upper()
        if not country_code:
            logging.warning(f"服务器 {i+1} 没有国家代码")
            continue
            
        country_name_en = COUNTRY_CODE_TO_NAME_MAP.get(country_code)
        if not country_name_en:
            logging.warning(f"警告：找不到国家代码 '{country_code}' 的映射")
            continue

        if country_name_en not in countries_data:
            coords = COUNTRY_COORDS.get(country_name_en, [0, 0])
            countries_data[country_name_en] = {
                "uplinkSpeed": 0, "downlinkSpeed": 0, "coords": coords
            }
        
        # 累加网速 (单位: bytes/s)
        net_out = status_info.get("net_out_speed", 0)
        net_in = status_info.get("net_in_speed", 0)
        countries_data[country_name_en]["uplinkSpeed"] += net_out
        countries_data[country_name_en]["downlinkSpeed"] += net_in
        logging.info(f"服务器 {i+1} ({country_name_en}): 上行 {net_out}, 下行 {net_in}")
        logging.info(f"status_info内容: {status_info}")

    # 格式化输出
    output_data = []
    for name, data in countries_data.items():
        output_data.append({
            "countryNameEN": name,
            "countryNameEmojiCN": COUNTRY_EMOJI_CN_MAP.get(name, f"🌐 {name}"),
            "uplinkSpeed": round((data["uplinkSpeed"] * 8) / 1e6, 2), # to Mbps
            "downlinkSpeed": round((data["downlinkSpeed"] * 8) / 1e6, 2), # to Mbps
            "coords": data["coords"]
        })

    logging.info(f"返回 {len(output_data)} 个国家的数据")
    logging.info(f"输出数据: {output_data}")
    return jsonify(output_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)