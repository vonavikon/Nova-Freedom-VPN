"""
Admin Handlers for Nova VPN Bot - Hiddify Version
Handles user approval and management
"""

import logging
import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def escape_md(text: str) -> str:
    """Escape Markdown v1 special characters for safe display."""
    for ch in ('\\', '`', '*', '_'):
        text = text.replace(ch, f'\\{ch}')
    return text

from ..services.user_service import UserService
from ..services.notification_service import NotificationService
from ..database import Database, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from ..keyboards import (
    get_approval_keyboard,
    get_pending_users_keyboard,
    get_pending_user_actions_keyboard
)

logger = logging.getLogger(__name__)
router = Router()

# Video tutorial file_id storage
VIDEO_FILE_ID_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'video_tutorial_file_id.txt')


def save_video_file_id(file_id: str):
    os.makedirs(os.path.dirname(VIDEO_FILE_ID_PATH), exist_ok=True)
    with open(VIDEO_FILE_ID_PATH, 'w') as f:
        f.write(file_id)


def get_video_file_id() -> str:
    try:
        with open(VIDEO_FILE_ID_PATH, 'r') as f:
            return f.read().strip()
    except FileNotFoundError:
        return ""


# ========== ADMIN CHECK ==========

def is_admin(user_id: int, admin_ids: list) -> bool:
    """Check if user is admin"""
    return user_id in admin_ids


# ========== ADMIN KEYBOARD ==========

def get_admin_keyboard(pending_count: int = 0) -> InlineKeyboardMarkup:
    """Admin menu keyboard"""
    pending_label = f"⏳ Ожидающие ({pending_count})" if pending_count else "⏳ Ожидающие"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=pending_label, callback_data="admin_pending"),
            InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="🚫 Отклонённые", callback_data="admin_rejected"),
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="🔙 В меню", callback_data="main_menu")
        ]
    ])


def get_user_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Keyboard for user management"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"admin_delete_user_{user_id}"),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")
        ]
    ])


# ========== FSM STATES ==========

class BroadcastStates(StatesGroup):
    waiting_for_message = State()


# ========== COMMAND HANDLERS ==========

@router.message(F.text == "/admin")
async def cmd_admin(message: Message, db: Database, user_service: UserService):
    """Open admin panel"""

    import bot.config as config

    if not is_admin(message.from_user.id, config.ADMIN_IDS):
        await message.answer("❌ Доступ запрещён")
        return

    stats = db.get_stats() if hasattr(db, 'get_stats') else {}
    pending = stats.get('pending_users', 0)

    await message.answer(
        "🔧 **Админ-панель Nova VPN**\n\n"
        f"✅ Активных: {stats.get('approved_users', 0)}\n"
        f"⏳ Ожидают: {pending}\n"
        f"🚫 Отклонено: {stats.get('rejected_users', 0)}\n"
        f"📱 Устройств: {stats.get('total_devices', 0)}\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(pending)
    )


# ========== CALLBACK HANDLERS ==========

@router.callback_query(F.data == "admin_menu")
async def cb_admin_menu(callback: CallbackQuery, db: Database):
    """Show admin menu"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    stats = db.get_stats() if hasattr(db, 'get_stats') else {}
    pending = stats.get('pending_users', 0)

    await callback.message.edit_text(
        "🔧 **Админ-панель Nova VPN**\n\n"
        f"✅ Активных: {stats.get('approved_users', 0)}\n"
        f"⏳ Ожидают: {pending}\n"
        f"🚫 Отклонено: {stats.get('rejected_users', 0)}\n"
        f"📱 Устройств: {stats.get('total_devices', 0)}\n\n"
        "Выберите действие:",
        reply_markup=get_admin_keyboard(pending)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_pending")
async def cb_admin_pending(callback: CallbackQuery, db: Database):
    """Show pending users"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    pending_users = db.get_pending_users() if hasattr(db, 'get_pending_users') else []

    if not pending_users:
        await callback.message.edit_text(
            "⏳ **Ожидающие одобрения**\n\nНет пользователей, ожидающих одобрения.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    text = f"⏳ **Ожидающие одобрения ({len(pending_users)}):**"
    await callback.message.edit_text(
        text,
        reply_markup=get_pending_users_keyboard(pending_users)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_rejected")
async def cb_admin_rejected(callback: CallbackQuery, db: Database):
    """Show rejected users"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    users = db.get_all_users() if hasattr(db, 'get_all_users') else []
    rejected = [u for u in users if u.get('status') == STATUS_REJECTED]

    if not rejected:
        await callback.message.edit_text(
            "🚫 **Отклонённые**\n\nНет отклонённых пользователей.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    buttons = []
    for user in rejected[:20]:
        username = f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown')
        buttons.append([
            InlineKeyboardButton(
                text=f"🚫 {username}",
                callback_data=f"pending_user_{user['id']}"
            )
        ])
    buttons.append([
        InlineKeyboardButton(text="🔙 В админ-меню", callback_data="admin_menu")
    ])

    await callback.message.edit_text(
        f"🚫 **Отклонённые ({len(rejected)}):**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("pending_user_"))
async def cb_pending_user(callback: CallbackQuery, db: Database):
    """Show pending user details"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user_by_id(user_id) if hasattr(db, 'get_user_by_id') else None

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    username = escape_md(f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown'))

    text = f"""⏳ **Заявка на доступ**

👤 Пользователь: {username}
🆔 Telegram ID: `{user.get('telegram_id', 'N/A')}`
📝 Имя: {escape_md(user.get('first_name', 'Не указано'))}
📅 Дата: {user.get('created_at', 'N/A')}

Одобрить или отклонить?"""

    await callback.message.edit_text(
        text,
        reply_markup=get_pending_user_actions_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("approve_user_"))
async def cb_approve_user(callback: CallbackQuery, db: Database, user_service: UserService):
    """Approve user"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user_by_id(user_id) if hasattr(db, 'get_user_by_id') else None

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    telegram_id = user['telegram_id']

    # Approve user
    success = user_service.approve_user(telegram_id)

    if success:
        username = escape_md(f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown'))

        # Notify user
        notification = NotificationService(callback.bot, config.ADMIN_IDS)
        await notification.notify_user_approved(telegram_id)

        await callback.message.edit_text(
            f"✅ **Пользователь одобрен**\n\n👤 {username}\n🆔 `{telegram_id}`\n\nПользователь получил уведомление.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer("✅ Пользователь одобрен")
    else:
        await callback.answer("❌ Ошибка при одобрении", show_alert=True)


@router.callback_query(F.data.startswith("reject_user_"))
async def cb_reject_user(callback: CallbackQuery, db: Database, user_service: UserService):
    """Reject user"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user_by_id(user_id) if hasattr(db, 'get_user_by_id') else None

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    telegram_id = user['telegram_id']

    # Reject user
    success = user_service.reject_user(telegram_id)

    if success:
        username = escape_md(f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown'))

        # Notify user
        notification = NotificationService(callback.bot, config.ADMIN_IDS)
        await notification.notify_user_rejected(telegram_id)

        await callback.message.edit_text(
            f"❌ **Пользователь отклонён**\n\n👤 {username}\n🆔 `{telegram_id}`\n\nПользователь получил уведомление.",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer("❌ Пользователь отклонён")
    else:
        await callback.answer("❌ Ошибка при отклонении", show_alert=True)


@router.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: CallbackQuery, db: Database):
    """Show all approved users"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    users = db.get_all_users() if hasattr(db, 'get_all_users') else []

    if not users:
        await callback.message.edit_text(
            "👥 **Пользователи**\n\nНет пользователей",
            reply_markup=get_admin_keyboard()
        )
        await callback.answer()
        return

    # Filter only approved users
    approved_users = [u for u in users if u.get('status') == STATUS_APPROVED]

    buttons = []
    for user in approved_users[:20]:
        username = f"@{user['username']}" if user.get('username') else user.get('first_name', 'Unknown')
        devices = db.get_user_devices(user['id']) if hasattr(db, 'get_user_devices') else []
        button_text = f"👤 {username} ({len(devices)} устройств)"
        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"admin_user_{user['id']}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")
    ])

    await callback.message.edit_text(
        f"👥 **Одобренные пользователи ({len(approved_users)}):**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_user_"))
async def cb_admin_user(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show user details"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split("_")[2])
    user = db.get_user_by_id(user_id) if hasattr(db, 'get_user_by_id') else None

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    devices = db.get_user_devices(user_id) if hasattr(db, 'get_user_devices') else []
    username = escape_md(f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown'))

    text = f"""👤 **Пользователь**

👤 Имя: {username}
🆔 Telegram ID: `{user.get('telegram_id', 'N/A')}`
📊 Статус: {escape_md(user.get('status', 'N/A'))}
📱 Устройств: {len(devices)}
"""

    if devices:
        text += "\n**Устройства:**\n"
        for device in devices:
            text += f"  📱 {device['device_name']} (hiddify)\n"

    await callback.message.edit_text(
        text,
        reply_markup=get_user_management_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_user_"))
async def cb_admin_delete_user(callback: CallbackQuery, db: Database, user_service: UserService):
    """Delete user and all devices"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    user_id = int(callback.data.split("_")[3])
    user = db.get_user_by_id(user_id) if hasattr(db, 'get_user_by_id') else None

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    username = escape_md(f"@{user.get('username')}" if user.get('username') else user.get('first_name', 'Unknown'))

    # Delete all devices first
    devices = db.get_user_devices(user_id) if hasattr(db, 'get_user_devices') else []
    for device in devices:
        try:
            await user_service.delete_device(user['telegram_id'], device['id'])
        except Exception as e:
            logger.error(f"Failed to delete device: {e}")

    # Delete user from database
    if hasattr(db, 'delete_user'):
        db.delete_user(user_id)

    await callback.message.edit_text(
        f"✅ Пользователь **{username}** удалён\n\nВсе устройства отозваны.",
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: CallbackQuery, db: Database):
    """Show statistics"""

    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    stats = db.get_stats() if hasattr(db, 'get_stats') else {}
    pending = stats.get('pending_users', 0)

    text = f"""📊 **Статистика Nova VPN**

👥 Пользователи:
   ✅ Активных: {stats.get('approved_users', 0)}
   ⏳ Ожидают: {pending}
   🚫 Отклонено: {stats.get('rejected_users', 0)}
   Всего заявок: {stats.get('total_users', 0)}

📱 Устройства:
   Всего: {stats.get('total_devices', 0)}
   Протокол: VLESS Reality

🚀 Протокол: VLESS Reality"""

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_keyboard(pending)
    )
    await callback.answer()


# ========== VIDEO TUTORIAL ==========

@router.message(F.video)
async def admin_set_video(message: Message):
    """Admin sends video to set as tutorial"""

    import bot.config as config

    if not is_admin(message.from_user.id, config.ADMIN_IDS):
        return

    file_id = message.video.file_id
    save_video_file_id(file_id)

    await message.answer(
        f"✅ **Видео инструкция обновлена**\n\n`file_id`: `{file_id}`\n\nТеперь оно будет показываться в разделе Помощь.",
        parse_mode="Markdown"
    )


# ========== BROADCAST ==========

@router.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: CallbackQuery, state: FSMContext, db: Database):
    """Start broadcast flow"""
    import bot.config as config

    if not is_admin(callback.from_user.id, config.ADMIN_IDS):
        await callback.answer("❌ Доступ запрещён", show_alert=True)
        return

    users = db.get_all_users() if hasattr(db, 'get_all_users') else []
    approved = [u for u in users if u.get('status') == STATUS_APPROVED]

    await state.set_state(BroadcastStates.waiting_for_message)
    await callback.message.edit_text(
        f"📢 **Рассылка**\n\nПолучателей: {len(approved)}\n\nОтправьте сообщение для рассылки (текст, фото или видео):",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_menu")]
        ])
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_for_message)
async def msg_broadcast(message: Message, state: FSMContext, db: Database):
    """Send broadcast message to all approved users"""
    import bot.config as config

    if not is_admin(message.from_user.id, config.ADMIN_IDS):
        return

    await state.clear()

    users = db.get_all_users() if hasattr(db, 'get_all_users') else []
    approved = [u for u in users if u.get('status') == STATUS_APPROVED]

    sent = 0
    failed = 0

    status_msg = await message.answer(f"⏳ Рассылка... 0/{len(approved)}")

    for user in approved:
        telegram_id = user.get('telegram_id')
        if not telegram_id:
            failed += 1
            continue
        try:
            await message.copy_to(telegram_id)
            sent += 1
        except Exception as e:
            logger.warning(f"Broadcast failed for {telegram_id}: {e}")
            failed += 1

    await status_msg.delete()
    await message.answer(
        f"✅ **Рассылка завершена**\n\n📤 Отправлено: {sent}\n❌ Ошибок: {failed}",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )