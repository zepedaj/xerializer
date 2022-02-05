

class NotAChildOfError(Exception):
    def __init__(self, orphan, parent):
        super().__init__(f'Node `{orphan}` is not a child of `{parent}`.')


class ResolutionCycleError(Exception):
    def __init__(self, cycle):
        self.cycle = cycle
        super().__init__(
            'Resolution dependency cycle detected when attempting to resolve a node: ' +
            ' -> '.join('<root>' if x.qual_name == '' else x.qual_name for x in cycle))


class InvalidRefStr(Exception):
    def __init__(self, ref: str):
        raise Exception(f'Invalid reference string `{ref}`.')


class InvalidRefStrComponent(Exception):
    def __init__(self, ref_component: str):
        self.ref_component = ref_component
        raise Exception(f'Invalid ref string component {ref_component}.')
