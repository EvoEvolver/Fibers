from __future__ import annotations

import base64
import copy
from io import BytesIO

from PIL.Image import Image

from fibers.debug.logger import Logger
from fibers.gui.dictionary_viewer import show_document_with_key_gui
from fibers.helper.cache.cache_service import enable_auto_cache
from fibers.model.openai import (_complete_chat as openai_complete_chat,
                                 _complete_chat_expensive as openai_complete_chat_expensive,
                                 model_list as openai_model_list)
from fibers.model.openllm import (complete_chat as openllm_complete_chat,
                                  complete_chat_expensive as openllm_complete_chat_expensive)


def encode_image(image_file: BytesIO):
    return base64.b64encode(image_file.read()).decode('utf-8')


class ChatLogger(Logger):
    active_loggers = []

    def display_log(self):
        contents = [str(chat) for chat in self.log_list]
        filenames = [caller_name.split("/")[-1] for caller_name in self.caller_list]
        show_document_with_key_gui(filenames, contents)


class Chat:
    """
    Class for chat completion
    """

    def __init__(self, user_message=None, system_message: any = None):
        self.history = []
        self.system_message = system_message
        if user_message is not None:
            self._add_message(user_message, "user")

    """
    ## Message editing and output
    """

    def _add_message(self, content: any, role: str):
        self.history.append({
            "content": content,
            "role": role
        })

    def _add_image_message(self, url: str, detail: str):
        self.history.append({
            "role": "user",
            "content": [{
                "type": "image_url",
                "image_url": {
                    "url": url,
                    "detail": detail}
                }]
        })

    def add_user_message(self, content: any):
        self._add_message(content, "user")

    def add_image_message(self, image_path: str, from_internet=False, detail="auto"):
        """
        :param from_internet: Whether the path is a url
        :param image_path: The path of the image
        :param detail: Low or high fidelity image understanding ("auto", "low", "high")
        """
        if not from_internet:
            with open(image_path, "rb") as image_file:
                base64_image = encode_image(image_file)
            url = f"data:image/jpeg;base64,{base64_image}"
        else:
            url = image_path
        self._add_image_message(url, detail)

    def add_image_message_by_obj(self, image: Image, detail="auto"):
        buffered = BytesIO()
        image.save(buffered, format="png")
        base64_image = base64.b64encode(buffered.getvalue()).decode('utf-8')
        url = f"data:image/jpeg;base64,{base64_image}"
        self._add_image_message(url, detail)

    def add_assistant_message(self, content: any):
        self._add_message(content, "assistant")

    def get_log_list(self):
        """
        :return: chat log for sending to the OpenAI API
        """
        res = []
        if self.system_message is not None:
            res.append({
                "content": str(self.system_message),
                "role": "system"
            })
        for message in self.history:
            res.append(message)
        return res

    """
    ## Chat completion functions
    """

    def complete_chat(self, options=None):
        cache = enable_auto_cache(self.get_log_list(), "chat")
        if cache is not None and cache.is_valid():
            self.add_assistant_message(cache.value)
            return cache.value

        options = options or {}
        if use_openai_model(options):
            res = openai_complete_chat(self, options=options)
        else:
            res = openllm_complete_chat(self, options=options)

        if len(ChatLogger.active_loggers) > 0:
            for chat_logger in ChatLogger.active_loggers:
                chat_logger.add_log(self)
        self.add_assistant_message(res)

        if cache is not None:
            cache.set_cache(res)

        return res

    def complete_chat_expensive(self, options=None):
        cache = enable_auto_cache(self.get_log_list(), "chat")
        if cache is not None and cache.is_valid():
            self.add_assistant_message(cache.value)
            return cache.value

        options = options or {}
        if use_openai_model(options):
            res = openai_complete_chat_expensive(self, options=options)
        else:
            res = openllm_complete_chat_expensive(self, options=options)

        if len(ChatLogger.active_loggers) > 0:
            for chat_logger in ChatLogger.active_loggers:
                chat_logger.add_log(self)
        self.add_assistant_message(res)

        if cache is not None:
            cache.set_cache(res)
        return res

    """
    ## Magic methods
    """

    def __str__(self):
        res = []
        log_list = self.get_log_list()
        for entry in log_list:
            res.append(f"------{entry['role']}------\n {entry['content']}")
        return "\n".join(res)

    def __repr__(self):
        return f"<{self.__class__.__name__}> {self.system_message!r}"

    def __copy__(self):
        new_chat_log = Chat(system_message=self.system_message)
        new_chat_log.history = copy.deepcopy(self.history)
        return new_chat_log


def use_openai_model(options) -> bool:
    return options.get("model", "gpt-3.5-turbo") in openai_model_list


def reduce_multiple_new_lines(text: str) -> str:
    """
    If there are more than two new lines, reduce them to two.
    """
    texts = text.split("\n")
    res = []
    for i, line in enumerate(texts):
        if i > 0 and len(line) == 0 and len(texts[i - 1]) == 0:
            continue
        res.append(line)
    return "\n".join(res)

