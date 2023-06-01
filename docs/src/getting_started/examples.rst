.. _examples:

=========
Examples
=========

Web3
======================

Minimal template:

.. code::

    from halborn_ctf.templates import Web3Challenge

    class Challenge(Web3Challenge):

        CHALLENGE_NAME = 'MY CHALLENGE'

        PATH_MAPPING = {
        }

        # optional
        def build(self):
            pass

        def run(self):
            pass

        def solver(self):
            pass

        def files(self):
            pass


Filtering
======================

On the ``PATH_MAPPING``:


.. code::

    import halborn_ctf.network.filters as filters

    ...

        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST'],
                    'filter': filters.json_rpc.whitelist_methods(['evm_.*']),
            },
        }

With custom filter on the ``PATH_MAPPING``:

.. code::

    import halborn_ctf.network.filters as filters

    ...

        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST'],
                    'filter': filters.generic_filter('filter_file.py', my_arg=[], extra='more'),
            },
        }