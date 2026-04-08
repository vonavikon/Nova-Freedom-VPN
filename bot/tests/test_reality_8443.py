"""
Unit tests for Standalone Reality 8443 functionality
"""

import unittest
from unittest.mock import Mock
from urllib.parse import urlparse, parse_qs


TEST_PUBLIC_KEY = 'test_public_key_1234567890abcdef'
TEST_DL_PUBLIC_KEY = 'test_dl_public_key_1234567890ab'
TEST_GRPC_PUBLIC_KEY = 'test_grpc_public_key_123456789'


class TestStandaloneReality8443(unittest.TestCase):
    """Test standalone Reality 8443 config generation"""

    def setUp(self):
        """Set up test fixtures"""
        from bot.services.hiddify_manager import HiddifyManager

        self.config = Mock()
        self.config.REALITY_HOST = 'YOUR_SERVER_IP'
        self.config.REALITY_PORT = 8443
        self.config.REALITY_PUBLIC_KEY = TEST_PUBLIC_KEY
        self.config.REALITY_SNI = 'addons.mozilla.org'
        self.config.REALITY_FLOW = 'xtls-rprx-vision'
        self.config.REALITY_FINGERPRINT = 'chrome'

        self.config.BYPASS_HOST = 'YOUR_SERVER_IP'
        self.config.BYPASS_PORT = 443
        self.config.BYPASS_DL_PUBLIC_KEY = TEST_DL_PUBLIC_KEY
        self.config.BYPASS_DL_SNI = 'dl.google.com'
        self.config.BYPASS_DL_FINGERPRINT = 'qq'
        self.config.BYPASS_DL_SID = ''
        self.config.BYPASS_GRPC_PORT = 2053
        self.config.BYPASS_GRPC_PUBLIC_KEY = TEST_GRPC_PUBLIC_KEY
        self.config.BYPASS_GRPC_SNI = 'www.google.com'
        self.config.BYPASS_GRPC_FINGERPRINT = 'random'
        self.config.BYPASS_GRPC_SID = ''

        self.manager = HiddifyManager(self.config)

    def test_generate_reality_8443_basic(self):
        test_uuid = 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertTrue(config_url.startswith('vless://'))

    def test_reality_8443_host_and_port(self):
        test_uuid = 'test-uuid-123'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('@YOUR_SERVER_IP:8443', config_url)

    def test_reality_8443_uuid(self):
        test_uuid = 'abc123-def456-ghi789'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn(test_uuid, config_url)

    def test_reality_8443_security_params(self):
        test_uuid = 'test-uuid'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('security=reality', config_url)
        self.assertIn('sni=addons.mozilla.org', config_url)
        self.assertIn(f'pbk={TEST_PUBLIC_KEY}', config_url)

    def test_reality_8443_flow_and_fingerprint(self):
        test_uuid = 'test-uuid'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('flow=xtls-rprx-vision', config_url)
        self.assertIn('fp=chrome', config_url)

    def test_reality_8443_type_tcp(self):
        test_uuid = 'test-uuid'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('type=tcp', config_url)

    def test_reality_8443_encryption_none(self):
        test_uuid = 'test-uuid'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('encryption=none', config_url)

    def test_reality_8443_has_fragment_name(self):
        test_uuid = '12345678-1234-1234-1234-123456789abc'
        config_url = self.manager.generate_standalone_reality_8443(test_uuid)
        self.assertIn('#Reality-8443', config_url)


class TestConfigConstants(unittest.TestCase):
    """Test that config constants are properly defined"""

    def test_reality_constants_exist(self):
        from bot import config as cfg

        required_attrs = [
            'REALITY_HOST',
            'REALITY_PORT',
            'REALITY_PUBLIC_KEY',
            'REALITY_SNI',
            'REALITY_FLOW',
            'REALITY_FINGERPRINT'
        ]

        for attr in required_attrs:
            self.assertTrue(hasattr(cfg, attr), f"Config should have {attr} attribute")


if __name__ == '__main__':
    unittest.main()
