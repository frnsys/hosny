import operator
from uuid import uuid4
from agent import Agent
from agent.action import Action, Prereq, Outcome, Goal
from agent.search import expand_graph
from .names import generate_name
from .generate import generate

START_HOUR = 0
HOURS_IN_DAY = 24


class Person(Agent):
    @classmethod
    def generate(cls):
        """generate a random person"""
        attribs = generate()
        return cls(**attribs)

    """an individual in the city"""
    def __init__(self, age, sex, race, puma, neighborhood, income, education, employed, occupation):
        self.id = uuid4().hex
        self.name = generate_name(sex, race)
        self.sex = sex
        self.race = race
        self.puma = puma
        self.neighborhood = neighborhood
        self.education = education
        self.employed = employed
        self.occupation = occupation

        # modifiable attribs
        self.health = 1.
        self.stress = 0.
        self.income = 0.
        self.savings = 0.
        self.rent = 0.
        self.income = income

        self.state = {
            'stress': 0.5,
            'fatigue': 0,
            'cash': 0,
            'employed': 1
        }
        self.rent = 1000

        # long-term goals
        self.goals = [Goal(
            prereqs={'cash': Prereq(operator.ge, self.rent)},
            failures=[Outcome({'stress': 1}, 1.)],
            time=2
        )]

    def __repr__(self):
        return self.name

    def step(self, model):
        """
        actions have a distribution of outcomes,
        outcomes represent changes in the agent's state; they are noisy
        agents do not know these true distributions, they can only estimate
        """
        # TODO implement using agent framework

    def actions(self, state, world):
        # for now, just return all
        # other possible actions: crime, sleep, doctor, find_job, etc
        # actions are impossible if the agent is dead (health <= 0),
        # exhausted (fatigue >= 1)
        actions = [
            Action('relax', {
                'cash': Prereq(operator.ge, 100)
            }, [
                Outcome({'stress': -0.2}, 0.8),
                Outcome({'stress': -0.4}, 0.1),
                Outcome({'stress': 0.1}, 0.1),
            ], 2),
            Action('work', {
                'fatigue': Prereq(operator.ge, 0.5),
                'emploted': Prereq(operator.eq, 1)
            }, [
                Outcome({'stress': 0.1, 'cash': 100, 'fatigue': 0.5}, 0.8),
                Outcome({'stress': 0.2, 'cash': 100, 'fatigue': 0.5}, 0.2),
            ], 4),
            Action('sleep', {}, [
                Outcome({'stress': -0.6, 'fatigue': -1, 'cash': 0}, 1),
            ], 6)
        ]

        time = world['time']
        for action in actions:
            # actions limited by time in day
            if time + action.cost <= START_HOUR + HOURS_IN_DAY:
                yield action


    def plan_day(self):
        """make a plan of what actions to (attempt to) execute through the day.
        the agent considers all possible paths through 24 hours, choosing the one
        that gets them closest to their important goals and maximizes average
        expected utility throughout the day"""
        world = {'time': START_HOUR}
        succs = self.successors(self.state, world)

        # generate full graph for the day
        paths = [[(a, (s,w))] for a, (s, w) in succs]
        paths = [p for p in expand_graph(paths, self._graph_succ_func)]

        # rank paths by utilities of the expected states
        paths = sorted(paths, key=lambda p: self.score_path(self, p), reverse=True)

        # preferred plan for the day
        return paths[0]
