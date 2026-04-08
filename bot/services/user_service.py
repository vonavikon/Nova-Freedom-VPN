"""
User Service for Nova VPN Bot
Handles device creation, management, and Hiddify integration
"""

import logging
from typing import Tuple, Optional, Dict

from ..database import Database, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from .hiddify_manager import HiddifyManager
from .notification_service import NotificationService

logger = logging.getLogger(__name__)


class UserService:
    """Service for managing users and devices"""

    def __init__(self, db: Database, hiddify: HiddifyManager, config, notification: NotificationService, xray_manager=None):
        self.db = db
        self.hiddify = hiddify
        self.config = config
        self.notification = notification
        self.xray_manager = xray_manager

    async def get_or_create_user(self, telegram_id: int, username: str = None,
                                  first_name: str = None, last_name: str = None) -> Dict:
        """Get or create user in database"""
        return self.db.get_or_create_user(telegram_id, username, first_name, last_name)

    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Get user by Telegram ID"""
        return self.db.get_user(telegram_id)

    def is_user_approved(self, telegram_id: int) -> bool:
        """Check if user is approved"""
        return self.db.is_user_approved(telegram_id)

    def get_user_status(self, telegram_id: int) -> Optional[str]:
        """Get user status"""
        return self.db.get_user_status(telegram_id)

    def approve_user(self, telegram_id: int) -> bool:
        """Approve user"""
        return self.db.approve_user(telegram_id)

    def reject_user(self, telegram_id: int) -> bool:
        """Reject user"""
        return self.db.reject_user(telegram_id)

    def get_user_devices(self, telegram_id: int) -> list:
        """Get all devices for user"""
        user = self.get_user(telegram_id)
        if not user:
            return []
        return self.db.get_user_devices(user['id'])

    def get_device_count(self, telegram_id: int) -> int:
        """Get device count for user"""
        user = self.get_user(telegram_id)
        if not user:
            return 0
        return self.db.get_device_count(user['id'])

    def can_create_device(self, telegram_id: int, device_name: str, protocol: str) -> Tuple[bool, str]:
        """Check if user can create device"""
        user = self.get_user(telegram_id)
        if not user:
            return False, "Пользователь не найден"

        # Check if user is approved
        if not self.is_user_approved(telegram_id):
            status = self.get_user_status(telegram_id)
            if status == STATUS_PENDING:
                return False, "⏳ Ваша заявка на рассмотрении. Ожидайте одобрения администратора."
            elif status == STATUS_REJECTED:
                return False, "❌ Ваш доступ был отклонён."
            else:
                return False, "❌ Доступ запрещён. Обратитесь к администратору."

        # Check device count
        count = self.db.get_device_count(user['id'])
        if count >= self.config.MAX_CONFIGS_PER_USER:
            return False, f"Максимум {self.config.MAX_CONFIGS_PER_USER} устройств"

        # Check device name uniqueness
        existing = self.db.get_device_by_name(user['id'], device_name)
        if existing:
            return False, "Устройство с таким именем уже существует"

        # Check protocol
        if protocol not in self.config.AVAILABLE_PROTOCOLS:
            return False, f"Протокол {protocol} не поддерживается"

        return True, ""

    async def create_device(self, telegram_id: int, device_name: str, protocol: str) -> Tuple[bool, str, Optional[Dict]]:
        """Create new VPN device for user"""

        # Validate
        is_valid, msg = self.can_create_device(telegram_id, device_name, protocol)
        if not is_valid:
            return False, msg, None

        user = self.get_user(telegram_id)
        username = user.get('username', '') if user else ''
        display_name = f"{username}_{device_name}" if username else device_name

        # Create in Hiddify
        success, hiddify_user, error = await self.hiddify.create_user(
            name=display_name,
            usage_limit_gb=self.config.DEFAULT_USAGE_LIMIT_GB,
            package_days=self.config.DEFAULT_PACKAGE_DAYS,
            telegram_id=telegram_id
        )

        if not success or not hiddify_user:
            return False, f"Ошибка Hiddify: {error}", None

        # Priority 1: Google DL bypass (dl.google.com TCP) — мобильный основной
        config_link = self.hiddify.generate_bypass_google_dl(hiddify_user.uuid)

        # Priority 2: Standalone Reality 8443 (WiFi/обычный интернет)
        if not config_link:
            config_link = self.hiddify.generate_standalone_reality_8443(hiddify_user.uuid)

        # Priority 3: CDN config (fallback для агрессивной блокировки)
        if not config_link:
            config_link = await self.hiddify.get_cdn_config(hiddify_user.uuid)

        if not config_link:
            # Clean up
            await self.hiddify.delete_user(hiddify_user.uuid)
            return False, "Не удалось получить конфиг", None

        # Save to database
        device_id = self.db.add_device(
            user_id=user['id'],
            device_name=device_name,
            public_key=hiddify_user.uuid,  # Store UUID as public_key
            private_key="",  # Not needed for Hiddify
            protocol=protocol,
            ip_address="hiddify",
            preshared_key=""
        )

        if not device_id:
            await self.hiddify.delete_user(hiddify_user.uuid)
            return False, "Ошибка базы данных", None

        # Add UUID to standalone Xray Reality config
        if self.xray_manager:
            try:
                self.xray_manager.add_client(hiddify_user.uuid)
            except Exception as e:
                logger.error(f"Failed to add UUID to Xray config: {e}")

        result = {
            'device_id': device_id,
            'device_name': device_name,
            'protocol': protocol,
            'config': config_link,
            'subscription_url': f"http://{self.config.REALITY_HOST}:8888/sub/{hiddify_user.uuid}",
            'uuid': hiddify_user.uuid,
            'usage_limit_gb': hiddify_user.usage_limit_gb,
            'package_days': hiddify_user.package_days
        }

        logger.info(f"Created device {device_name} ({protocol}) for user {telegram_id}")
        return True, "Устройство создано", result

    async def delete_device(self, telegram_id: int, device_id: int) -> Tuple[bool, str]:
        """Delete device"""
        device = self.db.get_device(device_id)
        if not device:
            return False, "Устройство не найдено"

        user = self.get_user(telegram_id)
        if not user or device['user_id'] != user['id']:
            return False, "Нет доступа к устройству"

        # Delete from Hiddify
        uuid = device.get('public_key')  # UUID stored as public_key
        if uuid:
            success, _ = await self.hiddify.delete_user(uuid)
            if not success:
                logger.warning(f"Failed to delete from Hiddify: {uuid}")

        # Remove from standalone Xray Reality config
        if self.xray_manager and uuid:
            try:
                self.xray_manager.remove_client(uuid)
            except Exception as e:
                logger.error(f"Failed to remove UUID from Xray config: {e}")

        # Delete from database
        self.db.remove_device(device_id)

        return True, "Устройство удалено"

    async def get_device_config(self, telegram_id: int, device_id: int) -> Tuple[bool, str, Optional[str]]:
        """
        Get device config. Returns multiple configs for mobile bypass.

        Priority:
        0. Google DL bypass (dl.google.com TCP) — мобильный основной
        1. Google gRPC bypass (www.google.com gRPC) — мобильный fallback
        2. Standalone Reality 8443 — для WiFi/обычного интернета
        """
        device = self.db.get_device(device_id)
        if not device:
            return False, "Устройство не найдено", None

        user = self.get_user(telegram_id)
        if not user or device['user_id'] != user['id']:
            return False, "Нет доступа", None

        uuid = device.get('public_key')
        if not uuid:
            return False, "UUID не найден", None

        # Generate all configs
        bypass_dl = self.hiddify.generate_bypass_google_dl(uuid)
        bypass_grpc = self.hiddify.generate_bypass_google_grpc(uuid)
        direct_config = self.hiddify.generate_standalone_reality_8443(uuid)

        config = bypass_dl or bypass_grpc or direct_config

        if not config:
            config = await self.hiddify.get_reality_config(uuid)

        if not config:
            return False, "Не удалось получить конфиг", None

        sub_url = f"http://{self.config.REALITY_HOST}:8888/sub/{uuid}"
        return True, config, sub_url
