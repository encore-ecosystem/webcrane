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

    def __len__(self):
        return len(self.key_2_val)

    def __contains__(self, item):
        return item in self.key_2_val or item in self.val_2_key


__all__ = ["Surjection"]
