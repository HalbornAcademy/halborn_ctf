import subprocess
import logging
import threading

_logger = logging.getLogger(__name__)

def run(cmd, *args, background=False, capture_output=False, **kwargs):
    if background and capture_output:
        raise ValueError("Not possible to run process on the background and capture output")

    _logger.info('Running CMD "{}" (background: {})'.format(cmd, background))

    def shell_run_pipe(pipe, log):
        for line in pipe:
            log(line.rstrip().decode("utf-8"))

    proc = subprocess.Popen(
        args=cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        *args,
        **kwargs
    )

    # If we don't capture the output, we will have 2 threads printing
    # stdout and stderr
    if not capture_output:
        out_thread = threading.Thread(target=shell_run_pipe, args=(proc.stdout, _logger.info), daemon=True)
        err_thread = threading.Thread(target=shell_run_pipe, args=(proc.stderr, _logger.error), daemon=True)
        out_thread.start()
        err_thread.start()

    # If its a background process, return process
    if background:
        return proc, None, None
    else:
        # If its not a background process, we always wait for the process to finish
        # If we capture the output, return it. Otherwise, wait for pipe threads
        proc.wait()
        if not capture_output:
            out_thread.join()
            err_thread.join()
        return (proc, proc.stdout.read().rstrip().decode("utf-8"), proc.stderr.read().rstrip().decode("utf-8"))