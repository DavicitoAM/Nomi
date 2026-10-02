class DomainError(Exception):
    def __init__(self, code: str, detail: str, status: int = 422):
        super().__init__(detail)
        self.code, self.detail, self.status = code, detail, status
