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