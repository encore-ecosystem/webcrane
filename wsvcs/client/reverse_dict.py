def reverse_dict(d: dict):
    result = {}
    for key, value in d.items():
        result[value] = key
    return result
