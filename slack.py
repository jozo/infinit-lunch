import json
from datetime import datetime


class Channel:
    """
    Represents one channel on a Slack team
    """

    def __init__(self, hook: str, http) -> None:
        self.hook = hook
        self.http = http

    def send(self, messages: list):
        for msg in messages:
            self.http.post(self.hook, data=json.dumps({'text': msg}))


class LunchAwareChannel(Channel):
    """
    Add proper formatting to messages to represents lunches
    """

    def send(self, messages: list):
        self.add_header_to(messages[0])
        super().send(messages)

    def add_header_to(self, message: str):
        return """*MENU {}*
        
        {}
        """.format(datetime.today().isoformat()[:10], message)