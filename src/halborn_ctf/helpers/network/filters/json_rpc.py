from halborn_ctf.helpers.shell import run as _run

def whitelist_rpc_methods(methods, listen_port, proxy_port):
    _run(f'mitmdump -s filter.py --mode upstream:http://127.0.0.1:{proxy_port} -p {listen_port} --set methods="{",".join(methods)}"', background=True)

def filter_rpc_methods(methods, listen_port, proxy_port):
    _run(f'mitmdump -s filter.py --mode upstream:http://127.0.0.1:{proxy_port} -p {listen_port} --set methods="{",".join(methods)}"', background=True)


__all__ = [
    'whitelist_rpc_methods',
    'filter_rpc_methods'
]