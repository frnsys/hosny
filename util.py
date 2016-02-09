import random


def random_choice(choices):
    """returns a random choice
    from a list of (choice, probability)"""
    # sort by probability
    choices = sorted(choices, key=lambda x:x[1])
    roll = random.random()

    acc_prob = 0
    for choice, prob in choices:
        acc_prob += prob
        if roll <= acc_prob:
            return choice


def ewms(p_mean, p_var, val, alpha=0.8):
    """computes exponentially weighted moving statistics (mean, variance)"""
    mean = p_mean + (alpha * (val - p_mean))
    var = p_var + (alpha * (val - p_mean)**2)
    return mean, var
