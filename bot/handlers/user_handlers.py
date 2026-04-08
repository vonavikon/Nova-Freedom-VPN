"""
User Handlers for Nova VPN Bot - Hiddify Version
"""

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..services.user_service import UserService
from ..services.notification_service import NotificationService
from ..database import Database, STATUS_PENDING, STATUS_APPROVED, STATUS_REJECTED
from ..keyboards import (
    get_main_keyboard,
    get_main_reply_keyboard,
    get_device_name_suggestions_keyboard,
    get_devices_keyboard,
    get_device_actions_keyboard,
    get_approval_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


# ========== FSM STATES ==========

class AddDeviceStates(StatesGroup):
    choosing_device_name = State()
    custom_device_name = State()


# ========== COMMAND HANDLERS ==========

@router.message(Command("start"))
async def cmd_start(message: Message, db: Database, user_service: UserService, notification_service: NotificationService):
    """Handle /start command"""

    # Check if user exists
    existing_user = user_service.get_user(message.from_user.id)
    is_new_user = existing_user is None

    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    status = user_service.get_user_status(message.from_user.id)

    # New user - send approval request to admins
    if is_new_user or status == STATUS_PENDING:
        # Notify admins about new user with approval buttons
        keyboard = get_approval_keyboard(user['id'])
        await notification_service.notify_new_user_pending(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            reply_markup=keyboard
        )

        await message.answer(
            f"""👋 Приветствую, {message.from_user.first_name}!

Это сервис **Nova Freedom VPN**, с помощью него, ты сможешь получить доступ к недоступным сервисам.

⏳ **Заявка отправлена на рассмотрение**

Ваш запрос на доступ отправлен администратору.
Как только доступ будет одобрен, вы получите уведомление.

Пожалуйста, ожидайте.""",
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard(has_access=False)
        )
        return

    # Rejected user
    if status == STATUS_REJECTED:
        await message.answer(
            f"""👋 Привет, {message.from_user.first_name}!

❌ **Доступ отклонён**

К сожалению, ваша заявка на доступ была отклонена.""",
            parse_mode="Markdown",
            reply_markup=get_main_reply_keyboard(has_access=False)
        )
        return

    # Approved user
    device_count = user_service.get_device_count(message.from_user.id)

    from ..texts import CLIENT_LINKS, VIDEO_TUTORIAL_URL

    video_section = f"\n\n🎬 **Видео инструкция:**\n{VIDEO_TUTORIAL_URL}\n" if VIDEO_TUTORIAL_URL else ""

    welcome_text = f"""👋 Привет, {message.from_user.first_name}!

🚀 **Nova Freedom VPN**

Устройств: {device_count}/3

✅ **Доступ разрешён**

**Для каких целей можно использовать сервис:**
  • Мессенджеры, сайты, почта
  • YouTube, Netflix, Spotify
  • Работа из дома

**Не разрешено:**
  • Торренты
  • Пиратский контент
  • Нелегальная деятельность
{video_section}"""

    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_reply_keyboard(has_access=True)
    )


@router.message(Command("help"))
async def cmd_help(message: Message, db: Database, user_service: UserService):
    """Handle /help command"""

    from ..texts import format_help_full
    from .admin_handlers import get_video_file_id

    text = format_help_full()
    video_id = get_video_file_id()

    if video_id:
        await message.answer_video(video=video_id)
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(has_access=True),
        disable_web_page_preview=True
    )


@router.message(Command("myconfig"))
async def cmd_myconfig(message: Message, db: Database, user_service: UserService):
    """Show user devices"""

    devices = user_service.get_user_devices(message.from_user.id)

    if not devices:
        await message.answer(
            "У вас пока нет устройств.\n\nНажмите 'Добавить VPN' чтобы создать!",
            reply_markup=get_main_keyboard(has_access=True)
        )
        return

    text = f"**Ваши устройства ({len(devices)}/3):**"

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_devices_keyboard(devices)
    )


# ========== CALLBACK HANDLERS ==========

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show main menu"""

    device_count = user_service.get_device_count(callback.from_user.id)

    await callback.message.edit_text(
        f"**Главное меню**\n\nУстройств: {device_count}/3",
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(has_access=True)
    )
    await callback.answer()


@router.callback_query(F.data == "my_devices")
async def cb_my_devices(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show user devices"""

    devices = user_service.get_user_devices(callback.from_user.id)

    if not devices:
        await callback.message.edit_text(
            "У вас пока нет устройств.\n\nНажмите 'Добавить VPN' чтобы создать!",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard(has_access=True)
        )
        await callback.answer()
        return

    text = f"**Ваши устройства ({len(devices)}/3):**"

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_devices_keyboard(devices)
    )
    await callback.answer()


@router.callback_query(F.data == "add_device")
async def cb_add_device_start(callback: CallbackQuery, state: FSMContext, db: Database, user_service: UserService):
    """Start add device flow"""

    # Check device count
    count = user_service.get_device_count(callback.from_user.id)
    if count >= 3:
        await callback.answer("❌ Максимум 3 устройств", show_alert=True)
        return

    # Show device name suggestions
    await state.set_state(AddDeviceStates.choosing_device_name)

    await callback.message.edit_text(
        "**Выберите название устройства:**",
        parse_mode="Markdown",
        reply_markup=get_device_name_suggestions_keyboard()
    )
    await callback.answer()


@router.callback_query(AddDeviceStates.choosing_device_name, F.data.startswith("device_name_"))
async def cb_device_name_selected(callback: CallbackQuery, state: FSMContext, db: Database, user_service: UserService):
    """Handle device name selection"""

    if callback.data == "device_name_custom":
        await state.set_state(AddDeviceStates.custom_device_name)
        await callback.message.edit_text(
            "**Введите название устройства:**\n\nМаксимум 20 символов.",
            parse_mode="Markdown"
        )
        await callback.answer()
        return

    device_name = callback.data.replace("device_name_", "")
    await _create_device(callback, state, db, user_service, device_name)


@router.message(AddDeviceStates.custom_device_name)
async def msg_custom_device_name(message: Message, state: FSMContext, db: Database, user_service: UserService):
    """Handle custom device name input"""

    device_name = message.text.strip()

    if len(device_name) < 2 or len(device_name) > 20:
        await message.answer("❌ Название должно быть от 2 до 20 символов")
        return

    # Get or create user (fixes "User not found" error)
    user = await user_service.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    # Create device
    success, msg, device = await user_service.create_device(
        telegram_id=message.from_user.id,
        device_name=device_name,
        protocol="hiddify"
    )

    await state.clear()

    if success and device:
        await _show_device_created(message, device, user_service, user)
    else:
        await message.answer(f"❌ Ошибка: {msg}")


async def _create_device(callback: CallbackQuery, state: FSMContext, db: Database, user_service: UserService, device_name: str):
    """Create device helper"""

    # Get or create user (fixes "User not found" error)
    user = await user_service.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        last_name=callback.from_user.last_name
    )

    success, msg, device = await user_service.create_device(
        telegram_id=callback.from_user.id,
        device_name=device_name,
        protocol="hiddify"
    )

    await state.clear()

    if success and device:
        await _show_device_created(callback.message, device, user_service, user, is_callback=True)
        await callback.answer()
    else:
        await callback.message.edit_text(f"❌ Ошибка: {msg}")
        await callback.answer()


async def _show_device_created(message, device, user_service, user, is_callback=False):
    """Show device created message with config"""

    from ..texts import format_device_created

    config = device.get('config', '')
    sub_url = device.get('subscription_url')

    text = format_device_created(
        device_name=device['device_name'],
        usage_gb=device.get('usage_limit_gb', 100),
        package_days=device.get('package_days', 365),
        config=config,
        sub_url=sub_url
    )

    if is_callback:
        devices = user_service.get_user_devices(user['telegram_id'] if 'telegram_id' in user else user['id'])
        await message.edit_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_devices_keyboard(devices),
            disable_web_page_preview=True
        )
    else:
        await message.answer(
            text,
            parse_mode="Markdown",
            disable_web_page_preview=True
        )


@router.callback_query(F.data.startswith("device_"))
async def cb_device_actions(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show device actions"""

    from ..texts import format_device_info

    device_id = int(callback.data.split("_")[1])
    device = db.get_device(device_id)

    if not device:
        await callback.answer("Устройство не найдено", show_alert=True)
        return

    user = user_service.get_user(callback.from_user.id)
    if not user or device['user_id'] != user['id']:
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    # Get config from Hiddify
    success, config, sub_url = await user_service.get_device_config(callback.from_user.id, device_id)

    if not success:
        config = ''
        usage_gb = device.get('usage_limit_gb', 100)
        package_days = device.get('package_days', 365)
    else:
        usage_gb = device.get('usage_limit_gb', 100)
        package_days = device.get('package_days', 365)

    text = format_device_info(device['device_name'], device['id'], config, usage_gb, package_days, sub_url)

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_device_actions_keyboard(device['id'], device['device_name']),
        disable_web_page_preview=True
    )
    await callback.answer()


@router.callback_query(F.data.startswith("delete_device_"))
async def cb_delete_device_confirm(callback: CallbackQuery, db: Database, user_service: UserService):
    """Delete device"""

    device_id = int(callback.data.split("_")[2])
    device = db.get_device(device_id)

    if not device:
        await callback.answer("Устройство не найдено", show_alert=True)
        return

    user = user_service.get_user(callback.from_user.id)
    if not user or device['user_id'] != user['id']:
        await callback.answer("Доступ запрещён", show_alert=True)
        return

    # Delete device
    success, msg = await user_service.delete_device(callback.from_user.id, device_id)

    if success:
        devices = user_service.get_user_devices(callback.from_user.id)
        if devices:
            await callback.message.edit_text(
                f"✅ {msg}",
                reply_markup=get_devices_keyboard(devices)
            )
        else:
            await callback.message.edit_text(
                f"✅ {msg}\n\nУ вас больше нет устройств.",
                reply_markup=get_main_keyboard(has_access=True)
            )
    else:
        await callback.answer(f"❌ {msg}", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "cancel")
async def cb_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel current operation"""

    await state.clear()
    await callback.message.edit_text(
        "❌ Операция отменена",
        reply_markup=get_main_keyboard(has_access=True)
    )
    await callback.answer()


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show user statistics"""

    from ..texts import format_stats

    devices = user_service.get_user_devices(callback.from_user.id)

    text = format_stats(len(devices))

    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_main_keyboard(has_access=True)
    )
    await callback.answer()


@router.callback_query(F.data == "help")
async def cb_help(callback: CallbackQuery, db: Database, user_service: UserService):
    """Show help via inline button"""

    from ..texts import format_help_short
    from .admin_handlers import get_video_file_id

    text = format_help_short()
    video_id = get_video_file_id()

    if video_id:
        await callback.message.delete()
        await callback.message.answer_video(video=video_id)
        await callback.message.answer(
            text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(has_access=True),
            disable_web_page_preview=True
        )
    else:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=get_main_keyboard(has_access=True),
            disable_web_page_preview=True
        )
    await callback.answer()


# ========== REPLY KEYBOARD HANDLERS ==========

@router.message(F.text == "📱 Мои устройства")
async def btn_my_devices(message: Message, db: Database, user_service: UserService):
    """Handle 'My Devices' reply button"""

    devices = user_service.get_user_devices(message.from_user.id)

    if not devices:
        await message.answer(
            "У вас пока нет устройств.\n\nНажмите 'Добавить VPN' чтобы создать!",
            reply_markup=get_main_keyboard(has_access=True)
        )
        return

    text = f"**Ваши устройства ({len(devices)}/3):**"

    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_devices_keyboard(devices)
    )


@router.message(F.text == "➕ Добавить VPN")
async def btn_add_device(message: Message, state: FSMContext, db: Database, user_service: UserService):
    """Handle 'Add VPN' reply button"""

    count = user_service.get_device_count(message.from_user.id)
    if count >= 3:
        await message.answer("❌ Максимум 3 устройств")
        return

    await state.set_state(AddDeviceStates.choosing_device_name)

    await message.answer(
        "**Выберите название устройства:**",
        parse_mode="Markdown",
        reply_markup=get_device_name_suggestions_keyboard()
    )


@router.message(F.text == "📊 Статистика")
async def btn_stats(message: Message, db: Database, user_service: UserService):
    """Handle 'Statistics' reply button"""

    from ..texts import format_stats

    devices = user_service.get_user_devices(message.from_user.id)

    text = format_stats(len(devices))

    await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "❓ Помощь")
async def btn_help(message: Message, db: Database, user_service: UserService):
    """Handle 'Help' reply button"""

    from ..texts import format_help_full
    from .admin_handlers import get_video_file_id

    text = format_help_full()
    video_id = get_video_file_id()

    if video_id:
        await message.answer_video(video=video_id)
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(has_access=True),
        disable_web_page_preview=True
    )