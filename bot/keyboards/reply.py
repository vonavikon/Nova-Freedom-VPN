"""
Reply Keyboards for Nova VPN Bot
"""

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove


def get_main_reply_keyboard(has_access: bool = True) -> ReplyKeyboardMarkup:
    """Main menu reply keyboard"""
    if has_access:
        return ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="📱 Мои устройства"),
                    KeyboardButton(text="➕ Добавить VPN")
                ],
                [
                    KeyboardButton(text="📊 Статистика"),
                    KeyboardButton(text="❓ Помощь")
                ]
            ],
            resize_keyboard=True
        )
    else:
        # No keyboard for non-approved users
        return ReplyKeyboardRemove()


def get_devices_reply_keyboard() -> ReplyKeyboardMarkup:
    """Devices reply keyboard"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Добавить VPN"),
                KeyboardButton(text="❓ Помощь")
            ]
        ],
        resize_keyboard=True
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    """Remove reply keyboard"""
    return ReplyKeyboardRemove()
