import dataiku
import dataikuapi
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from project_advisor.pat_tools import dss_obj_to_dss_obj_md_link

import sqlfluff

from typing import List, Dict, Tuple
from dataikuapi.dss.projectlibrary import DSSLibraryFile
from dataikuapi.dss.projectlibrary import DSSLibraryFolder

CONNECTION_TYPE_TO_SQLFLUFF_DIALECT_MAP = {
    "Databricks": "databricks",
    "Snowflake": "snowflake",
    "Redshift": "redshift",
    "BigQuery": "bigquery",
    "PostgreSQL": "postgres",
    "MySQL": "mysql",
    "SQLServer": "tsql",
    "Oracle": "oracle",
    "Trino": "trino",
    "Teradata": "teradata",
    "Vertica": "vertica",
    "Athena": "athena",
    "Greenplum": "greenplum",
    "SparkSQL": "sparksql",
}


class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def _get_recipe_to_sql_dialect_mappings(self) -> List[Tuple[str, str]]:
        """
        Identifies all SQL recipes in the project and maps them to their SQL dialect based on the connection type of their input dataset.

        Returns:
            List[Tuple[str, str]]: List of tuples containing recipe name and SQL dialect, using Dataiku formatting conventions
        """

        all_recipes = self.project.list_recipes()
        flow_nodes = self.project.get_flow().get_graph().nodes

        sql_recipe_names = [
            d["name"]
            for d in all_recipes
            if d["type"] == "sql_query"
            or d["type"] == "sql_script"
            or d["type"] == "spark_sql_query"
        ]
        mappings = []
        for recipe_name in sql_recipe_names:
            recipe_node = flow_nodes[recipe_name]
            if recipe_node.get("subType") != "spark_sql_query":
                predecessor_name = recipe_node.get("predecessors")[0]
                predecessor_type = (
                    self.project.get_dataset(dataset_name=predecessor_name)
                    .get_definition()
                    .get("type")
                )
                mappings.append((recipe_name, predecessor_type))
            else:
                mappings.append((recipe_name, "SparkSQL"))

        return mappings


    def _get_formatting_status(
        self, recipe_name_dialect_mappings: List[Tuple[str, str]]
    ) -> List[Dict[str, int]]:
        """

        Args:
            sql_queries (List[Tuple[str,str]]): Tuple containing sql recipe name and SQL dialect, using Dataiku formatting conventions

        Returns:
            List[Dict[str, int]]: Dictionary containing recipe name and number of lines to be formatted
        """
        results = []
        for recipe in recipe_name_dialect_mappings:
            recipe_name = recipe[0]
            sql_query = self.project.get_recipe(recipe_name).get_settings().get_payload()
            sql_dialect = CONNECTION_TYPE_TO_SQLFLUFF_DIALECT_MAP.get(recipe[1], "ansi")
            n_formatting_changes = len(sqlfluff.lint(sql_query, dialect=sql_dialect))

            results.append(
                {
                    "name": recipe_name,
                    "n_formatting_changes": n_formatting_changes,
                }
            )
        return results


    def run(self):

        decision_criteria = self.config.get("decision_criteria")

        lowest_threshold = self.config.get("lowest")
        low_threshold = self.config.get("low")
        medium_threshold = self.config.get("medium")
        high_threshold = self.config.get("high")
        critical_threshold = self.config.get("critical")

        recipe_to_sql_dialect_mappings = self._get_recipe_to_sql_dialect_mappings()
        if len(recipe_to_sql_dialect_mappings) == 0:
            return ProjectStandardsCheckRunResult.not_applicable(
                message="No SQL recipes found in the project."
            )

        details = {}
        global_results = []

        global_results.extend(self._get_formatting_status(recipe_to_sql_dialect_mappings))

        total_sql_num_recipes = len(recipe_to_sql_dialect_mappings)

        total_n_formatting_changes = sum(
            [d.get("n_formatting_changes") for d in global_results]
        )

        avg_per_recipe_formatting_changes = round(
            total_n_formatting_changes / total_sql_num_recipes, 2
        )

        details.update(
            {
                d.get("name"): f"{d.get('n_formatting_changes')} formatting changes"
                for d in global_results
            }
        )
        if decision_criteria == "total":
            error_message = f"Identified {total_n_formatting_changes} formatting changes across all project SQL queries."
            decision_metric = total_n_formatting_changes
        elif decision_criteria == "average":
            error_message = f"Identified an average of {avg_per_recipe_formatting_changes} formatting changes per SQL query across the project."
            decision_metric = avg_per_recipe_formatting_changes

        if decision_metric > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=5, message=error_message, details=details
            )
        elif decision_metric > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=4, message=error_message, details=details
            )
        elif decision_metric > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=3, message=error_message, details=details
            )
        elif decision_metric > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=2, message=error_message, details=details
            )
        elif decision_metric > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=1, message=error_message, details=details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message=f"There were minimal identified formatting changes.",
                details=details,
            )
