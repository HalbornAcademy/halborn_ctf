"""
This is the CLI module exposing a system command named ``halborn_ctf`` that helps
running template extended challenges (:obj:`halborn_ctf.templates.GenericChallenge`).

The entry point for the CLI command is the :obj:`run` function.
"""

import argparse
import logging
import sys
import os
import docker

from halborn_ctf import __version__
from halborn_ctf.generator import generate

__author__ = "ferran.celades"
__copyright__ = "ferran.celades"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

# ---- CLI ----
# The functions defined in this section are wrappers around the main Python
# API allowing them to be called directly from the terminal as a CLI
# executable/script.


def _parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parent_parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration", add_help=False)
    parent_parser.add_argument("-c", "--class", help="The name of the class in the file to use", default="Challenge", metavar='class')
    # parent_parser.add_argument('--local', action='store_true', help="Runs the challenge locally instead of a container")
    parent_parser.add_argument("-f", "--file", help="File path", default="./challenge.py")
    parent_parser.add_argument('--verbose', '-v', action='count', default=0, help="Level of verbosity")

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='method', help='Methods', required=True)

    local_parser = subparsers.add_parser('local', help='Runs the challenge locally', parents=[parent_parser])

    run_parser = subparsers.add_parser('run', help='Runs the challenge', parents=[parent_parser])

    build_parser = subparsers.add_parser('build', help='Builds the challenge', parents=[parent_parser])
    build_parser.add_argument('--no-cache', action='store_true', help='Ignores the docker build cache')

    init_parser = subparsers.add_parser('init', help='Allows to use challenge templates', parents=[parent_parser])
    init_parser.add_argument('-t',"--template", help="The name of the template to use", default="generic")

    parser.add_argument(
        "--version",
        action="version",
        version=f"halborn_ctf {__version__}",
    )

    return parser.parse_args(args)


def _setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    # logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logformat = "%(asctime)s | %(name)s | %(funcName)s | %(levelname)s | %(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(list_args):
    """Wrapper allowing any method to be called on a given module/class provided via arguments in a CLI fashion

    Args:
      list_args (List[str]): command line parameters as list of strings.

    """
    args = _parse_args(list_args)

    if args.method == 'init':
        if os.listdir('.'):
            print('Folder not empty')
        else:
            generate(args.template)
    elif args.method == 'local':

            abs_path = os.path.abspath(args.file)
            module_name = os.path.splitext(os.path.basename(abs_path))[0]
            module_path = os.path.dirname(abs_path)

            sys.path.append(module_path)

            module = __import__(module_name)

            _cls = getattr(module, getattr(args, 'class'))

            levels = [
                (logging.WARNING, 'WARNING'),
                (logging.INFO, 'INFO'),
                (logging.DEBUG, 'DEBUG')
            ]

            _level,_level_name = levels[min(args.verbose, len(levels) - 1)]

            _setup_logging(_level)
            _logger.warning('============================')
            _logger.warning('Logging level: {}'.format(_level_name))
            _logger.warning('============================')

            # Initiation challenge
            c = _cls()

            # _method = getattr(c, '_'+args.method)
            _run_method = getattr(c, '_run')

            # Initiation method
            _run_method()
    else:
        IMAGE_NAME = 'ctf-local'
        client = docker.from_env()
        if args.method == 'build':
            b = client.api.build(path='.', tag=IMAGE_NAME, quiet=False, decode=True, nocache=args.no_cache)
            for line in b:
                if 'error' in line:
                    print(line['error'], end='')
                elif 'stream' in line:
                    print(line['stream'], end='')
                else:
                    print(line)
        elif args.method == 'run':
            # Kill old container
            for container in client.containers.list():
                if container.attrs['Config']['Image'] == IMAGE_NAME:
                    container.kill()
            _container = client.containers.run(IMAGE_NAME, ports={'8080': '8080'}, detach=True, stderr=True, command=list_args + ['--local'])
            try:
                for line in _container.logs(stream=True):
                    print(line.decode('utf-8'), end='')
            except:
                _container.kill()


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`.

    This function can be used as entry point for the ``halborn_ctf`` challenges.

    The allowed flags are:

        - ``[METHOD]``: The method to execute. Only 'build' and 'run' are allowed. Valids are ``build, run``.
        - ``-f/--file``: The file where the class/function is present. Defaults to ``"./challenge.py"``.
        - ``-c/--class``: The class where the method is found. Defaults to ``"Challenge"``.
        - ``-v``: Verbose (INFO).
        - ``-vv``: Verbose (DEBUG).

    Example:
        Executing method ``run`` from the ``challenge.py`` file and the class named ``Challenge`` in debug mode::

            halborn_ctf run -vv

        Executing method ``build`` from the ``file.py`` file and the class named ``ChallengeCustom``::

            halborn_ctf build -f file.py -c ChallengeCustom

    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m halborn_ctf.cli 42
    #
    run()
