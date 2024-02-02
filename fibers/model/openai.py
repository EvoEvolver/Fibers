from __future__ import annotations

from typing import TYPE_CHECKING

import openai

verbose = 1

if TYPE_CHECKING:
    from fibers.model.chat import Chat

"""
## Chat completion
"""

normal_model = "gpt-3.5-turbo"
expensive_model = "gpt-4"
vision_model = "gpt-4-vision-preview"
model_list = [normal_model, expensive_model, vision_model]

default_options = {
    "temperature": 0.7,
    "timeout": 15,
}

def contains_image(chat: Chat):
    for message in chat.history:
        content = message["content"]
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item["type"] == "image_url":
                    return True
        elif isinstance(content, dict):
            if content["type"] == "image_url":
                return True
    return False

def _complete_chat(chat: Chat, options=None):
    options = options or {}
    _options = {"model": normal_model, **options, **default_options}
    if contains_image(chat):
        _options["model"] = "gpt-4-vision-preview"
        _options["max_tokens"] = 2000
    return openai.ChatCompletion.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


def _complete_chat_expensive(chat: Chat, options=None):
    options = options or {}
    _options = {**options, **default_options, "model": expensive_model}
    return openai.ChatCompletion.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


"""
## Embedding
"""

def _get_embeddings(texts, options):
    options = {**options, "model": "text-embedding-ada-002"}
    return openai.Embedding.create(input=texts, **options)["data"]


