import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Check that the Project isn't too big
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        nodes = self.project.get_flow().get_graph().nodes
        count = len([name for name in nodes.keys() if "DATASET" in nodes[name]["type"]])
        details = {"nbr_datasets" : count}
        
        if count > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = f"This Flow has {count} datasets which is more than the critical threshold of {critical_threshold} datasets.",
                details = details
            )
        elif count > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message =   f"This Flow has {count} datasets which is more than the high criticality threshold of {high_threshold} datasets.",
                details = details
            )
        elif count > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message =   f"This Flow has {count} datasets which is more than the medium criticality threshold of {medium_threshold} datasets.",
                details = details
            )
        elif count > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message =   f"This Flow has {count} datasets which is more than the low criticality threshold of {low_threshold} datasets.",
                details = details
            )
        elif count > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = f"This Flow has {count} datasets which is more than the lowest critical threshold of {lowest_threshold} datasets.",
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project's Flow is under the recommended max number of datasets : {int(lowest_threshold)}",
                details = details
            )
        
