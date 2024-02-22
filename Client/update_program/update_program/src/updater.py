def state_updater(req, state):
    for e in state:
        if (e.path, e.method) == (req.path, req.method):
            return state
    newEntry = StateEntry(path=req.path, method=req.method)
    state.append(newEntry)
    return state