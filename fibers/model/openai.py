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
model_list = [normal_model, expensive_model]


def _complete_chat(chat: Chat, options=None):
    options = options or {}
    _options = {**options, "model": normal_model}
    return openai.ChatCompletion.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


def _complete_chat_expensive(chat: Chat, options=None):
    options = options or {}
    _options = {**options, "model": expensive_model}
    return openai.ChatCompletion.create(
        messages=chat.get_log_list(), **_options).choices[
        0].message.content


"""
## Embedding
"""

def _get_embeddings(texts, options):
    options = {**options, "model": "text-embedding-ada-002"}
    return openai.Embedding.create(input=texts, **options)["data"]


