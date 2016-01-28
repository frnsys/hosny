import random


def random_choice(choices):
    """returns a random choice
    from a dict of {choice: probability}"""
    # sort by probability
    choices = sorted(choices.items(), key=lambda x:x[1])
    roll = random.random()

    acc_prob = 0
    for choice, prob in choices:
        acc_prob += prob
        if roll <= acc_prob:
            return choice
