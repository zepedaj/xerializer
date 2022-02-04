

class NotAChildOfError(Exception):
    def __init__(self, orphan, parent):
        super().__init__(f'Node `{orphan}` is not a child of `{parent}`.')


class ResolutionCycleError(Exception):
    def __init__(self, cycle):
        self.cycle = cycle
        super().__init__(
            'Resolution dependency cycle detected when attempting to resolve a node: ' +
            ' -> '.join('<root>' if x.qual_name == '' else x.qual_name for x in cycle))
