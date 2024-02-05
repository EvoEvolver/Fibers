import os

if os.getenv("OPENAI_API_KEY") is None:
    print("You must set environment variable OPENAI_API_KEY before use")
    raise Exception("OPENAI_API_KEY is not set")