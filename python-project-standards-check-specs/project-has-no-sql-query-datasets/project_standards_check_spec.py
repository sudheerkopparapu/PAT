import dataiku

from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):

    def run(self):
        """
        Runs the check to identify datasets that are in sql query mode.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        check_pass = True
        message = "All SQL datasets are in 'read a database table' mode."
        result = {}

        sql_query_dataset_names = []
        for d in self.project.list_datasets():
            if "params" in d and "mode" in d["params"] and d["params"]["mode"] == "query":
                check_pass = False
                sql_query_dataset_names.append(d["name"])

        if not check_pass:
            result["sql_query_dataset_names"] = sql_query_dataset_names
            message = f"Identified {len(sql_query_dataset_names)} datasets that are in 'SQL query' mode."

        if check_pass:    
            return ProjectStandardsCheckRunResult.success(
                message = message,
                details = result
            )
        else:
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = message,
                details = result
            )
