class InvalidInputError(Exception):
    def __init__(self, val: object, txt: str = '', *args: object) -> None:
        self.val = val
        self.txt = txt
    
    def __str__(self) -> str:
        return f"Can't create cls object from: {self.val}; {self.txt}"

class UserNotFoundError(Exception):
    def __init__(self, user_id) -> None:
        self.user_id = user_id