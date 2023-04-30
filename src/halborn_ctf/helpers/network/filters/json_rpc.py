from ._json_rpc import whitelist_json_rpc_method
from ._json_rpc import filter_json_rpc_method

from  ._utils import run_script

def whitelist_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    run_script(whitelist_json_rpc_method.__file__, **locals())

def filter_methods(methods=[], *, listen_port, to_port, to_host='127.0.0.1'):
    run_script(filter_json_rpc_method.__file__, **locals())

__all__ = [
    'whitelist_methods',
    'filter_methods'
]