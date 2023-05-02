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

        def build(self):
            pass

        def run(self):
            pass

        def solver(self):
            pass

        def files(self):
            pass


ETH
----------------------


Installing forge
^^^^^^^^^^^^^^^^

.. code::

    import halborn_ctf.shell as shell

    ...

        def build(self):
            shell.run('curl -L https://foundry.paradigm.xyz | bash', env={"FOUNDRY_DIR": '/usr'})
            shell.run('foundryup', env={"FOUNDRY_DIR": '/usr'})

    ...


Filtering
======================

Inline:

.. code::


    import halborn_ctf.network as network

    ...

        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST']
            },
        }

        ...

        def run(self):
            network.filters.json_rpc.filter_methods([], listen_port=8545, to_port=8546)


On the ``PATH_MAPPING``:


.. code::

    import halborn_ctf.network as network

    ...

        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST'],
                    'filter': {
                        'method': network.filters.json_rpc.filter_methods,
                        'args': [
                            ['evm_.*']
                        ],
                    }
            },
        }

With custom filter on the ``PATH_MAPPING``:

.. code::

    import halborn_ctf.network as network

    ...

        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST'],
                    'filter': {
                        'method': network.filters.run_script,
                        'args': [
                            ['filter.py']
                        ],
                        'kwargs': {
                            'context_argument': 0x1337
                        },
                    }
            },
        }