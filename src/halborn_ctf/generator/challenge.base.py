from halborn_ctf.templates import GenericChallenge

class Challenge(GenericChallenge):

    HAS_SOLVER = True

    CHALLENGE_NAME = 'MY CHALLENGE'

    def run(self):
        # Do deployment
        pass

    def solver(self):
        self.solved = True