def update_state(state, update, expected=False):
    """generates a new state based on the specified update dict;
    note: this does not attenuate the state"""
    state = state.copy()
    for k, v in update.items():
        # ignore keys not in state
        if k not in state:
            continue

        # get the type of the value
        # to coerce it back if necessary
        typ = type(state[k])

        # v can be a callable, taking the state,
        # or an int/float
        try:
            val = v(state)
            if isinstance(val, tuple):
                val, exp = val
            else:
                exp = val
            state[k] += (exp if expected else val)
        except TypeError:
            state[k] += v
        state[k] = typ(state[k])
    return state


def attenuate_state(state, ranges):
    """attenuates a state so that its values
    are within the specified ranges"""
    for k, v in state.items():
        if k in ranges:
            state[k] = attenuate_value(v, ranges[k])
    return state


def attenuate_value(value, range):
    """attenuates a value to be within the specified range"""
    mn, mx = range
    if mn is not None: value = max(mn, value)
    if mx is not None: value = min(mx, value)
    return value
