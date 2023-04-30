from ._json_rpc import whitelist_json_rpc_method
from ._json_rpc import filter_json_rpc_method

from  ._utils import run_script

def whitelist_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    """Proxy filter that allows whitelisting JSON RPC methods

    The proxy will expose a service that will be listening on ``listen_port`` and redirect
    all traffic to ``to_host:to_port``.

    Each request will be checked for a valid method and if the method is not whitelisted 
    the following data will be send::

        {
            "jsonrpc": "2.0",
            "id": json_dump['id'],
            "error": {
                "code":-32601,
                "message":"Method not allowed"
            }
        }

    Example:

        The ``methods`` parameter does support regex on each of the elements::

            # Allowing all methods starting with `eth_` and `net_`
            whitelist_methods(["eth_.*", "net_.*"], listen_port=8545, to_port=8546)

    Args:
        methods (list, optional): A list of methods to whitelist. Each element of the 
            list does support regex expressions to match multiple patterns. Example: ``["eth_.*"]``. Defaults to [].
        listen_port (int): The port that will expose the proxy filter server 
        to_port (int): The port that all traffic will be redirected to 
        to_host (str, optional): The host that all traffic will be redirected to. Defaults to '127.0.0.1'.
    """
    run_script(whitelist_json_rpc_method.__file__, **locals())

def filter_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    """Proxy filter that allows filtering JSON RPC method

    The proxy will expose a service that will be listening on ``listen_port`` and redirect
    all traffic to ``to_host:to_port``.

    Each request will be checked for a valid method and if the method is on the filter list 
    the following data will be send::

        {
            "jsonrpc": "2.0",
            "id": json_dump['id'],
            "error": {
                "code":-32601,
                "message":"Method not allowed"
            }
        }

    Example:

        The ``methods`` parameter does support regex on each of the elements::

            # Disable all methods starting with `anvil_` and `evm_`
            filter_methods(["anvil_.*", "evm_.*"], listen_port=8545, to_port=8546)

    Args:
        methods (list, optional): A list of methods to filter. Each element of the 
            list does support regex expressions to match multiple patterns. Example: ``["evm_.*"]``. Defaults to [].
        listen_port (int): The port that will expose the proxy filter server 
        to_port (int): The port that all traffic will be redirected to 
        to_host (str, optional): The host that all traffic will be redirected to. Defaults to '127.0.0.1'.
    """
    run_script(filter_json_rpc_method.__file__, **locals())

__all__ = [
    'whitelist_methods',
    'filter_methods'
]