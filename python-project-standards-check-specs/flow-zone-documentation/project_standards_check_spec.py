import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list 


class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    
    def run(self):
        """
        Check that the project has at least one scenario.
        """
        flow = self.project.get_flow()
        zones = flow.list_zones()
        check_pass = True
        message = f"All flow zones have at least a short description"
        details = {}
        no_desc_zones=[]
        for zone in zones:
            description=zone.get_settings().get_raw()
            if "description" in description and len(description["description"])>0:
                long_desc=description["description"]
            else:
                if "shortDesc" in description and len(description["shortDesc"])>0:
                    short_desc=description["shortDesc"]
                else:
                    check_pass = False
                    no_desc_zones.append(zone.id)
        if no_desc_zones:
            message = f"{len(no_desc_zones)} flow zone(s) identified without a description"
        
        details["no_desc_zones"] = md_print_list(no_desc_zones, "flow_zone", self.original_project_key)

        if check_pass:
            return ProjectStandardsCheckRunResult.success(
                message =message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message =message,
                    details = details
                )

