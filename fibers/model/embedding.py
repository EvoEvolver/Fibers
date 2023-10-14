from __future__ import annotations

import hashlib
import os
from typing import List

import numpy as np

from fibers.model.openai import _get_embeddings

model_for_embedding = "text-embedding-ada-002"
embedding_cache_path = os.getcwd() + "/embedding.ec.npy"
model_to_embedding_dim = {
    "text-embedding-ada-002": 1536
}


embedding_cache = None


def flatten_nested_list(texts: list[list[str]]) -> (List[float], List[int]):
    flattened_texts = []
    index_start = []
    for i, texts_ in enumerate(texts):
        index_start.append(len(flattened_texts))
        flattened_texts.extend(texts_)
    return flattened_texts, index_start


def get_embeddings(texts: list[str], make_cache=True) -> list[list[float]]:
    global embedding_cache
    if embedding_cache is None:
        if os.path.exists(embedding_cache_path):
            embedding_cache = np.load("embedding.ec.npy", allow_pickle=True).item()
        else:
            embedding_cache = {}

    embedding_dim_using = model_to_embedding_dim[model_for_embedding]

    hash_keys = [hashlib.md5(text.encode()).hexdigest() for text in texts]
    embeddings = []
    index_for_eval = []
    texts_without_cache = []
    for i, text in enumerate(texts):
        if len(text) == 0:
            embeddings.append(np.zeros(embedding_dim_using))
            continue
        if hash_keys[i] not in embedding_cache:
            texts_without_cache.append(text)
            embeddings.append(None)
            index_for_eval.append(i)
        else:
            embeddings.append(embedding_cache[hash_keys[i]])
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
            embedding_cache[hash_keys[i]] = r
            embeddings[i] = r

    if make_cache:
        np.save(embedding_cache_path, embedding_cache)

    return embeddings
