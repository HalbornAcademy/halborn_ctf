import logging

from ..state import State

from abc import ABC, abstractmethod

class Web3GenericChallenge(ABC):

    def __init__(self) -> None:
        self.state = State({
            'solved': False,
            'ready': False,
            'private': State({}),
            'port_mapping': {}
        })
        self.log = logging.getLogger('challenge')

    @abstractmethod
    def build(self):
        pass

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def files(self):
        pass