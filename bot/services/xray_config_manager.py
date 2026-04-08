"""
XrayConfigManager - manages client UUIDs in standalone Xray Reality config.
Adds/removes UUIDs and restarts the systemd service.
"""

import json
import logging
import subprocess
from typing import List, Optional

import os

logger = logging.getLogger(__name__)


class XrayConfigManager:

    def __init__(self, config_path: str, service_name: str = "xray-reality",
                 secondary_config_path: Optional[str] = None,
                 secondary_service_name: Optional[str] = None,
                 dry_run: bool = False):
        self.config_path = config_path
        self.service_name = service_name
        # Decouple from Hiddify: don't sync UUIDs or Hiddify's xray config
        # Hiddify manages its own Reality inbound independently.
        self.secondary_config_path = None
        self.secondary_service_name = None
        self.dry_run = dry_run
        self.restart_requested = False

    def load_config(self) -> dict:
        with open(self.config_path, 'r') as f:
            return json.load(f)

    def _save_config(self, config: dict):
        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def _get_clients(self, config: dict) -> list:
        return config["inbounds"][0]["settings"]["clients"]

    def get_client_uuids(self) -> List[str]:
        config = self.load_config()
        return [c["id"] for c in self._get_clients(config)]

    def _update_all_inbounds(self, config: dict, uuid: str, add: bool) -> bool:
        """Add or remove uuid from all inbounds in the config. Returns True if changed."""
        changed = False
        for inbound in config.get("inbounds", []):
            clients = inbound.get("settings", {}).get("clients", [])
            if add:
                if not any(c["id"] == uuid for c in clients):
                    uses_flow = any("flow" in c for c in clients)
                    if uses_flow:
                        clients.append({"id": uuid, "flow": "xtls-rprx-vision"})
                    else:
                        clients.append({"id": uuid})
                    changed = True
            else:
                original_len = len(clients)
                clients[:] = [c for c in clients if c["id"] != uuid]
                if len(clients) < original_len:
                    changed = True
        return changed

    def add_client(self, uuid: str) -> bool:
        config = self.load_config()
        changed = self._update_all_inbounds(config, uuid, add=True)
        if changed:
            self._save_config(config)
            self.restart_service()
            logger.info(f"Added UUID {uuid} to Xray config")

        # No longer sync with Hiddify — Hiddify manages its own Reality inbound
        return changed

    def remove_client(self, uuid: str) -> bool:
        config = self.load_config()
        changed = self._update_all_inbounds(config, uuid, add=False)
        if changed:
            self._save_config(config)
            self.restart_service()
            logger.info(f"Removed UUID {uuid} from Xray config")
        # No longer sync with Hiddify — Hiddify manages its own Reality inbound
 return changed

