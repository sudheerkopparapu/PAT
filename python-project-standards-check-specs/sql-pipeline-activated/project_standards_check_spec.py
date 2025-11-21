import dataikuapi
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)


class SQLPipelineActivatedCheckSpec(ProjectStandardsCheckSpec):
    """
    Check that all SQL pipelines available in a project are activated.
    """
    def _get_severity(self, value: int) -> int:
        """
        Return severity code based on criticality thresholds
        """
        lowest_threshold = self.config.get("lowest")
        low_threshold = self.config.get("low")
        medium_threshold = self.config.get("medium")
        high_threshold = self.config.get("high")
        critical_threshold = self.config.get("critical")
        severities_thresholds = [
            critical_threshold,
            high_threshold,
            medium_threshold,
            low_threshold,
            lowest_threshold,
        ]

        for i in range(0, len(severities_thresholds)):
            if value >= severities_thresholds[i]:

                return 5 - i
        return 0

    def run(self):
        """
        For SQL pipelines to be actived, we need to:
        - Have SQL pipelines activated on the project.
        - Have virtualizable SQL datasets in a chain.

        # Note : And dataset can be virtualizable.
        # Note : A recipe can't be partially SQL to virtualize the previous dataset.

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """

        # Possible SQL Connections
        sql_cnx_types = [
            "Snowflake",
            "Redshift",
            "Databricks",
            "BigQuery",
            "Synapse",
            "OneLake",
            "PostgreSQL",
            "MySQL",
            "SQLServer",
            "Oracle",
            "Teradata",
            "AlloyDB",
            "Athena",
            "Greenplum",
            "Vertica",
            "SAPHANA",
        ]

        # STEP 1 : Find all SQL datasets in the Flow
        sql_datasets = []
        for d in self.project.list_datasets(as_type="objects"):
            if d.get_definition().get("type") in sql_cnx_types:
                sql_datasets.append(d.name)

        # STEP 2 : Find all the virtualizable SQL datasets
        # A SQL dataset is Virtualizable is when all the connecting recipes are pushing down to SQL.
        def has_sql_engine(project: dataikuapi.dss.project.DSSProject, recipe_name: str) -> bool:
            """Return true if the engine of the recipe is SQL"""
            try:
                r = project.get_recipe(recipe_name)
                return r.get_status().data.get("selectedEngine", {}).get("label") == "In-database (SQL)"
            except Exception as e:
                return False  # No SQL Engine

        shared_objects = self.project.get_settings().get_raw().get("exposedObjects", {}).get("objects")
        shared_datasets = [obj.get("localName") for obj in shared_objects if obj.get("type") == "DATASET"]

        nodes = self.project.get_flow().get_graph().nodes
        virtualizable_datasets = []
        for sql_d in sql_datasets:
            sql_node = nodes[sql_d]
            predecessors = sql_node.get("predecessors", [])
            successors = sql_node.get("successors", [])
            if (
                all([has_sql_engine(self.project, r_name) for r_name in predecessors + successors])
                and len(predecessors) > 0
                and len(successors) > 0
                and shared_datasets
                and sql_d not in shared_datasets
            ):
                virtualizable_datasets.append(sql_d)

        # STEP 3 : Check that SQL pipeline is activated for the SQL Virtualizable datasets
        virtualized_datasets = []
        datasets_to_virtualize = []

        for d_name in virtualizable_datasets:
            d = self.project.get_dataset(d_name)
            if d.get_definition().get("flowOptions", {}).get("virtualizable", {}):
                virtualized_datasets.append(d_name)
            else:
                datasets_to_virtualize.append(d_name)

        run_result = {
            "virtualizable_datasets": virtualizable_datasets,
            "virtualized_datasets": virtualized_datasets,
            "datasets_to_virtualize": datasets_to_virtualize,
        }

        if len(virtualizable_datasets) == 0:
            return ProjectStandardsCheckRunResult.not_applicable("No SQL pipelines are needed", run_result)

        enable_sql_pipelines = (
            self.project.get_settings()
            .settings.get("settings", {})
            .get("flowBuildSettings", {})
            .get("mergeSqlPipelines")
        )

        if len(datasets_to_virtualize) > 0:
            if enable_sql_pipelines:
                message = f"There are {len(datasets_to_virtualize)} dataset(s) to virtualize out of the {len(virtualizable_datasets)} virtualizable dataset(s). Allow build virtualization on these datasets : {', '.join(datasets_to_virtualize)}"
            else:
                message = f"{len (virtualizable_datasets)} dataset(s) is/are virtualizable, enable SQL Pipelines in the project settings to virtualize it/them."
            return ProjectStandardsCheckRunResult.failure(
                self._get_severity(len(datasets_to_virtualize)),
                message,
                run_result,
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                f"All the {len(virtualizable_datasets)} virtualizable dataset(s) have been virtualized", run_result
            )
