def zoom_access_only_created(req, state):
    if req.path.startswith('/events'):
        if (req.path, req.method) == ('/events', 'POST'):
            # Allow creating a new event.
            return True
        else:
            # Iterate through the state - history of API calls,
            # to see if the user has created this event.
            for e in state:
                if (e.path, e.method) == ('/events', 'POST'):
                    # Allow access if the state indicates that 
                    # the user has created this event.
                    return True
            # Deny if no creation in the state.
            return False
    # Allow accessing other endpoints in the scope.
    return True