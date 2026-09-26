class AIError(Exception): pass
class AIAuthenticationError(AIError): pass
class AIRateLimitError(AIError):
    def __init__(self, message="Rate limited", retry_after=1.0): super().__init__(message); self.retry_after = retry_after
class AIResponseError(AIError): pass
class AICancelled(AIError): pass
