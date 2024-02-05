from __future__ import annotations

import os
from typing import TYPE_CHECKING

import openai
from openai import OpenAI

openai_api_key = os.getenv("OPENAI_API_KEY")

if openai_api_key is None:
    print("You must set environment variable OPENAI_API_KEY before use")
    raise Exception("OPENAI_API_KEY is not set")
else:
    client = OpenAI(
        # This is the default and can be omitted
        api_key=openai_api_key,
    )

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
    return client.chat.completions.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


def _complete_chat_expensive(chat: Chat, options=None):
    options = options or {}
    _options = {**options, **default_options, "model": expensive_model}
    return client.chat.completions.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


"""
## Embedding
"""

def _get_embeddings(texts, options):
    options = {**options, "model": "text-embedding-ada-002"}
    return openai.embeddings.create(input=texts, **options).data


