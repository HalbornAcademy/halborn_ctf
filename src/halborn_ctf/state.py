
class State(dict):
    def __getattr__(self, key):
        return self.get(key, None)

    def __setattr__(self, key, value):
        super().__setitem__(key, value)