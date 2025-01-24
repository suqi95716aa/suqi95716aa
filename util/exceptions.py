class IllegalRequestError(Exception):
    """
    Custom exception class
    for representing situations involving illegal or sensitive information。
    """
    def __init__(self, message):
        self.message = message
        super().__init__(message)

    def __str__(self):
        return self.message

if __name__ == "__main__":

    try:
        raise IllegalRequestError("mmm")
    except Exception as e:
        print(str(e))