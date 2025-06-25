class DocumentError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class DocumentDoesNotExistsError(DocumentError):
    def __init__(self, attribute_name: str, attribute_value: any):
        super().__init__(
            f"Document with {attribute_name}={attribute_value} does not exists"
        )
