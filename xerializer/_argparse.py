class Argument:
    """
    Defines an argument that will be added to a parser. This object can be passed as an argument to CLI builders.
    """

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self._bound = None

    def bind(self, parser):
        """
        Adds this argument to the specified parser.
        """
        self._bound = parser.add_argument(*self.args, **self.kwargs)
        return self._bound

    def name(self):
        if not self._bound:
            raise Exception("Cannot retrieve the name of an unbound argument.")
        return self._bound.dest
