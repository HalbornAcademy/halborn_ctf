from ...shell import run as _run
import json

def generic_filter(filter_file, **kwargs):
    """Allows running an arbitrary ``mitmdump`` script as a background shell process.

    The ``mitmdump`` will be used in ``upstream`` mode. Any extra arguments provided to the ``generic_filter`` will be
    transfered to the ``script`` using the ``--set`` command flag on the command line of mitmdump
    as JSON encoded string which can be accessed on the script using ``mitmproxy.ctx.options.[varname]``.

    https://docs.mitmproxy.org/stable/addons-examples/

    Example:
        Once the script is created it can be used on using :class:`generic_filter`::

            generic_filter('./filter.py', my_args=[], extra_custom='more')
            ...
            # The script can access the extra **kwargs using ``ctx.options.[varname]`` and JSON decoding it
            custom_data = json.loads(ctx.options.[varname])

    Args:
        script (str): Path of the script to execute
        **kwargs: Any extra arguments that the filter script needs
    """
    def _wrapper(listen_port, to_port, to_host='127.0.0.1'):
        set_args = ' '.join(['--set {0}={1}'.format(k, json.dumps(json.dumps(v))) for k,v in kwargs.items()])

        cmd = f'mitmdump -s {filter_file} --mode upstream:http://{to_host}:{to_port} -p {listen_port} {set_args}'
        _run(cmd, background=True)

    return _wrapper

# def generic_filter(script, listen_port, to_port, to_host='127.0.0.1', **kwargs):

#     # The double escape is for the cli to handle it as part as the --set definition (ex method="[\"data\"]")
#     set_args = ' '.join(['--set {0}={1}'.format(k, json.dumps(json.dumps(v))) for k,v in kwargs.items()])

#     cmd = f'mitmdump -s {script} --mode upstream:http://{to_host}:{to_port} -p {listen_port} {set_args}'
#     _run(cmd, background=True)
