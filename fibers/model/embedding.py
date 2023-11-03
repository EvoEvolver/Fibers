from __future__ import annotations

import hashlib
from typing import List

import numpy as np

from fibers.helper.cache.cache_service import cache_service
from fibers.model.openai import _get_embeddings

model_for_embedding = "text-embedding-ada-002"
model_to_embedding_dim = {
    "text-embedding-ada-002": 1536
}


def flatten_nested_list(texts: list[list[str]]) -> (List[float], List[int]):
    flattened_texts = []
    index_start = []
    for i, texts_ in enumerate(texts):
        index_start.append(len(flattened_texts))
        flattened_texts.extend(texts_)
    return flattened_texts, index_start


def get_embeddings(texts: list[str]) -> list[list[float]]:
    embedding_dim_using = model_to_embedding_dim[model_for_embedding]

    cache_table = cache_service.cache_embed.load_cache_table(model_for_embedding)
    hash_keys = [hashlib.md5(text.encode()).hexdigest() for text in texts]

    embeddings = []
    index_for_eval = []
    texts_without_cache = []
    for i, text in enumerate(texts):
        if len(text) == 0:
            embeddings.append(np.zeros(embedding_dim_using))
            continue
        if hash_keys[i] not in cache_table:
            texts_without_cache.append(text)
            embeddings.append(None)
            index_for_eval.append(i)
        else:
            embeddings.append(cache_table[hash_keys[i]])
    if len(texts_without_cache) > 0:
        try:
            res = _get_embeddings(texts_without_cache, {"model": model_for_embedding})
        except Exception as e:
            print(e)
            print(texts_without_cache)
            raise e
        res = [r["embedding"] for r in res]
        print(f"{len(res)} embeddings generated")
        for i, r in zip(index_for_eval, res):
            cache_table[hash_keys[i]] = r
            embeddings[i] = r

    return embeddings
