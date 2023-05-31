"""Templates to create CTF challenges.

Creating a challenge consists on the following steps:

- Pick a template from this module to use. If undecided use the :obj:`ChallengeGeneric` and configure it by reading the documentation.
- Create a class extending the template and implement the abstract methods::

    # challenge.py
    class Challenge(ChallengeGeneric):

        def build(self):
            pass

        def run(self):
            pass

- Test the template by using the ``halborn_ctf`` CLI (:obj:`halborn_ctf.cli.run`)::

    halborn_ctf run -vv

- Server can be accessed under ``localhost:8080`` by default.

"""
from dataclasses import dataclass
import logging
import flask
from flask_cors import CORS
from flask import Response, request
import requests
import os
import zipfile
import sys
from io import BytesIO
import glob
import pickle
import signal
from urllib.parse import urljoin
from typing import TypedDict, NotRequired, Callable
from enum import Enum
from textwrap import dedent

from .state import State

from abc import ABC, abstractmethod

from .network import find_free_port

# https://stackoverflow.com/questions/320232/ensuring-subprocesses-are-dead-on-exiting-python-program
class _CleanChildProcesses:
  def __enter__(self):
    logging.info("pid=%d  pgid=%d" % (os.getpid(), os.getpgid(0)))

    try:
        os.setpgrp() # create new process group, become its leader
    except:
        pass
        # ERRORS
        #    EPERM  The  process group ID of any process equals the PID of the call-
        #           ing process.  Thus, in particular, setsid() fails if the calling
        #           process is already a process group leader.

  def __exit__(self, type, value, traceback):
    logging.info('Killing all processes')

    try:
      os.killpg(0, signal.SIGINT) # kill all processes in my group
    except KeyboardInterrupt:
      # SIGINT is delievered to this process as well as the child processes.
      # Ignore it so that the existing exception, if any, is returned. This
      # leaves us with a clean exit code if there was no exception.
      pass

class MappingInfo(TypedDict):
    """Dictionary data type to store the details for a path mapping
    """

    port: int
    """ (int): The port to redirect to.
    """
    host: NotRequired[str]
    """ (str, optional): The host to redirect to. Defaults to ``'127.0.0.1'``.
    """
    path: NotRequired[str]
    """ (str, optional): The path to redirect to. Defaults to ``'/'``.
    """
    methods: list[str]
    """ (list[str], optional): The allowed methods. Defaults to ``["GET"]``.
    """
    filter: Callable
    """ (Callable, optional): One of the valid built-in filters or a generic_filter function. 
    """

class FlagType(Enum):
    NONE = 0
    """If no flag is present
    """
    STATIC = 1
    """If the flag is statically defined or embedded into the challenge somewhere.
    """
    DYNAMIC = 2
    """When the challenge is deployed a ``FLAG`` environment variable will be set.
    """

@dataclass
class StrFile():
    """It allows to create a container for temporary generated files from strings. It can be used on the
    :obj:`GenericChallenge.HAS_FILES` to add on-the fly files:

    Example::

        from halborn_ctf.templates import StrFile

        def files(self):
            return [
                StrFile('folder/test.txt', 'THIS IS THE CONTENT')
            ]

    """
    filepath: str
    content: str

class GenericChallenge(ABC):
    """Generic CTF challenge template

    Each created/deployed challenge does have two steps defined, :obj:`build` and :obj:`run`. The ``build`` step is only executed once
    when the challenge is created and uploaded into the platform for playing. The ``run`` step is always executed for each player request
    to deploy a new challenge.

    This template does also expose the challenge by using an HTTP server. The server does allow registering routes to it by using
    the :obj:`PATH_MAPPING` attribute.

    An attribute named :obj:`state` can be used to store any sort of object that will persiste between the ``build`` and ``run`` steps. Furthermore,
    this attribute can be used to store anything that would be used across the different functions. The `state_public` property will be exposed
    under the `/info` path on the challenge domain.

    The following routes will be exposed under ``localhost:8080``:

    - ``/info``: Does contain general info of the challenge such as :obj:`ready` and :obj:`state_public`.
    - ``/solved``: Does execute the "solver" function and display if the challenge was solved together with a solved message or hint to the player.

    Note:
        Only if :attr:`HAS_SOLVER` == ``True``.

    - ``/files``: Does download the files listed under the "files" function as a zip file named by :attr:`CHALLENGE_NAME`.

    Note:
        Only if :attr:`HAS_FILES` == ``True``.

    """

    CHALLENGE_NAME = 'challenge'
    """ (str): The name of the challenge.
    """

    FLAG_TYPE = FlagType.NONE
    """ (FlagType): The type of flag. Set to :obj:`FlagType.NONE` if using a solver unless using manual flag input on the CTF platform.
    """

    HAS_FILES = False
    """ (bool): If the challenge has downloadable files. A "files" function must be defined returning a list of files that
    will be downloable from the challenge container. Glob patterns can be used (:mod:`glob`)::

        def files(self):
            return [
                "filter.py",
                "folder/test.sol",
                "folder2/**",
                "folder3/*.sol",
            ]

    Tip:
        You can also create virtual files from strings using :obj:`StrFile`.

    Note:
        Each time the user request the `/files` route a zip archive with all of the listed files will be downloaded.
    """

    HAS_SOLVER = False
    """
    (bool): If the challenge has a solver. The required function "solver" should be present. Although it is possible
    to have periodic functions (:obj:`periodic`) that set the :obj:`solved`.
    You can keep the method defined like this if the latter is being used::

        def solver(self):
            pass

    Note:
        This function will be executed each time the user requests the ``/solved`` route.
    """

    HAS_DETAILS = False
    """
    (bool): If the challenge has dynamic or specific implementation details. The required function "details" should be present.
    This function must return a string. You can format the string using any ``state`` variable or any dynamic content (for example a file content).

    The string does support ``Markdown`` syntax and will be displayed on the platform UI and under the ``/info`` route

    Example::

        DETAILS_TEMPLATE = '''
        This is a detailed description of the challenge:

        You will require:

        - This
        - That

        You can also check: {custom_value}

        Don't forget: {extra}

        Helper:

        ``` python
        def helper():
            pass
        ```
        '''

        ...

        def __init__(self):
            super().__init__()

            self.state = {
                'custom_value': 0x1337
            }


        def details(self):
            return DETAILS_TEMPLATE.format(
                **self.state,
                **{
                    'extra': "Extra info"
                }
            )

    Note:
        This function will be executed each time the user requests the ``/info`` route.
    """

    PATH_MAPPING: dict[str, MappingInfo] = {}
    """
    (dict[str, MappingInfo]): Mapping used internally to register the challenge URL's paths.
    It does contain a mapping of ``path`` to ``MappingInfo`` dictionary details.

    Example:
        Have the challenge ``/`` path expose the anvil service which is running internally on port ``8545``::

            PATH_MAPPING = {
                '/': {
                        'host': '127.0.0.1', # optional. Defaults to '127.0.0.1'
                        'port': 8545,
                        'path': '/', # optional. Defaults to '/'
                        'methods': ['POST'] # optional. Defaults to ['GET']
                }
            }

        A request to http://challenge/ will be proxied to http://127.0.0.1:8545/

        Redirect all request to the service running on port ``9999`` and under ``/service``::

            PATH_MAPPING = {
                '/<path:path>': {
                        'port': 9999,
                        'path': '/service',
                        'methods': ['GET', 'POST', 'HEAD']
                }
            }

        A request to http://challenge/my_path/file will be proxied to http://127.0.0.1:9999/service/my_path/file. But not http://challenge/.

        It allows to use filters::

            PATH_MAPPING = {
                '/': {
                        'port': 8545,
                        'path': '/',
                        'methods': ['POST'],
                        'filter': network.filters.json_rpc.whitelist_methods(['evm_.*']),
                }
            }

    Note:
        There is no need to specify any of the required field for the filter such as ``listen_port``, ``to_port``, ``to_host`` as those will
        be extracted from the mapping itself and a random listening port used and remapped.
    """

    def _check_feature_enabled(self, feature_name, required_function):
        if getattr(self, feature_name):
            try:
                getattr(self, required_function)
            except:
                raise NotImplementedError(f'Missing function "{required_function}" ({feature_name} == True)')

            self._challenge_config[feature_name] = True
        else:
            try:
                getattr(self, required_function)
                raise NotImplementedError(f'Remove "{required_function}" function ({feature_name} == False)')
            except:
                pass

            self._challenge_config[feature_name] = False


    def __init__(self) -> None:
        super().__init__()

        self._app = flask.Flask('Challenge')
        self.log = logging.getLogger(self.CHALLENGE_NAME)

        CORS(self._app)

        self._ready = False
        self._state_set = False
        self._state = State({})
        self._state_public_set = False
        self._state_public = State({})

        self._challenge_config = {}
        self._challenge_config['FLAG_TYPE'] = self.FLAG_TYPE.name

        if self.HAS_SOLVER:
            self._solved = False
            self._solved_msg = None
            # self._state._setattr('solved', False)
            # self._state._setattr('solved_msg', None)

        self._check_feature_enabled('HAS_FILES', 'files')
        self._check_feature_enabled('HAS_SOLVER', 'solver')
        self._check_feature_enabled('HAS_DETAILS', 'details')

        if not self.HAS_SOLVER and self.FLAG_TYPE == FlagType.NONE:
            raise ValueError("HAS_SOLVER == False and FLAG_TYPE == NONE")

    # @property
    # def ready(self):
    #     """(bool): Allows setting the challenge as ready to be played.

    #         Example::

    #             def run(self):
    #                 ...
    #                 self.ready = True

    #     """
    #     return self._ready

    # @ready.setter
    # def ready(self, value):
    #     # if self._ready:
    #     #     raise ValueError('Challenge ready already')
    #     self._ready = value

    @property
    def solved(self):
        """(bool): Returns and allows to set if the challenge is solved or not. Only functional if :obj:`HAS_SOLVER` is set.

            Example::

                def solver(self):
                    ...
                    self.solved = True

        """

        if not self.HAS_SOLVER:
            raise ValueError('Challenge !HAS_SOLVER')
        return self._solved

    @solved.setter
    def solved(self, value):
        if not self.HAS_SOLVER:
            raise ValueError('Challenge !HAS_SOLVER')
        self._solved = value

    @property
    def solved_msg(self):
        """(str): Returns and allows to set a message or hint for the player. Only functional if :obj:`HAS_SOLVER` is set.
            Example::

                def solver(self):
                    ...
                    if self.solved:
                        self.solved_msg = "You are the best hacker!"
                    else:
                        self.solved_msg = "Keep trying :("

        """

        if not self.HAS_SOLVER:
            raise ValueError('Challenge !HAS_SOLVER')

    @solved_msg.setter
    def solved_msg(self, value):
        if not self.HAS_SOLVER:
            raise ValueError('Challenge !HAS_SOLVER')
        self._solved_msg = value

    @property
    def state(self):
        """(State): Extended dictionary to store variables that can be accessed during challenge execution.

        The challenge :obj:`build` step will pickle this variable for the :obj:`run` method to have the same state.

        Example:
            Initializing the state::

                self.state = {
                    'custom': 'Initial value'
                }

            Updating the state value::

                self.state.custom = 'Changed value'

            Reading an state value::

                print(self.state.custom)
                # Changed value

        """
        if not self._state_set:
            raise ValueError("State not initialized")
        return self._state

    @state.setter
    def state(self, value):
        if self._state_set:
            raise ValueError("State already set, use state.update instead")
        self._state._merge(value)
        # self._state = State(value)
        self._state_set = True

    @property
    def state_public(self):
        """(State): It will expose the state content into the challenge ``/info`` route. Refer to :obj:`state`.
        """
        if not self._state_public_set:
            raise ValueError("State not initialized")
        return self._state_public

    @state_public.setter
    def state_public(self, value):
        if self._state_public_set:
            raise ValueError("State already set, use state_public.update instead")
        self._state_public._merge(value)
        # self._state_public_set = State(value)
        self._state_public_set = True

    def _app_info_handler(self):
        # if not self._ready:
        #     return Response("Challenge not ready", status=503)

        _mapping: dict[str, MappingInfo] = {}
        for k,v in self.PATH_MAPPING.items():
            _mapping[k] = {
                'port': v.get('port'),
                'host': v.get('host', '127.0.0.1'),
                'path': v.get('path', '/'),
                'methods': v.get('methods', ['GET']),
                # 'filter': _filter
            }

        _return = {
            'ready': self._ready,
            'state': self._state_public,
            'config': self._challenge_config,
            'mapping': _mapping
        }

        if self.HAS_DETAILS:
            _return['details'] = dedent(self.details()).strip()
        else:
            _return['details'] = None

        return _return

    def _app_files_handler(self):
        if not self._ready:
            return Response("Challenge not ready", status=503)

        name = self.CHALLENGE_NAME.replace(' ','_')

        fileName = f"{name}.zip"
        files = self.files() + ['challenge.py', 'Dockerfile']

        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for _added in files:
                if type(_added) == StrFile:
                    zipf.writestr(_added.filepath, _added.content)
                else:
                    for result in glob.glob(_added):
                        zipf.write(result)

        memory_file.seek(0)
        return flask.send_file(memory_file,
                        download_name=fileName,
                        as_attachment=True)

    def _app_solved_handler(self):
        if not self._ready:
            return Response("Challenge not ready", status=503)

        # If not solved, we check on the solver
        if not self.solved:
            try:
                self.solver()
            except Exception as e:
                self.log.exception(e)

        response = {
            'solved': self.solved
        }

        if self._solved_msg:
            response['msg'] = self._solved_msg
        else:
            response['msg'] = 'Solved' if self.solved else 'Not solved'

        if self.solved and self.FLAG_TYPE == FlagType.DYNAMIC:
            response['flag'] = os.environ.get('FLAG', 'HAL{PLACEHOLDER}')

        return response

    def _generic_path_handler(self, port, host, path):

        # port = path_data['port']
        # host = path_data.get('host', '127.0.0.1')
        # proxy_path = path_data.get('path', '/')

        def _handler(**kwargs):

            # Important to add the final '/'
            full_path = urljoin(path, '/' + kwargs.get('path', ''))
            full_url = f'http://{host}:{port}{full_path}'

            try:
                resp = requests.request(
                    method=request.method,
                    url=full_url,
                    headers={key: value for (key, value)
                            in request.headers if key != 'Host'},
                    data=request.get_data(),
                    cookies=request.cookies,
                    allow_redirects=False,
                    stream=True)

                excluded_headers = ['content-encoding',
                            'content-length', 'transfer-encoding', 'connection']
                headers = [(name, value) for (name, value) in resp.raw.headers.items()
                if name.lower() not in excluded_headers]

                return Response(resp, resp.status_code, headers)
            except ConnectionError:
                return Response("Could not connect with server on port {}".format(None), 503)

        return _handler

    def _register_challenge_paths(self):
        for i, values in enumerate(self.PATH_MAPPING.items()):
            path, path_data = values
            methods = path_data.get('methods', ['GET'])
            host = path_data.get('host', '127.0.0.1')
            port = path_data['port']
            # TODO: Verify methods and path_data
            _filter = path_data.get('filter', None)
            if _filter:

                random_port = find_free_port()

                _filter(listen_port=random_port, to_port=port, to_host=host)

                # The path mapping should redirect to 127.0.0.1:random_port
                self._app.add_url_rule(path, 'mapping-{}'.format(i), self._generic_path_handler(port=random_port, host='127.0.0.1', path=path), methods=methods)
            else:
                self._app.add_url_rule(path, 'mapping-{}'.format(i), self._generic_path_handler(port=port, host=host, path=path), methods=methods)

    def _flask_run(self):
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

        self._app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), use_reloader=False, debug=False)

    #######################################

    def _register_flask_paths(self):
        self._app.add_url_rule('/info', 'info', self._app_info_handler, methods=['GET'])
        if self.HAS_FILES:
            self._app.add_url_rule('/files', 'files', self._app_files_handler, methods=['GET'])
        if self.HAS_SOLVER:
            self._app.add_url_rule('/solved', 'solved', self._app_solved_handler, methods=['GET'])

    def _build(self):
        with _CleanChildProcesses():
            self.build()

            f = open('/tmp/state.dump', 'bw')
            pickle.dump(self._state, f)

            f = open('/tmp/state_public.dump', 'bw')
            pickle.dump(self._state_public, f)

    def _run(self):
        with _CleanChildProcesses():

            f = open('/tmp/state.dump', 'br')
            tmp = pickle.load(f)
            self._state._merge(tmp)

            f = open('/tmp/state_public.dump', 'br')
            # TODO: Do a merge instead of replace
            tmp = pickle.load(f)
            self._state_public._merge(tmp)

            self._register_flask_paths()

            self.run()

            self._register_challenge_paths()

            self._ready = True

            # TODO: Try to run in on a thread and start it before the self.run function. This will allow to notify the ready state
            # in case a backgroun process is not specified as background.
            self._flask_run()


    @abstractmethod
    def build(self):
        """All the static funtionality that should be executed during the build phase of the challenge container. The running container will
        have everything executed here pre-bundled as this funcionality is only executed once for all running instances.

        NOTE:
            At the end of the execution of this function all processes will be killed. Any dynamic funcionality or any code that should be depended to each deployment, dynamic keys, dynamic accounts... should be inserted into
            :obj:`run` instead.
        """
        pass

    @abstractmethod
    def run(self):
        """All the dynamic funtionallity that should be executed during the creation of a challenge for each player.

        The ``run`` function should be used to start the actual challenge for the player. Such as running the chain, deploying the contracts (if they have to be done dynamically), starting the services and execute any :obj:`halborn_ctf.network.filters`.
        """
        pass

class Web3Challenge(GenericChallenge):
    """

    Class extending the GenericChallenge with :obj:`GenericChallenge.HAS_SOLVER` and :obj:`GenericChallenge.HAS_FILES` both set to ``True``.

    """

    FLAG_TYPE = FlagType.NONE
    HAS_SOLVER = True
    HAS_FILES = True

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def files(self):
        """Refer to :obj:`HAS_FILES`
        """
        pass

    @abstractmethod
    def solver(self):
        """Refer to :obj:`HAS_SOLVER`
        """
        pass
