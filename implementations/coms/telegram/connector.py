"""TelegramConnector — scaffold (not yet implemented).

To implement: use the Telegram Bot API (https://core.telegram.org/bots/api).
Requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID env vars.
"""

from core.interfaces.communicator import CommunicatorInterface
from core.models import NotificationPayload


class TelegramConnector(CommunicatorInterface):
    def send(self, payload: NotificationPayload) -> str:
        raise NotImplementedError("TelegramConnector is not yet implemented")
