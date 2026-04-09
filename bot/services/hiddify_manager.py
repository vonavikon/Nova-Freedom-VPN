"""
HiddifyManager — integration with Hiddify Panel API and config generation.
Manages users via Hiddify REST API and generates VLESS+Reality config links.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlencode

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class HiddifyUser:
    """Represents a user created in Hiddify Panel."""
    uuid: str
    usage_limit_gb: float
    package_days: int


class HiddifyManager:
    """Manages Hiddify Panel users and generates VLESS config links."""

    def __init__(self, config):
        self.config = config
        self.api_url = config.HIDDIFY_API_URL
        self.api_key = config.HIDDIFY_API_KEY

    # ── Hiddify Panel API ──────────────────────────────────────────

    async def _api_request(self, method: str, path: str, json_data: dict = None) -> Tuple[bool, Optional[dict]]:
        """Make authenticated request to Hiddify Panel API."""
        if not self.api_url or not self.api_key:
            logger.error("HIDDIFY_API_URL or HIDDIFY_API_KEY not set")
            return False, None

        url = f"{self.api_url.rstrip('/')}/{path.lstrip('/')}"
        headers = {"Hiddify-API-Key": self.api_key}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.request(method, url, json=json_data, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return True, data
                    else:
                        text = await resp.text()
                        logger.error(f"Hiddify API error {resp.status}: {text[:200]}")
                        return False, None
        except Exception as e:
            logger.error(f"Hiddify API request failed: {e}")
            return False, None

    async def create_user(self, name: str, usage_limit_gb: int,
                          package_days: int, telegram_id: int) -> Tuple[bool, Optional[HiddifyUser], Optional[str]]:
        """Create a new user in Hiddify Panel.

        Returns (success, HiddifyUser or None, error_message or None).
        """
        payload = {
            "name": name,
            "usage_limit_GB": usage_limit_gb,
            "package_days": package_days,
            "comment": f"telegram:{telegram_id}",
        }

        success, data = await self._api_request("POST", "admin/user/add/", payload)

        if not success or not data:
            return False, None, "Failed to create user in Hiddify"

        user_data = data.get("user", data)
        uuid = user_data.get("uuid", "")
        if not uuid:
            return False, None, "No UUID in Hiddify response"

        user = HiddifyUser(
            uuid=uuid,
            usage_limit_gb=float(user_data.get("usage_limit_GB", usage_limit_gb)),
            package_days=int(user_data.get("package_days", package_days)),
        )

        logger.info(f"Created Hiddify user {name} (uuid={uuid[:8]}...)")
        return True, user, None

    async def delete_user(self, uuid: str) -> Tuple[bool, Optional[str]]:
        """Delete a user from Hiddify Panel by UUID."""
        success, data = await self._api_request("POST", f"admin/user/delete/{uuid}/")
        if success:
            logger.info(f"Deleted Hiddify user {uuid[:8]}...")
        return success, None if success else "Failed to delete user"

    async def get_cdn_config(self, uuid: str) -> Optional[str]:
        """Fetch CDN (Cloudflare) subscription config from Hiddify Panel."""
        base = self.config.HIDDIFY_CDN_SUBSCRIPTION_BASE
        if not base:
            return None

        url = f"{base.rstrip('/')}/{uuid}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import base64
                        decoded = base64.b64decode(text).decode()
                        for line in decoded.splitlines():
                            if line.strip().startswith("vless://"):
                                return line.strip()
        except Exception as e:
            logger.error(f"Failed to fetch CDN config: {e}")

        return None

    async def get_reality_config(self, uuid: str) -> Optional[str]:
        """Fetch Reality subscription config from Hiddify Panel."""
        base = self.config.HIDDIFY_SUBSCRIPTION_BASE
        if not base:
            return None

        url = f"{base.rstrip('/')}/{uuid}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        text = await resp.text()
                        import base64
                        decoded = base64.b64decode(text).decode()
                        for line in decoded.splitlines():
                            if line.strip().startswith("vless://"):
                                return line.strip()
        except Exception as e:
            logger.error(f"Failed to fetch Reality config: {e}")

        return None

    # ── Local config generation (no API calls) ─────────────────────

    def generate_standalone_reality_8443(self, uuid: str) -> Optional[str]:
        """Generate VLESS+Reality config for standalone Xray on port 8443."""
        host = self.config.REALITY_HOST
        port = self.config.REALITY_PORT
        pbk = self.config.REALITY_PUBLIC_KEY
        sni = self.config.REALITY_SNI
        flow = self.config.REALITY_FLOW
        fp = self.config.REALITY_FINGERPRINT

        if not host or host == "YOUR_SERVER_IP" or not pbk or pbk == "YOUR_PUBLIC_KEY":
            logger.warning("Reality 8443: host or public key not configured")
            return None

        params = urlencode({
            "encryption": "none",
            "flow": flow,
            "security": "reality",
            "sni": sni,
            "fp": fp,
            "pbk": pbk,
            "type": "tcp",
        })

        return f"vless://{uuid}@{host}:{port}?{params}#Reality-8443"

    def generate_bypass_google_dl(self, uuid: str) -> Optional[str]:
        """Generate VLESS+Reality config for dl.google.com bypass (TCP, port 443 via HAProxy)."""
        host = self.config.BYPASS_HOST
        port = self.config.BYPASS_PORT
        pbk = self.config.BYPASS_DL_PUBLIC_KEY
        sni = self.config.BYPASS_DL_SNI
        fp = self.config.BYPASS_DL_FINGERPRINT
        sid = self.config.BYPASS_DL_SID

        if not host or host == "YOUR_SERVER_IP" or not pbk or pbk == "YOUR_DL_PUBLIC_KEY":
            return None

        params = urlencode({
            "encryption": "none",
            "flow": "xtls-rprx-vision",
            "security": "reality",
            "sni": sni,
            "fp": fp,
            "pbk": pbk,
            "type": "tcp",
            "sID": sid or "",
        })

        return f"vless://{uuid}@{host}:{port}?{params}#Google-DL"

    def generate_bypass_google_grpc(self, uuid: str) -> Optional[str]:
        """Generate VLESS+Reality config for www.google.com gRPC bypass (port 2053)."""
        host = self.config.BYPASS_HOST
        port = self.config.BYPASS_GRPC_PORT
        pbk = self.config.BYPASS_GRPC_PUBLIC_KEY
        sni = self.config.BYPASS_GRPC_SNI
        fp = self.config.BYPASS_GRPC_FINGERPRINT
        sid = self.config.BYPASS_GRPC_SID

        if not host or host == "YOUR_SERVER_IP" or not pbk or pbk == "YOUR_GRPC_PUBLIC_KEY":
            return None

        params = urlencode({
            "encryption": "none",
            "security": "reality",
            "sni": sni,
            "fp": fp,
            "pbk": pbk,
            "type": "grpc",
            "sID": sid or "",
        })

        return f"vless://{uuid}@{host}:{port}?{params}#Google-gRPC"
