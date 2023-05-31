from ._json_rpc import whitelist_json_rpc_method
from ._json_rpc import filter_json_rpc_method

from  ._utils import generic_filter

def whitelist_methods(methods=[]):
    """Proxy filter that allows whitelisting JSON RPC methods

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
            whitelist_methods(["eth_.*", "net_.*"])

    Args:
        methods (list, optional): A list of methods to whitelist. Each element of the 
            list does support regex expressions to match multiple patterns. Example: ``["eth_.*"]``. Defaults to [].
    """
    return generic_filter(whitelist_json_rpc_method.__file__, **locals())

def filter_methods(methods=[]):
    """Proxy filter that allows filtering JSON RPC method

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
            filter_methods(["anvil_.*", "evm_.*"])

    Args:
        methods (list, optional): A list of methods to filter. Each element of the 
            list does support regex expressions to match multiple patterns. Example: ``["evm_.*"]``. Defaults to [].
    """
    return generic_filter(filter_json_rpc_method.__file__, **locals())

__all__ = [
    'whitelist_methods',
    'filter_methods'
]