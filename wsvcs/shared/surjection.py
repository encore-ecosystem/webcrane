class Surjection:
    def __init__(self):
        self.key_2_val = {}
        self.val_2_key = {}

    def __getitem__(self, item):
        if item in self.key_2_val:
            return self.key_2_val[item]
        if item in self.val_2_key:
            return self.val_2_key[item]
        raise KeyError(f"There is no such element as {item}")

    def get(self, item, default=None):
        try:
            return self[item]
        except KeyError:
            return default

    def add_dict_as_key2val(self, d: dict):
        for k, v in d.items():
            self.key_2_val[k] = v
            self.val_2_key[v] = k

    def add_dict_as_val2key(self, d: dict):
        for k, v in d.items():
            self.key_2_val[v] = k
            self.val_2_key[k] = v

    def from_keys(self):
        return self.key_2_val.keys()

    def to_keys(self):
        return self.val_2_key.keys()

    def __len__(self):
        return len(self.key_2_val)

    def __contains__(self, item):
        return item in self.key_2_val or item in self.val_2_key


__all__ = ["Surjection"]
