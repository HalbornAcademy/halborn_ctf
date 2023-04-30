from ._json_rpc import whitelist_json_rpc_method
from ._json_rpc import filter_json_rpc_method

from  ._utils import run_script

def whitelist_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    """Allows whitelisting a JSON RPC method from a given list

    If the method is not whitelisted the following data will be send::

        {
            "jsonrpc": "2.0",
            "id": json_dump['id'],
            "error": {
                "code":-32601,
                "message":"Method not allowed"
            }
        }

    Args:
        listen_port (_type_): _description_
        to_port (_type_): _description_
        methods (list, optional): _description_. Defaults to [].
        to_host (str, optional): _description_. Defaults to '127.0.0.1'.
    """
    run_script(whitelist_json_rpc_method.__file__, **locals())

def filter_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    run_script(filter_json_rpc_method.__file__, **locals())

__all__ = [
    'whitelist_methods',
    'filter_methods'
]