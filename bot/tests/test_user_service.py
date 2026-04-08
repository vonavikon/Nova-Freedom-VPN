"""
Tests for UserService - Device Creation with Approval Check
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

# Add project root to path for absolute imports
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from bot.database import Database, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from bot.services.user_service import UserService


@pytest.fixture
def db():
    """Create temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    database = Database(db_path)
    yield database
    os.unlink(db_path)


@pytest.fixture
def mock_hiddify():
    """Mock HiddifyManager"""
    return AsyncMock()


@pytest.fixture
def mock_notification():
    """Mock NotificationService"""
    return AsyncMock()


@pytest.fixture
def mock_config():
    """Mock config"""
    config = MagicMock()
    config.MAX_CONFIGS_PER_USER = 10
    config.AVAILABLE_PROTOCOLS = {'hiddify': {'name': 'VLESS Reality'}}
    return config


@pytest.fixture
def user_service(db, mock_hiddify, mock_config, mock_notification):
    """Create UserService with mocked dependencies"""
    return UserService(db, mock_hiddify, mock_config, mock_notification)


class TestCanCreateDeviceApproval:
    """Test can_create_device with approval status check"""

    def test_pending_user_cannot_create_device(self, user_service, db):
        """Pending user cannot create device"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='iPhone',
            protocol='hiddify'
        )

        assert can_create is False
        assert 'ожидании' in message.lower() or 'pending' in message.lower() or 'одобрения' in message.lower()

    def test_approved_user_can_create_device(self, user_service, db):
        """Approved user can create device"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='iPhone',
            protocol='hiddify'
        )

        assert can_create is True
        assert message == ""

    def test_rejected_user_cannot_create_device(self, user_service, db):
        """Rejected user cannot create device"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.reject_user(telegram_id=12345)

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='iPhone',
            protocol='hiddify'
        )

        assert can_create is False
        assert 'отклонён' in message.lower() or 'rejected' in message.lower()

    def test_nonexistent_user_cannot_create_device(self, user_service):
        """Non-existent user cannot create device"""
        can_create, message = user_service.can_create_device(
            telegram_id=99999,
            device_name='iPhone',
            protocol='hiddify'
        )

        assert can_create is False
        assert 'не найден' in message.lower() or 'not found' in message.lower()


class TestCanCreateDeviceLimits:
    """Test can_create_device with device limits"""

    def test_approved_user_respects_device_limit(self, user_service, db, mock_config):
        """Approved user cannot exceed device limit"""
        mock_config.MAX_CONFIGS_PER_USER = 2

        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        # Add devices up to limit
        user = db.get_user(telegram_id=12345)
        db.add_device(user['id'], 'Device1', 'key1', 'priv1', 'hiddify')
        db.add_device(user['id'], 'Device2', 'key2', 'priv2', 'hiddify')

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='Device3',
            protocol='hiddify'
        )

        assert can_create is False
        assert 'максимум' in message.lower() or '2' in message

    def test_approved_user_cannot_duplicate_device_name(self, user_service, db):
        """Approved user cannot create device with duplicate name"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        # Add a device
        user = db.get_user(telegram_id=12345)
        db.add_device(user['id'], 'iPhone', 'key1', 'priv1', 'hiddify')

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='iPhone',
            protocol='hiddify'
        )

        assert can_create is False
        assert 'уже существует' in message.lower() or 'already' in message.lower()

    def test_invalid_protocol_rejected(self, user_service, db):
        """Invalid protocol is rejected"""
        db.get_or_create_user(telegram_id=12345, username='testuser')
        db.approve_user(telegram_id=12345)

        can_create, message = user_service.can_create_device(
            telegram_id=12345,
            device_name='iPhone',
            protocol='invalid_protocol'
        )

        assert can_create is False
        assert 'протокол' in message.lower() or 'protocol' in message.lower()


class TestUserServiceHelpers:
    """Test UserService helper methods"""

    def test_is_user_approved(self, user_service, db):
        """is_user_approved returns correct status"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        assert user_service.is_user_approved(12345) is False

        db.approve_user(12345)

        assert user_service.is_user_approved(12345) is True

    def test_get_user_status(self, user_service, db):
        """get_user_status returns correct status"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        assert user_service.get_user_status(12345) == STATUS_PENDING

        db.approve_user(12345)
        assert user_service.get_user_status(12345) == STATUS_APPROVED

        db.reject_user(12345)
        assert user_service.get_user_status(12345) == STATUS_REJECTED

    def test_approve_user(self, user_service, db):
        """approve_user updates status"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        result = user_service.approve_user(12345)

        assert result is True
        assert db.is_user_approved(12345) is True

    def test_reject_user(self, user_service, db):
        """reject_user updates status"""
        db.get_or_create_user(telegram_id=12345, username='testuser')

        result = user_service.reject_user(12345)

        assert result is True
        assert db.get_user_status(12345) == STATUS_REJECTED
