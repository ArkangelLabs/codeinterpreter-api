import asyncio
import json
from typing import List

from codeboxapi import CodeBox  # type: ignore
from langchain.schema import BaseChatMessageHistory
from langchain.schema.messages import BaseMessage, messages_from_dict, messages_to_dict


# TODO: This is probably not efficient, but it works for now.
class CodeBoxChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history that stores history inside the codebox.
    """

    def __init__(self, codebox: CodeBox):
        self.codebox = codebox

        name, content = "history.json", b"{}"
        if (loop := asyncio.get_event_loop()).is_running():
            loop.create_task(self.codebox.aupload(name, content))
        else:
            self.codebox.upload(name, content)

    @property
    def messages(self) -> List[BaseMessage]:  # type: ignore
        """Retrieve the messages from the codebox"""
        return (
            messages_from_dict(json.loads(file_content.decode("utf-8")))
            if (
                file_content := (
                    loop.run_until_complete(self.codebox.adownload("history.json"))
                    if (loop := asyncio.get_event_loop()).is_running()
                    else self.codebox.download("history.json")
                ).content
            )
            else []
        )

    def add_message(self, message: BaseMessage) -> None:
        """Append the message to the record in the local file"""
        messages = messages_to_dict(self.messages)
        messages.append(messages_to_dict([message])[0])
        name, content = "history.json", json.dumps(messages).encode("utf-8")
        if (loop := asyncio.get_event_loop()).is_running():
            loop.create_task(self.codebox.aupload(name, content))
        else:
            self.codebox.upload(name, content)

    def clear(self) -> None:
        """Clear session memory from the local file"""
        code = "import os; os.remove('history.json')"
        if (loop := asyncio.get_event_loop()).is_running():
            loop.create_task(self.codebox.arun(code))
        else:
            self.codebox.run(code)
