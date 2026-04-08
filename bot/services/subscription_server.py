"""
Subscription server for Nova VPN Bot.
Serves base64-encoded VLESS configs via HTTP for VPN client auto-import.
"""

import base64
import logging
import re
from aiohttp import web

logger = logging.getLogger(__name__)

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)


class SubscriptionServer:
    """HTTP server that serves VPN subscription configs per user UUID."""

    def __init__(self, hiddify_manager, xray_manager, config, host="0.0.0.0", port=8888):
        self.hiddify = hiddify_manager
        self.xray_manager = xray_manager
        self.config = config
        self.host = host
        self.port = port
        self.app = web.Application()
        self.app.router.add_get("/sub/{uuid}", self.handle_subscription)

    def _get_configs(self, uuid: str) -> list:
        """Generate all available configs for a UUID."""
        configs = []

        # Bypass configs (mobile)
        bypass_dl = self.hiddify.generate_bypass_google_dl(uuid)
        if bypass_dl:
            configs.append(bypass_dl)

        bypass_grpc = self.hiddify.generate_bypass_google_grpc(uuid)
        if bypass_grpc:
            configs.append(bypass_grpc)

        # Direct Reality (WiFi)
        direct = self.hiddify.generate_standalone_reality_8443(uuid)
        if direct:
            configs.append(direct)

        return configs

    async def handle_subscription(self, request: web.Request) -> web.Response:
        uuid = request.match_info["uuid"]

        # Validate UUID format
        if not UUID_PATTERN.match(uuid):
            return web.Response(status=400, text="Bad request")

        # Verify UUID exists in Xray config
        known_uuids = self.xray_manager.get_client_uuids()
        if uuid not in known_uuids:
            return web.Response(status=404, text="Not found")

        configs = self._get_configs(uuid)
        if not configs:
            return web.Response(status=500, text="No configs")

        payload = "\n".join(configs)
        encoded = base64.b64encode(payload.encode()).decode()

        return web.Response(
            text=encoded,
            content_type="text/plain",
            headers={
                "Content-Disposition": 'attachment; filename="nova-vpn.txt"',
                "Profile-Title": "Nova VPN",
                "Profile-Update-Interval": "6",
                "Subscription-Userinfo": f"upload=0; download=0; total={self.config.DEFAULT_USAGE_LIMIT_GB * 1073741824}",
            },
        )

    async def start(self):
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        logger.info(f"Subscription server started on {self.host}:{self.port}")
