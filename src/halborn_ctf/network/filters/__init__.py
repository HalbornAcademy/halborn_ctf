"""
Filters module provide an easy way to restrict functionality to an exposed server on the challenge box.

All filters are using ``mitmdump`` from ``mitmproxy`` underneath to execute an script to filter the traffic to a given port.
To do the filtering, the command should expose a different port were the standard requests will flow in. None-filtered responses will
be forwarded to the specified upstream server on each of the filters.

Example:
    We can run ``anvil`` on the background and have a network filter for specific JSON-RPC methods::

        ...

        # Have port 8545 be exposed on the root of the challenge
        PATH_MAPPING = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST'],
                    'filter': network.filters.json_rpc.whitelist_methods(['net_*', 'eth_*'...])
            },
        }

        ...

        shell.run('anvil -p 8545')

It is possible to also define your own filters (which can later be exposed to the player for reference) by either referencing the current
implementations or the official documentation (https://2qwesgdhjuiytyrjhtgdbf.readthedocs.io/en/latest/scripting/inlinescripts.html) and examples (https://docs.mitmproxy.org/stable/addons-examples/).

Example:
    Once the script is created it can be used using :class:`generic_filter`::

        generic_filter('./filter.py', my_args=[], extra_custom='more')
        ...
        # The script can access the extra **kwargs using ``ctx.options.[varname]`` and JSON decoding it
        custom_data = json.loads(ctx.options.[varname])

Tip:
    You can use the current ``challenge.py`` as the container for the filter without having to create a separated file by using python built-in ``__file__``::

        generic_filter(__file__, my_args=[], extra_custom='more')

"""
from . import json_rpc
from ._utils import generic_filter

__all__ = [
    'generic_filter'
]