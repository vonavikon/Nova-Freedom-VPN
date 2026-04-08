"""
Keyboards module for Nova VPN Bot - Hiddify Version
"""

from .inline import (
    get_main_keyboard,
    get_device_name_suggestions_keyboard,
    get_devices_keyboard,
    get_device_actions_keyboard,
    get_confirmation_keyboard,
    get_approval_keyboard,
    get_pending_users_keyboard,
    get_pending_user_actions_keyboard
)

from .reply import (
    get_main_reply_keyboard,
    get_devices_reply_keyboard,
    remove_keyboard
)

__all__ = [
    'get_main_keyboard',
    'get_device_name_suggestions_keyboard',
    'get_devices_keyboard',
    'get_device_actions_keyboard',
    'get_confirmation_keyboard',
    'get_approval_keyboard',
    'get_pending_users_keyboard',
    'get_pending_user_actions_keyboard',
    'get_main_reply_keyboard',
    'get_devices_reply_keyboard',
    'remove_keyboard'
]
