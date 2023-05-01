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
from typing import TypedDict, NotRequired
from enum import Enum

from .state import State

from abc import ABC, abstractmethod

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
    """ port (int): The port to redirect to.
    """
    host: NotRequired[str]
    """ host (str): The host to redirect to. Defaults to ``'127.0.0.1'``.
    """
    path: NotRequired[str]
    """ path (str): The path to redirect to. Defaults to ``'/'``.
    """
    methods: list[str]
    """ methods (list[str]): The allowd methods. Defaults to ``["GET"]``.
    """

class FlagType(Enum):
    NONE = 0
    STATIC = 1
    DYNAMIC = 2

class GenericChallenge(ABC):
    """Generic CTF challenge template

    Each created/deployed challenge does have two steps defined, :obj:`build` and :obj:`run`. The ``build`` step is only executed once
    when the challenge is created and uploaded into the platform for playing. The ``run`` step is always executed for each player request
    to deploy a new challenge.

    This template does also expose the challenge by using an HTTP server. The server does allow registering routes to it by using
    the :obj:`path_mapping` attribute.

    An attribute named :obj:`state` can be used to store any sort of object that will persiste between the ``build`` and ``run`` steps. Furthermore,
    this attribute can be used to store anything that would be used across the different functions. The `state.public` attribute will be exposed
    under the `/state` path on the challenge domain.

    Attributes:

    """

    CHALLENGE_NAME = os.environ.get('CHALLENGE_NAME', 'challenge')
    FLAG_TYPE = FlagType.NONE
    HAS_FILES = False
    HAS_SOLVER = False

    def __init__(self) -> None:
        super().__init__()

        self._app = flask.Flask('Challenge')
        self._log = logging.getLogger('GenericChallenge')

        CORS(self._app)

        self._state_set = False
        self._state = State({
            'public': State({}),
            'ready': False,
        })

        if self.HAS_SOLVER:
            self._state._setattr('solved', False)
            self._state._setattr('solved_msg', False)

        if self.HAS_FILES:
            try:
                getattr(self, 'files')
            except:
                raise NotImplementedError('Missing function "files" (HAS_FILES == True)')
        else:
            try:
                getattr(self, 'files')
                raise NotImplementedError('Remove "files" function (HAS_FILES == False)')
            except:
                pass

        if self.HAS_SOLVER:
            try:
                getattr(self, 'solved')
            except:
                raise NotImplementedError('Missing function "solved" (HAS_SOLVER == True)')
        else:
            try:
                getattr(self, 'solved')
                raise NotImplementedError('Remove "solved" function (HAS_SOLVER == False)')
            except:
                pass

        if not self.HAS_SOLVER and self.FLAG_TYPE == FlagType.NONE:
            raise ValueError("HAS_SOLVER == False and FLAG_TYPE == NONE")

        self._path_mapping: dict[str, MappingInfo] = {}

    @property
    def path_mapping(self):
        """(dict[str, MappingInfo]): Mapping used internally to register the challenge URL's paths.
            It does contain a mapping of ``path`` to ``MappingInfo`` dictionary details.

            Example:
                Have the challenge ``/`` path expose the anvil service which is running internally on port ``8545``::

                    self.path_mapping = {
                        '/': {
                                'host': '127.0.0.1', # optional. Defaults to '127.0.0.1'
                                'port': 8545,
                                'path': '/', # optional. Defaults to '/'
                                'methods': ['POST'] # optional. Defaults to ['GET']
                        }
                    }

                Redirect all request to the service running on port ``8080`` and under ``/service``::

                    self.path_mapping = {
                        '/<path:path>': {
                                'port': 8080,
                                'path': '/service',
                                'methods': ['GET', 'POST', 'HEAD']
                        }
                    }
        """
        return self._path_mapping

    @path_mapping.setter
    def path_mapping(self, value):
        self._path_mapping = value

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


        Attributes:
            public (State): It will expose the state content into the challenge `/state` route.
            ready (bool): If the challenge is ready to be played.
            solved (bool): Only present if :obj:`HAS_SOLVER` is set. It does allow setting the challenge as solved
            solved_msg (str): Only present if :obj:`HAS_SOLVER` is set. It does allow setting a "clue" or info message to the player

        """
        return self._state

    @state.setter
    def state(self, value):
        if self._state_set:
            raise ValueError("State already set, use state.update instead")
        self._state._merge(value)
        self._state_set = True

    def _app_info_handler(self):
        if not self.state.ready:
            return Response("Challenge not ready", status=503)

        return self.state.public

    def _app_files_handler(self):
        if not self.state.ready:
            return Response("Challenge not ready", status=503)

        fileName = f"{self.CHALLENGE_NAME}.zip"
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for _added in self.files():
                for result in glob.glob(_added):
                    zipf.write(result)

        memory_file.seek(0)
        return flask.send_file(memory_file,
                        download_name=fileName,
                        as_attachment=True)

    def _app_solved_handler(self):
        if not self.state.ready:
            return Response("Challenge not ready", status=503)

        try:
            self.solved()
        except:
            pass

        _solved_state = self.state.get('solved', False)
        response = {
            'solved': _solved_state,
            'msg': self.state.get('solved_msg', 'Solved' if _solved_state else 'Not solved'),
            }

        if self.FLAG_TYPE != FlagType.NONE:
            response['flag'] = os.environ.get('FLAG', 'HAL{PLACEHOLDER}')

        return response

    def _generic_path_handler(self, path, path_data: MappingInfo):

        port = path_data['port']
        host = path_data.get('host', '127.0.0.1')
        proxy_path = path_data.get('path', '/')

        def _handler(**kwargs):

            # Important to add the final '/'
            full_path = urljoin(proxy_path, '/' + kwargs.get('path', ''))
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
        for i, values in enumerate(self.path_mapping.items()):
            path, path_data = values
            methods = path_data.get('methods', ['GET'])
            # TODO: Verify methods and path_data
            self._app.add_url_rule(path, 'mapping-{}'.format(i), self._generic_path_handler(path, path_data), methods=methods)

    def _flask_run(self):
        cli = sys.modules['flask.cli']
        cli.show_server_banner = lambda *x: None

        self._app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), use_reloader=False, debug=False)

    #######################################

    def _register_flask_paths(self):
        self._app.add_url_rule('/state', 'public-state', self._app_info_handler, methods=['GET'])
        if self.HAS_FILES:
            self._app.add_url_rule('/files', 'files', self._app_files_handler, methods=['GET'])
        if self.HAS_SOLVER:
            self._app.add_url_rule('/solved', 'solved', self._app_solved_handler, methods=['GET'])

    def _build(self):
        with _CleanChildProcesses():
            self.build()

            f = open('state.dump', 'bw')
            pickle.dump(self.state, f)

    def _run(self):
        with _CleanChildProcesses():

            f = open('state.dump', 'br')
            self._state = pickle.load(f)

            self._register_flask_paths()
            self._register_challenge_paths()

            self.run()

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
        pass