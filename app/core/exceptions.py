class AuthenticationError(Exception):
    def __init__(self, detail: str = "Not authenticated"):
        self.detail = detail


class ForbiddenError(Exception):
    def __init__(self, detail: str = "Forbidden"):
        self.detail = detail


class NotFoundError(Exception):
    def __init__(self, detail: str = "Not found"):
        self.detail = detail


class ConflictError(Exception):
    def __init__(self, detail: str = "Conflict"):
        self.detail = detail
