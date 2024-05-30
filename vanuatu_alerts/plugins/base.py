class BasePlugin:
    def __init__(self, name: str, frequency: int):
        self.name = name
        self.frequency = frequency

    def run(self) -> str | None:
        pass
