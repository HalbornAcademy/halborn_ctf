def _merge(source, destination, exists_only=True):
    """

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if exists_only:
            if key not in destination:
                raise ValueError(f"Only existing keys can be merged, missing: {key}")
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, State({}))
            _merge(value, node, exists_only=exists_only)
        else:
            destination[key] = value

    return destination

class State(dict):
    """Wrapper around dictionary for easier access and storage

    This class is not intended to be used directly but from templates members

    Example:
        The class allows to create dictionaries that can be accessed like this::

            state = State({
                'value': 0,
                'extra': {
                    'more': 'initial'
                }
            })

            state.value = 1337
            state.extra.more = 'data'

            print(state.value) # 1337
            print(state.extra.more) # data


            state.newvalue = 0
            # ValueError: Key "newvalue" not found
    Raises:
        ValueError: If the key is not declared during initialization and a value is stored to it.

    Args:
        dict (dict): Extending from dictionary
    """

    def __init__(self, *args, **kw):
        _dict = args[0]
        for k in _dict.keys():
            if type(_dict[k]) == dict:
                _dict[k] = State(_dict[k])
        super(State,self).__init__(_dict)

    def __getattr__(self, key):
        if key not in self:
            raise ValueError(f'Key "{key}" not found')
        return self.get(key)

    # def __setitem__(self, key, value):
    #     super().__setitem__(key, value)
        # raise NotImplementedError()

    # def __getitem__(self, key):
    #     raise NotImplementedError()

    def __setattr__(self, key, value):
        if key not in self:
            raise ValueError(f'Key "{key}" not found')
        super().__setitem__(key, value)

    def _setattr(self, key, value):
        super().__setitem__(key, value)

    def _merge(self, source):
        _merge(source, self, exists_only=False)

    def udpate(self, source):
        """ Does allow updating an state recursively with another dictionary

        Note:
            All keys from the ``source`` must exist on the state.

        Raises:
            ValueError: If the key is not found on the state

        Example:
            It allows updating the current state with another dictionary::

                state = State({
                    'test': 'hi',
                    'public': {
                        'more': {
                            'test': 'hi'
                            }
                        }
                })

                print(state)
                # {'test': 'hi', 'public': {'more': {'test': 'hi'}}}

                state.update({
                    'test': 'change',
                    'public': {
                        'more': {
                            'test': 'bye'
                        }
                    }
                })

                print(state)
                # {'test': 'change', 'public': {'more': {'test': 'bye'}}}

        Args:
            source (dict): The dictionary to update with
        """
        _merge(source, self, exists_only=True)