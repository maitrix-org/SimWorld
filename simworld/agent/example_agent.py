
class ExampleAgent(BaseAgent):
    def __init__(self, position: Vector, direction: Vector, communicator: Communicator, use_a2a: bool = False, use_rule_based: bool = False, llm: LLM = None, vlm: VLM = None):
        super().__init__(position, direction)
        self.communicator = communicator
        self.a2a = Activity2Action(llm, vlm, self, use_rule_based)

    

