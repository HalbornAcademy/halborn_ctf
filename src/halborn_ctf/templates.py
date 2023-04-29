import logging
import flask
from flask_cors import CORS
from flask import Response, request
import requests
import os
import zipfile
import json
from io import BytesIO
import glob
import pickle
import signal
from urllib.parse import urljoin

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


class GenericChallenge(ABC):

    def __init__(self) -> None:
        super().__init__()

        self._app = flask.Flask('Challenge')

        CORS(self._app)

        self.state = State({})
        self.path_mapping = {}
        self.state.private = State({})

        self.log = logging.getLogger('challenge')

    def _generic_path_handler(self, path, path_data):

        port = path_data['port']
        host = path_data.get('host', '127.0.0.1')
        proxy_path = path_data.get('path', '/') + '/' # Important to add the final '/'

        def _handler(**kwargs):

            full_path = urljoin(proxy_path, kwargs.get('path', ''))

            try:
                resp = requests.request(
                    method=request.method,
                    url=f'http://{host}:{port}{full_path}',
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
        self._app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080), use_reloader=False, debug=False)
    
    #######################################

    def _register_flask_paths(self):
        pass

    def _build(self):
        with _CleanChildProcesses():
            self.build()

            f = open('state.dump', 'bw')
            pickle.dump(self.state, f)

    def _run(self):
        with _CleanChildProcesses():

            f = open('state.dump', 'br')
            self.state = pickle.load(f)

            self._register_flask_paths()
            self._register_challenge_paths()

            self.run()

            self._flask_run()

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def run(self):
        pass

class Web3GenericChallenge(GenericChallenge):

    def _app_files_handler(self):
        if self.state.ready:
            return Response("Challenge not ready", status=503)

        CHALLENGE_FLAG = os.environ.get('CHALLENGE_FLAG', 'HAL{FLAG}')
        CHALLENGE_NAME = os.environ.get('CHALLENGE_NAME', 'challenge')


        fileName = f"{CHALLENGE_NAME}.zip"
        memory_file = BytesIO()
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for _added in self.files():
                for result in glob.glob(_added):
                    zipf.write(result)

        memory_file.seek(0)
        return flask.send_file(memory_file,
                        download_name=fileName,
                        as_attachment=True)
    
    
    def _app_info_handler(self):

        def without_keys(d, keys):
            return {k: v for k, v in d.items() if k not in keys}
        return without_keys(self.state, ['private', 'solved'])
    
    def _app_solved_handler(self):
        if self.state.ready:
            return Response("Challenge not ready", status=503)

        _solved_state = self.state.get('solved', False)
        response = {
            'solved': _solved_state,
            'msg': self.state.get('solved_msg', 'Solved' if _solved_state else 'Not solved'),
            }

        return response
    
    ##################################

    def _register_flask_paths(self):
        super()._pre_run()
        self._add_endpoint('/files', 'files', self._app_files_handler)
        self._add_endpoint('/solved', 'solved', self._app_solved_handler)
        self._add_endpoint('/', 'info', self._app_info_handler)


    def __init__(self) -> None:
        super().__init__()

        self.state.solved = False
        self.ready = False
        self.state.private = State({})
    


    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def files(self):
        pass