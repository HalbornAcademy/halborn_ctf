"""
Filters module provide an easy way to restrict functionality to an exposed server on the challenge box.

All filters are using ``mitmdump`` from ``mitmproxy`` underneath to execute an script to filter the traffic to a given port.
To do the filtering, the command should expose a different port were the standard requests will flow in. None-filtered responses will
be forwarded to the specified upstream server on each of the filters.

Example:
    We can run ``anvil`` on the background and have a network filter for specific JSON-RPC methods::

        ...

        # Have port 8545 be exposed on the root of the challenge
        self.path_mapping = {
            '/': {
                    'port': 8545,
                    'path': '/',
                    'methods': ['POST']
            },
        }

        ...

        # Expose anvil to an internal port that will is not being exposed
        shell.run('anvil -p 9999')
        network.filters.json_rpc.filter_methods(['evm_*'], listen_port=8545, to_port=9999)

        # We can also use the whitelist variant to only allow those methods
        # network.filters.json_rpc.whitelist_methods(['net_*', 'eth_*'...], listen_port=8545, to_port=9999)

It is possible to also define your own filters (which can later be exposed to the player for reference) by either referencing the current 
implementations or the official documentation (https://2qwesgdhjuiytyrjhtgdbf.readthedocs.io/en/latest/scripting/inlinescripts.html).

Example:
    Once the script is created it can be executed using :class:`run_script`::

        run_script('./filter.py', listen_port=8545, to_port=9999, custom='More data')
        ...
        # The script can access the extra **kwargs using ``ctx.options.[kwargname]`` and JSON decoding it
        custom_data = json.loads(ctx.options.custom)

"""
from . import json_rpc
from ._utils import run_script

__all__ = [
    'run_script'
]