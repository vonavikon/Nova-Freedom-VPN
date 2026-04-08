"""
Tests for XrayConfigManager - manages UUID clients in standalone Xray Reality config
"""

import pytest
import tempfile
import os
import sys
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from bot.services.xray_config_manager import XrayConfigManager


SAMPLE_CONFIG = {
    "log": {"loglevel": "warning"},
    "inbounds": [{
        "tag": "reality-in",
        "port": 8443,
        "protocol": "vless",
        "settings": {
            "clients": [
                {"id": "existing-uuid-1", "flow": "xtls-rprx-vision"},
                {"id": "existing-uuid-2", "flow": "xtls-rprx-vision"}
            ],
            "decryption": "none"
        },
        "streamSettings": {
            "network": "tcp",
            "security": "reality",
            "realitySettings": {
                "dest": "addons.mozilla.org:443",
                "serverNames": ["addons.mozilla.org"],
                "privateKey": "test-private-key",
                "shortIds": [""]
            }
        }
    }],
    "outbounds": [{"tag": "direct", "protocol": "freedom"}]
}


@pytest.fixture
def config_file(tmp_path):
    """Create a temp Xray config file"""
    path = tmp_path / "config.json"
    path.write_text(json.dumps(SAMPLE_CONFIG, indent=2))
    return str(path)


@pytest.fixture
def manager(config_file):
    """XrayConfigManager with temp config, no real service restart"""
    return XrayConfigManager(
        config_path=config_file,
        service_name="xray-reality-test",
        dry_run=True  # don't actually restart systemd
    )


class TestLoadConfig:
    def test_loads_valid_config(self, manager):
        config = manager.load_config()
        assert config is not None
        assert "inbounds" in config

    def test_returns_clients_list(self, manager):
        config = manager.load_config()
        clients = config["inbounds"][0]["settings"]["clients"]
        assert len(clients) == 2

    def test_raises_on_missing_file(self, tmp_path):
        mgr = XrayConfigManager(
            config_path=str(tmp_path / "nonexistent.json"),
            service_name="test",
            dry_run=True
        )
        with pytest.raises(FileNotFoundError):
            mgr.load_config()


class TestAddClient:
    def test_adds_new_uuid(self, manager, config_file):
        new_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        result = manager.add_client(new_uuid)
        assert result is True
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        uuids = [c["id"] for c in clients]
        assert new_uuid in uuids
        assert len(clients) == 3

    def test_new_client_has_flow(self, manager, config_file):
        new_uuid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        manager.add_client(new_uuid)
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        new_client = [c for c in clients if c["id"] == new_uuid][0]
        assert new_client["flow"] == "xtls-rprx-vision"

    def test_skips_duplicate_uuid(self, manager, config_file):
        result = manager.add_client("existing-uuid-1")
        assert result is False
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        assert len(clients) == 2

    def test_preserves_existing_clients(self, manager, config_file):
        manager.add_client("new-uuid")
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        uuids = [c["id"] for c in clients]
        assert "existing-uuid-1" in uuids
        assert "existing-uuid-2" in uuids


class TestRemoveClient:
    def test_removes_existing_uuid(self, manager, config_file):
        result = manager.remove_client("existing-uuid-1")
        assert result is True
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        uuids = [c["id"] for c in clients]
        assert "existing-uuid-1" not in uuids
        assert len(clients) == 1

    def test_returns_false_for_missing_uuid(self, manager):
        result = manager.remove_client("nonexistent-uuid")
        assert result is False

    def test_preserves_other_clients(self, manager, config_file):
        manager.remove_client("existing-uuid-1")
        with open(config_file) as f:
            config = json.load(f)
        clients = config["inbounds"][0]["settings"]["clients"]
        assert clients[0]["id"] == "existing-uuid-2"


class TestGetClients:
    def test_returns_all_uuids(self, manager):
        uuids = manager.get_client_uuids()
        assert "existing-uuid-1" in uuids
        assert "existing-uuid-2" in uuids
        assert len(uuids) == 2

    def test_reflects_additions(self, manager):
        manager.add_client("new-uuid")
        uuids = manager.get_client_uuids()
        assert "new-uuid" in uuids
        assert len(uuids) == 3


class TestRestartService:
    def test_dry_run_returns_true(self, manager):
        result = manager.restart_service()
        assert result is True

    def test_records_restart_call(self, manager):
        manager.add_client("new-uuid")
        assert manager.restart_requested is True
