import subprocess
import logging
import threading

_logger = logging.getLogger(__name__)

def run(cmd: str, *, background=False, capture_output=False, **kwargs):
    """This is a function used to execute a given ``cmd`` on as a subprocess on a shell.

    An exam

    Example:
        Example of executing ``ls`` and getting the output and error::

            process, stdout, stderr = run("ls -la", capture_output=True)

            print(stdout)
            print(stderr)

        Example of installing ``forge`` in the ``/usr`` directory::

            run('curl -L https://foundry.paradigm.xyz | bash', env={"FOUNDRY_DIR": '/usr'})
            run('foundryup', env={"FOUNDRY_DIR": '/usr'})

        Example of executing ``anvil`` in the background as a none blocking process::

            run("anvil -p 8545", background_process=True)

    Args:
        cmd (str): The command to be executed. Keep in mind that the program being executed
            must be present on the ``PATH`` environment variable for the shell to find it.
            The default executed shell corresponds to the ``/bin/sh`` and there is not way to have
            awareness on ``.bashrc`` or any other ``.rc`` file unless manually loaded. If enviroment variables
            are required they can be provided through the ``**kwargs`` parameter that accepts the same arguments
            as :class:`subprocess.Popen`

        background (bool, optional): If set it will run the program on the background and will not wait for its
            execution to finish. Defaults to False.
        capture_output (bool, optional): If set it will capture the command output and return it from the function
            as a decoded string. This flag can not be set at the same time as ``background``. Defaults to False.

    Raises:
        ValueError: If both ``background`` and ``capture_output`` are set this error is raised.
        AttributeError: If any argument that is internally used to spawn :class:`subprocess.Popen`
            is specified on the ``kwargs``, this error is raised.


    Returns:
        tuple:

        - process: (:class:`subprocess.Popen`)
            The process opened, you can use all methods of the ``popen-objects``.
        - stdout: (str or None)
            A decoded string of the ``stdout`` of the executed process. Only if ``capture_output`` is set to ``True``. Otherwise ``None`` is returned
        - stderr: (str or None)
            A decoded string of the ``stderr`` of the executed process. Only if ``capture_output`` is set to ``True``. Otherwise ``None`` is returned
    """


    if background and capture_output:
        raise ValueError("Not possible to run process on the background and capture output")

    _invalid_kwargs = ['shell', 'args', 'stdout', 'stderr']
    for _tag in _invalid_kwargs:
        if _tag in kwargs:
            raise AttributeError(f"You cannot use kwarg named: {_tag}")

    _logger.info('Running CMD "{}" (background: {})'.format(cmd, background))

    def shell_run_pipe(pipe, log):
        for line in pipe:
            log(line.rstrip().decode("utf-8"))

    proc = subprocess.Popen(
        args=cmd,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
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