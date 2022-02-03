

class NotAChildOfError(Exception):
    def __init__(self, orphan, parent):
        super().__init__(f'Node `{orphan}` is not a child of `{parent}`.')
