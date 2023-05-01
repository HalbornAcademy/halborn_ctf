from ...shell import run as _run
import json

def run_script(script, listen_port, to_port, to_host='127.0.0.1', **kwargs):
    """Allows running an arbitrary ``mitmdump`` script as a background shell process.

    The ``mitmdump`` will be used in ``upstream`` mode against ``http://{to_host}:{to_port}`` 
    and listen under ``listen_port``. Any extra arguments provided to the ``run_script`` will be 
    transfered to the ``script`` using the ``--set`` command flag on the command line of mitmdump 
    as JSON encoded string which can be accessed on the script using ``mitmproxy.ctx.options.[varname]``.

    Example:
        Once the script is created it can be executed using :class:`run_script`::

            run_script('./filter.py', listen_port=8545, to_port=9999, custom='More data')
            ...
            # The script can access the extra **kwargs using ``ctx.options.[kwargname]`` and JSON decoding it
            custom_data = json.loads(ctx.options.custom)

    Args:
        script (str): Path of the script to execute
        listen_port (int): Port that mitmdump will listen on
        to_port (int): The upstream port to proxy traffic to
        to_host (str): The upstream host to proxy traffic to. Defaults to '127.0.0.1'.
    """

    # The double escape is for the cli to handle it as part as the --set definition (ex method="[\"data\"]")
    set_args = ' '.join(['--set {0}={1}'.format(k, json.dumps(json.dumps(v))) for k,v in kwargs.items()])

    cmd = f'mitmdump -s {script} --mode upstream:http://{to_host}:{to_port} -p {listen_port} {set_args}'
    _run(cmd, background=True)
