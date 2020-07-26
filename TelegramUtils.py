import requests
import os


class TelegramUtils():
    """
    Contains function related to telegram usage.
    """

    def __init__(self):
        self.bot_token = os.getenv('bot_token')
        self.bot_chatID = os.getenv('chat_id')

    def send_message(self, message):
        send_text = 'https://api.telegram.org/bot' + self.bot_token + '/sendMessage?chat_id=' + \
            self.bot_chatID + '&parse_mode=MarkdownV2&text=' + message
        response = requests.get(send_text)