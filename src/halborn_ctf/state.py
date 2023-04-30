
class State(dict):
    """Wrapper around dictionary for easier access and storage

    This class is not intended to be used directly but from templates members

    Example:
        The class allows to create dictionaries that can be accessed like this::

            state = State()
            state.value = 1337
            print(state.value) # 1337

    Args:
        dict (dict): Extending from dictionary
    """
    def __getattr__(self, key):
        return self.get(key, None)

    def __setattr__(self, key, value):
        super().__setitem__(key, value)