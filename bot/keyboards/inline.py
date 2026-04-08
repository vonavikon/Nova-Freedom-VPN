"""
Inline Keyboards for Nova VPN Bot
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard(has_access: bool = True) -> InlineKeyboardMarkup:
    """Main menu inline keyboard"""
    if has_access:
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 Мои устройства", callback_data="my_devices"),
                InlineKeyboardButton(text="➕ Добавить VPN", callback_data="add_device")
            ],
            [
                InlineKeyboardButton(text="📊 Статистика", callback_data="stats"),
                InlineKeyboardButton(text="❓ Помощь", callback_data="help")
            ]
        ])
    else:
        # No buttons for non-approved users
        return InlineKeyboardMarkup(inline_keyboard=[])


def get_device_name_suggestions_keyboard() -> InlineKeyboardMarkup:
    """Device name suggestions keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📱 iPhone", callback_data="device_name_iPhone"),
            InlineKeyboardButton(text="📱 Android", callback_data="device_name_Android")
        ],
        [
            InlineKeyboardButton(text="💻 MacBook", callback_data="device_name_MacBook"),
            InlineKeyboardButton(text="💻 Windows", callback_data="device_name_Windows")
        ],
        [
            InlineKeyboardButton(text="🖥️ PC", callback_data="device_name_PC"),
            InlineKeyboardButton(text="📱 iPad", callback_data="device_name_iPad")
        ],
        [
            InlineKeyboardButton(text="✏️ Свое название", callback_data="device_name_custom")
        ],
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
        ]
    ])


def get_devices_keyboard(devices: list) -> InlineKeyboardMarkup:
    """Devices list keyboard"""
    buttons = []
    for device in devices:
        buttons.append([
            InlineKeyboardButton(
                text=f"📱 {device['device_name']}",
                callback_data=f"device_{device['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="➕ Добавить устройство", callback_data="add_device"),
        InlineKeyboardButton(text="🔙 Меню", callback_data="main_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_device_actions_keyboard(device_id: int, device_name: str) -> InlineKeyboardMarkup:
    """Device actions keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_device_{device_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="my_devices")
        ]
    ])


def get_confirmation_keyboard(action: str, item_id: int) -> InlineKeyboardMarkup:
    """Confirmation keyboard"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_{action}_{item_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="cancel")
        ]
    ])


def get_approval_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard for admin to approve/reject new user"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_user_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_user_{user_id}")
        ]
    ])


def get_pending_users_keyboard(users: list) -> InlineKeyboardMarkup:
    """Keyboard with list of pending users"""
    buttons = []
    for user in users:
        username = f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown')
        buttons.append([
            InlineKeyboardButton(
                text=f"⏳ {username}",
                callback_data=f"pending_user_{user['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 В админ-меню", callback_data="admin_menu")
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pending_user_actions_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard for managing pending user"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Одобрить", callback_data=f"approve_user_{user_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"reject_user_{user_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 К списку", callback_data="admin_pending")
        ]
    ])
