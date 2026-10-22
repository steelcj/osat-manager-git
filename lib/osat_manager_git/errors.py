"""The one exception manage-git raises for anything it refuses to do."""


class ManagerError(Exception):
    """A request the manager will not carry out; the command line turns it
    into a message and exit status 1.

    ``key`` names the message in the catalogue, and ``fields`` fill its
    placeholders, so the same refusal reads correctly in every language.
    """

    def __init__(self, key: str, /, **fields: object):
        self.key = key
        self.fields = fields
        super().__init__(key)
