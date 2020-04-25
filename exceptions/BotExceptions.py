class BotError(Exception):
    """Base class for exceptions in this module."""
    pass

class NotConfiguredAPI(BotError):
    """Exception raised for usages of the API without proper configuration
    Attributes:
        message -- explanation of the error
    """
    def __init__(self, message="No page_name and token provided to this bot."):
        self.message = message
    def __str__(self):
        return self.message


class NotLoggedIn(BotError):
    """Exception raised when bot attempts to execute a function that requires it logged in

    Attributes:
        message -- explanation of why the specific transition is not allowed
    """
    def __init__(self, message="Bot isn't logged in."):
        self.message = message
    def __str__(self):
        return self.message


class NoAccountCredentials(BotError):
    def __init__(self, message="Bot credentials aren't defined."):
        self.message = message
    def __str__(self):
        return self.message


class NoDatabase(BotError):
    def __init__(self, message="No database detected."):
        self.message = message
    def __str__(self):
        return self.message 


class NoDriver(BotError):
    def __init__(self, message="No driver!"):
        self.message = message
    def __str__(self):
        return self.message 

class FailedImageDownload(BotError):
    def __init__(self, message="Failed image download!"):
        self.message = message
    def __str__(self):
        return self.message