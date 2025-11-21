from enum import Enum, auto

class CheckSeverity(Enum):
    """
    Enumeration representing different check Severities
    """
    NO_SEVERITY = -1
    OK = 0
    LOWEST = 1
    LOW = 2
    MEDIUM = 3
    HIGH = 4
    CRITICAL = 5
    
class DSSAssessmentStatus(Enum):
    """
    Enumeration representing different Assessment Run Status
    """
    RUN_SUCCESS = auto()
    RUN_ERROR = auto()
    NOT_APPLICABLE = auto()
    NOT_RUN = auto()


class ProjectCheckCategory(Enum):
    """
    Enumeration representing different categories of project checks.
    """

    FLOW = auto()
    AUTOMATION = auto()
    DOCUMENTATION = auto()
    CODE = auto()
    PERFORMANCE = auto()
    ROBUSTNESS = auto()
    API_SERVICE = auto()
    DEPLOYMENT = auto()

class InstanceCheckCategory(Enum):
    """
    Enumeration representing different categories of instance checks.
    """

    USAGE = auto()
    PLATFORM = auto()
    CONFIGURATION = auto()
    PROCESSES = auto()