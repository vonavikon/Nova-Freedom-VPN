"""
Texts for Nova VPN Bot
All user-facing text strings in one place for easy editing
"""

# ========== CONSTANTS ==========
MAX_DEVICES = 3
DEFAULT_TRAFFIC_GB = 100
DEFAULT_DAYS = 365
VIDEO_TUTORIAL_URL = ""  # unused, video is now sent as Telegram file

# ========== CLIENT LINKS ==========
CLIENT_LINKS = """**Рекомендуемые клиенты:**
📱 iOS: [VPnet](https://apps.apple.com/ru/app/vpnet/id6756558545), [V2Box](https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690)
🤖 Android: [VPnet](https://play.google.com/store/apps/details?id=com.gmm.vpnet.client), [V2Box](https://play.google.com/store/apps/details?id=com.v2box.client)
💻 Windows/Mac: [Hiddify](https://hiddify.com/)"""

CLIENT_LINKS_HTML = """<b>Рекомендуемые клиенты:</b>
📱 iOS: <a href="https://apps.apple.com/ru/app/vpnet/id6756558545">VPnet</a>, <a href="https://apps.apple.com/us/app/v2box-v2ray-client/id6446814690">V2Box</a>
🤖 Android: <a href="https://play.google.com/store/apps/details?id=com.gmm.vpnet.client">VPnet</a>, <a href="https://play.google.com/store/apps/details?id=com.v2box.client">V2Box</a>
💻 Windows/Mac: <a href="https://hiddify.com/">Hiddify</a>"""

# ========== HELP TEXT (full version for /help command and reply button) ==========
def format_help_full() -> str:
    return f"""❓ <b>Справка Nova VPN</b>

Контакт админа: см. /start

<b>Доступные команды:</b>
/start - Главное меню
/myconfig - Мои устройства

<b>Как подключиться:</b>
1. Нажмите "Добавить VPN"
2. Выберите название устройства
3. Скопируйте <b>ссылку подписки</b>
4. Добавьте в клиент (VPNet/Streisand/Husi/v2rayNG)
5. Пользуйтесь!

{CLIENT_LINKS_HTML}"""


# ========== HELP TEXT (short version for inline button) ==========
def format_help_short() -> str:
    return f"""❓ <b>Справка Nova VPN</b>

<b>Как подключиться:</b>
1. Нажмите "Добавить VPN"
2. Выберите название устройства
3. Скопируйте <b>ссылку подписки</b>
4. Добавьте в клиент (VPNet/Streisand/Husi/v2rayNG)
5. Пользуйтесь!

{CLIENT_LINKS_HTML}"""

# ========== DEVICE CREATED ==========
def format_device_created(device_name: str, usage_gb: float, package_days: int, config: str = '', sub_url: str = None) -> str:
    sub_block = f"\n🔗 **Подписка:**\n```\n{sub_url}\n```" if sub_url else ""
    return f"""✅ **Устройство создано!**

📱 **Название:** {device_name}
{sub_block}

ℹ️ Скопируйте ссылку подписки и добавьте в клиент

{CLIENT_LINKS}"""


# ========== DEVICE INFO ==========
def format_device_info(device_name: str, device_id: int, config: str = '', usage_gb: float = 100, package_days: int = 365, sub_url: str = None) -> str:
    sub_block = f"\n🔗 **Подписка:**\n```\n{sub_url}\n```" if sub_url else ""
    return f"""**{device_name}**
{sub_block}

{CLIENT_LINKS}"""


# ========== STATS ==========
def format_stats(device_count: int) -> str:
    return f"""📊 **Ваша статистика**

📱 Устройств: {device_count}/3"""
