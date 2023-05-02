"""
This is the CLI module exposing a system command named ``halborn_ctf`` that helps
running template extended challenges (:obj:`halborn_ctf.templates.GenericChallenge`).

The entry point for the CLI command is the :obj:`run` function.
"""

import argparse
import logging
import sys
import os

from halborn_ctf import __version__

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
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"halborn_ctf {__version__}",
    )
    parser.add_argument(dest="method", help="The method to run on the challenge", type=str, metavar="METHOD", choices=['build', 'run'])
    # parser.add_argument(dest="file", help="The file where the challenge is present", type=str, metavar="FILE")
    parser.add_argument("-c", "--class", help="Class name", default="Challenge", metavar='class')
    parser.add_argument("-f", "--file", help="File path", default="./challenge.py")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--debug",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
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


def main(args):
    """Wrapper allowing any method to be called on a given module/class provided via arguments in a CLI fashion

    Args:
      args (List[str]): command line parameters as list of strings.

    """
    args = _parse_args(args)
    abs_path = os.path.abspath(args.file)
    module_name = os.path.splitext(os.path.basename(abs_path))[0]
    module_path = os.path.dirname(abs_path)

    sys.path.append(module_path)

    module = __import__(module_name)

    _cls = getattr(module, getattr(args, 'class'))

    _setup_logging(args.loglevel)

    # Initiation challenge
    c = _cls()

    _method = getattr(c, '_'+args.method)

    # Initiation method
    _method()


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`.

    This function can be used as entry point for the ``halborn_ctf`` challenges.

    The allowed flags are:

        - ``[METHOD]``: The method to execute. Only 'build' and 'run' are allowed. Valids are ``build, run``.
        - ``-f/--file``: The file where the class/function is present. Defaults to ``"./challenge.py"``.
        - ``-c/--class``: The class where the method is found. Defaults to ``"Challenge"``.
        - ``-v/--verbose``: Verbose (INFO).
        - ``-vv/--debug``: Verbose (DEBUG).

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
