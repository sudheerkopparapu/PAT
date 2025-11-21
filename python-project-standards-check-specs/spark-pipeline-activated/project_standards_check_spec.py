import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from typing import Dict, Tuple, List, Any


class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def _get_project_shared_datasets(self) -> List[str]:
        project_shared_objects = (
            self.project.get_settings()
            .get_raw()
            .get("exposedObjects", {})
            .get("objects")
        )
        return [
            obj.get("localName")
            for obj in project_shared_objects
            if obj.get("type") == "DATASET"
        ]

    def _get_spark_reliant_recipes(self) -> List[Dict[str, bool]]:
        """
        STEP 1 : Check that Spark is used in the project
        """
        engine_type = "SPARK"
        uses_spark_engine = {}
        [
            uses_spark_engine.update(
                {
                    r.name: r.get_status().data.get("selectedEngine", {}).get("type")
                    == engine_type
                }
            )
            for r in self.project.list_recipes(as_type="objects")
        ]
        return uses_spark_engine

    def _get_spark_virtualizable_dataset(
        self, uses_spark_engine: List[Dict[str, bool]]
    ) -> List[str]:
        """
        STEP 2 : Get virtualizable Spark datasets
        """

        virtualizable_datasets = []

        for d_name in [d.get("name") for d in self.project.list_datasets()]:
            node = self.project_flow_nodes[d_name]
            predecessors = node.get("predecessors", [])
            successors = node.get("successors", [])
            all_connected_recipes = predecessors + successors
            if (
                all(
                    [
                        uses_spark_engine.get(r_name, False)
                        for r_name in all_connected_recipes
                    ]
                )
                and len(predecessors) > 0
                and len(successors) > 0
                and d_name not in self.project_shared_datasets
            ):
                virtualizable_datasets.append(d_name)

        return virtualizable_datasets

    def _check_if_spark_pipeline_activated(
        self,
        uses_spark_engine: List[Dict[str, bool]],
        virtualizable_datasets: List[str],
    ) -> Tuple[List[str], List[str]]:
        """
        STEP 3: Check that Spark pipeline are activated if needed.
        """
        virtualized_datasets = []
        datasets_to_virtualize = []
        if any(list(uses_spark_engine.values())):
            for d_name in virtualizable_datasets:
                d = self.project.get_dataset(d_name)
                if d.get_definition().get("flowOptions", {}).get("virtualizable", {}):
                    virtualized_datasets.append(d_name)
                else:
                    datasets_to_virtualize.append(d_name)

        return virtualized_datasets, datasets_to_virtualize

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

    def _get_run_result(
        self,
        virtualizable_datasets: List[str],
        datasets_to_virtualize: List[str],
        run_details: Dict[str, List[str]],
    ) -> Any:
        """
        STEP 4: Determine whether check passed based on datasets_to_virtualize
        """

        num_virtualizable_datasets = len(virtualizable_datasets)
        num_datasets_to_virtualize = len(datasets_to_virtualize)

        if num_datasets_to_virtualize > 0:
            if self.sql_pipelines_is_enabled:
                message = f"There is/are {num_datasets_to_virtualize} dataset(s) to virtualize out of the {num_virtualizable_datasets} virtualizable dataset(s). Allow build virtualization on these datasets : {', '.join(datasets_to_virtualize)}."

            else:
                message = f"{num_virtualizable_datasets} dataset(s) is/are virtualizable, but Spark pipelines are disabled. You can enable Spark pipelines in the project settings."
                

            return ProjectStandardsCheckRunResult.failure(
                severity=self._get_severity(num_datasets_to_virtualize),
                message=message,
                details=run_details,
            )

        else:
            return ProjectStandardsCheckRunResult.success(
                message=f"All the {num_virtualizable_datasets} virtualizable datasets have been virtualized.",
                details=run_details,
            )

    def run(self):
        """
        For Spark pipelines to be actived, we need to:
        - Have Spark pipelines activated on the project.
        - Allow Spark Virtualization on virtualizable spark datasets.

        # Note : A dataset is Spark virtualizable when it has
         - all connecting recipes running on spark
         - At least one input and one output.
         - Is not shared.
        """
        self.sql_pipelines_is_enabled = (
            self.project.get_settings()
            .settings.get("settings", {})
            .get("flowBuildSettings", {})
            .get("mergeSparkPipelines")
        )
        self.project_shared_datasets = self._get_project_shared_datasets()
        self.project_flow_nodes = self.project.get_flow().get_graph().nodes

        uses_spark_engine = self._get_spark_reliant_recipes()
        virtualizable_datasets = self._get_spark_virtualizable_dataset(
            uses_spark_engine
        )
        if len(virtualizable_datasets) == 0:
            return ProjectStandardsCheckRunResult.not_applicable(
                message="There are no virtualizable datasets in this project.",
            )

        virtualized_datasets, datasets_to_virtualize = (
            self._check_if_spark_pipeline_activated(
                uses_spark_engine, virtualizable_datasets
            )
        )

        run_details = {
            "virtualizable_datasets": virtualizable_datasets,
            "virtualized_datasets": virtualized_datasets,
            "datasets_to_virtualize": datasets_to_virtualize,
        }

        return self._get_run_result(
            virtualizable_datasets, datasets_to_virtualize, run_details
        )
