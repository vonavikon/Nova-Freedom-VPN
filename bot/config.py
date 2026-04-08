"""
Configuration file for Nova VPN Bot
Hiddify Integration - VLESS Reality only
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN required")

# Admin IDs
ADMIN_IDS_str = os.getenv("ADMIN_IDS", "")
ADMIN_IDS = list(map(int, ADMIN_IDS_str.split(","))) if ADMIN_IDS_str else []

# Database
DB_PATH = os.getenv("DB_PATH", "/opt/nova-vpn/data/database.db")

# Limits
MAX_CONFIGS_PER_USER = int(os.getenv("MAX_CONFIGS_PER_USER", "3"))
DEFAULT_USAGE_LIMIT_GB = int(os.getenv("DEFAULT_USAGE_LIMIT_GB", "100"))
DEFAULT_PACKAGE_DAYS = int(os.getenv("DEFAULT_PACKAGE_DAYS", "365"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Paths
BASE_DIR = os.getenv("BASE_DIR", "/opt/nova-vpn")
CONFIGS_DIR = os.getenv("CONFIGS_DIR", f"{BASE_DIR}/data/configs")
XRAY_CONFIG_PATH = os.getenv("XRAY_CONFIG_PATH", "/opt/xray-reality/config.json")
XRAY_SERVICE_NAME = os.getenv("XRAY_SERVICE_NAME", "xray-reality")
HIDDIFY_XRAY_CONFIG_PATH = os.getenv("HIDDIFY_XRAY_CONFIG_PATH", "/opt/hiddify-manager/xray/configs/05_inbounds_02_reality_main.json")
HIDDIFY_XRAY_SERVICE_NAME = os.getenv("HIDDIFY_XRAY_SERVICE_NAME", "hiddify-xray")

# Hiddify Configuration (local API)
HIDDIFY_API_URL = os.getenv("HIDDIFY_API_URL")
HIDDIFY_API_KEY = os.getenv("HIDDIFY_API_KEY")
HIDDIFY_SUBSCRIPTION_BASE = os.getenv("HIDDIFY_SUBSCRIPTION_BASE")
HIDDIFY_CDN_SUBSCRIPTION_BASE = os.getenv("HIDDIFY_CDN_SUBSCRIPTION_BASE")
HIDDIFY_REALITY_DOMAIN = os.getenv("HIDDIFY_REALITY_DOMAIN")
HIDDIFY_CDN_DOMAIN = os.getenv("HIDDIFY_CDN_DOMAIN")

# Standalone Xray Reality
REALITY_HOST = os.getenv("REALITY_HOST", "YOUR_SERVER_IP")
REALITY_PORT = int(os.getenv("REALITY_PORT", "8443"))
REALITY_PUBLIC_KEY = os.getenv("REALITY_PUBLIC_KEY", "YOUR_PUBLIC_KEY")
REALITY_SNI = os.getenv("REALITY_SNI", "addons.mozilla.org")
REALITY_FLOW = os.getenv("REALITY_FLOW", "xtls-rprx-vision")
REALITY_FINGERPRINT = os.getenv("REALITY_FINGERPRINT", "chrome")

# Bypass — обход whitelist через Google SNI
BYPASS_HOST = os.getenv("BYPASS_HOST", "YOUR_SERVER_IP")

# Bypass config 1: dl.google.com TCP (fp=qq) — port 443 через HAProxy
BYPASS_PORT = int(os.getenv("BYPASS_PORT", "443"))
BYPASS_DL_PUBLIC_KEY = os.getenv("BYPASS_DL_PUBLIC_KEY", "YOUR_DL_PUBLIC_KEY")
BYPASS_DL_SNI = os.getenv("BYPASS_DL_SNI", "dl.google.com")
BYPASS_DL_FINGERPRINT = os.getenv("BYPASS_DL_FINGERPRINT", "qq")
BYPASS_DL_SID = os.getenv("BYPASS_DL_SID", "")

# Bypass config 2: www.google.com gRPC (fp=random) — port 2053 standalone Xray
BYPASS_GRPC_PORT = int(os.getenv("BYPASS_GRPC_PORT", "2053"))
BYPASS_GRPC_PUBLIC_KEY = os.getenv("BYPASS_GRPC_PUBLIC_KEY", "YOUR_GRPC_PUBLIC_KEY")
BYPASS_GRPC_SNI = os.getenv("BYPASS_GRPC_SNI", "www.google.com")
BYPASS_GRPC_FINGERPRINT = os.getenv("BYPASS_GRPC_FINGERPRINT", "random")
BYPASS_GRPC_SID = os.getenv("BYPASS_GRPC_SID", "")

# Only Hiddify protocol
AVAILABLE_PROTOCOLS = {
    "hiddify": {
        "name": "VLESS Reality",
        "description": "Обход блокировок",
        "icon": "🚀",
        "port": 443,
        "subnet": None,
        "requires_ip": False
    }
}
