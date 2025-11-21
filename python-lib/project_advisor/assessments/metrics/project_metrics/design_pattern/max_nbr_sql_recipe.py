import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class MaxNbrOfSqlRowsInRecipeMetric(ProjectMetric):
    """
    Max number of rows in a sql recipes in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the MaxNbrOfSqlRowsInRecipeMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="max_nbr_of_sql_rows_in_recipe",
            metric_type=AssessmentMetricType.INT,
            description="Max number of rows in a sql recipes in a project.",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["DESIGN_PATTERN"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes max number of rows in a sql recipes in a project.
        :return: self
        """
        result = {}
        max_nbr_row_sql_recipe=0
        allSQLRecipes = []

        # Get all recipes in the project
        recipe_list = self.project.list_recipes()

        # Filter for SQL code recipes
        sql_recipes_list = [recipe for recipe in recipe_list if recipe['type'] == 'sql_query']
            
        for recipe in sql_recipes_list:
            recipe_name = recipe["name"]
            recipe = self.project.get_recipe(recipe_name)
            settings = recipe.get_settings()
            sql_code = settings.get_payload()
                    
            if sql_code == None:
                sql_code = ""
            # Ignore blank lines, imports, and comments
            lines = sql_code.split("\n")
            lines = [line for line in lines if line.strip()]
            lines = [line for line in lines if not line.startswith("--")]
            lines = [line for line in lines if not line.startswith("import")]
            lines = [line for line in lines if not line.startswith("from")]
            allSQLRecipes.append(f'{recipe_name}: {len(lines)} rows')
            if max_nbr_row_sql_recipe<len(lines):
                max_nbr_row_sql_recipe=len(lines)

        result['all_sql_recipes']=f'SQL Recipes in project: {", ".join(allSQLRecipes)}'
        result['max_nbr_of_rows_in_sql_recipe']=max_nbr_row_sql_recipe

        self.value = max_nbr_row_sql_recipe
        self.run_result = result
        return self
