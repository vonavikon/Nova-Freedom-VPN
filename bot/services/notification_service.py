"""
Notification Service for Nova VPN Bot
Sends notifications to admins
"""

import logging
from typing import List, Optional
from aiogram.types import InlineKeyboardMarkup

logger = logging.getLogger(__name__)


def escape_md(text: str) -> str:
    """Escape Markdown v1 special characters."""
    for ch in ('\\', '`', '*', '_'):
        text = text.replace(ch, f'\\{ch}')
    return text


class NotificationService:
    """Service for sending notifications to admins"""

    def __init__(self, bot, admin_ids: List[int]):
        self.bot = bot
        self.admin_ids = admin_ids

    async def notify_admins(self, message: str, parse_mode: str = "Markdown", reply_markup: InlineKeyboardMarkup = None):
        """Send notification to all admins"""
        for admin_id in self.admin_ids:
            try:
                await self.bot.send_message(
                    admin_id,
                    message,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id}: {e}")

    async def notify_user(self, user_id: int, message: str, parse_mode: str = "Markdown", disable_web_page_preview: bool = False):
        """Send notification to specific user"""
        try:
            await self.bot.send_message(user_id, message, parse_mode=parse_mode, disable_web_page_preview=disable_web_page_preview)
        except Exception as e:
            logger.error(f"Failed to notify user {user_id}: {e}")

    async def notify_new_user_pending(self, telegram_id: int, username: Optional[str], first_name: Optional[str], reply_markup: InlineKeyboardMarkup):
        """Notify admins about new user waiting for approval"""
        name = escape_md(f"@{username}" if username else first_name or f"User {telegram_id}")
        message = f"""🆕 **Новая заявка на доступ**

👤 Пользователь: {name}
🆔 Telegram ID: `{telegram_id}`
📝 Имя: {escape_md(first_name or 'Не указано')}

Требуется одобрение:"""
        await self.notify_admins(message, reply_markup=reply_markup)

    async def notify_user_approved(self, telegram_id: int):
        """Notify user that they were approved"""
        from ..texts import CLIENT_LINKS, VIDEO_TUTORIAL_URL

        video_section = f"\n\n🎬 **Видео инструкция:**\n{VIDEO_TUTORIAL_URL}\n" if VIDEO_TUTORIAL_URL else ""

        message = f"""✅ **Доступ одобрен!**

Теперь вы можете создавать VPN конфигурации.
Нажмите "➕ Добавить VPN" чтобы начать.

{CLIENT_LINKS}{video_section}"""
        await self.notify_user(telegram_id, message, disable_web_page_preview=True)

    async def notify_user_rejected(self, telegram_id: int):
        """Notify user that they were rejected"""
        message = """❌ **Доступ отклонён**

К сожалению, ваша заявка на доступ была отклонена."""
        await self.notify_user(telegram_id, message)

    async def notify_device_created(self, telegram_id: int, device_name: str, protocol: str):
        """Notify admins about new device"""
        message = f"📱 **Новое устройство**\n\n👤 User: `{telegram_id}`\n📲 Device: {device_name}\n🔒 Protocol: {protocol}"
        await self.notify_admins(message)

    async def notify_device_deleted(self, telegram_id: int, device_name: str):
        """Notify admins about device deletion"""
        message = f"🗑️ **Устройство удалено**\n\n👤 User: `{telegram_id}`\n📲 Device: {device_name}"
        await self.notify_admins(message)
