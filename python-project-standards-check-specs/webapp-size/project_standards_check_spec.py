import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
    
    def run(self):
        """
        Runs the check to determine if Webapps are under a specified number of rows.
        """
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        details = {}

        webapps = []
        code_webapp_types = ['DASH', 'STANDARD', 'BOKEH', "SHINY"]
        for webapp in self.project.list_webapps():
            if webapp.get("type") in code_webapp_types:
                webapps.append(webapp)
        
        details["nbr_webapps"] = len(webapps)

        if not webapps:
            return ProjectStandardsCheckRunResult.not_applicable(
                message =  f"The project does not contain any code webapps",
                details = details
            )
        
        [details.update({webapp_type : 0}) for webapp_type in code_webapp_types]
        
        big_webapps = []
        webapp_row_counts = []
        for webapp in webapps:
            details[webapp.get("type")]+=1
            webapp_id = webapp.get("id")
            webapp_current = self.project.get_webapp(webapp_id)
            setting_params = webapp_current.get_settings().get_raw().get("params", {})
            if webapp.get("type") == "SHINY":
                ui_code = setting_params.get("ui")
                server_code = setting_params.get("server")
                code = ui_code + server_code
            else:
                code = setting_params.get("python")

            if code == None:
                code = ""
            lines = code.split("\n")
            lines = [line for line in lines if line != ""]
            lines = [line for line in lines if not line.startswith("#")]
            lines = [line for line in lines if not line.startswith("import")]
            lines = [line for line in lines if not line.startswith("from")]
            lines = [line for line in lines if not line.startswith("library")] # For R code
            
            row_count = len(lines)
            webapp_row_counts.append(row_count)
            if row_count > lowest_threshold:
                big_webapps.append(webapp_id)
        
        
        nbr_big_webapps = len(big_webapps)
        
        max_row_count = max(webapp_row_counts)
        avg_row_count = sum(webapp_row_counts)/len(webapps)

        details["big_webapps"] = md_print_list(big_webapps, "webapp", self.original_project_key)
        details["nbr_big_webapps"] = nbr_big_webapps
        details["max_row_count"] = max_row_count
        details["avg_row_count"] = avg_row_count
        
        error_message = f"{nbr_big_webapps} too big webapps have been identified. Consider leveraging code libraries"
        
        if max_row_count > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = error_message,
                details = details
            )
        elif max_row_count > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = error_message,
                details = details
            )
        elif max_row_count > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = error_message,
                details = details
            )
        elif max_row_count > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = error_message,
                details = details
            )
        elif max_row_count > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = error_message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"All python recipes in the Flow are under {int(lowest_threshold)} lines of code.",
                details = details
            )
        
