from ...shell import run as _run
import json

def run_script(script, listen_port, to_port, to_host, **kwargs):

    # The double escape is for the cli to handle it as part as the --set definition (ex method="[\"data\"]")
    set_args = ' '.join(['--set {0}={1}'.format(k, json.dumps(json.dumps(v))) for k,v in kwargs.items()])

    cmd = f'mitmdump -s {script} --mode upstream:http://{to_host}:{to_port} -p {listen_port} {set_args}'
    _run(cmd, background=True)
