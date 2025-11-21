import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class NumberOfTooBigPyRecipesMetric(ProjectMetric):
    """
    Count the number of "too big" python recipes in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the NumberOfTooBigPyRecipesMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_too_big_py_recipes",
            metric_type=AssessmentMetricType.INT,
            description="Number of too big python recipes",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["DESIGN_PATTERN"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of too big python code recipes in the project.
        :return: self
        """
        result = {}
        max_nbr_row_python_recipe = 500
        result = {
          'max_nbr_row_python_recipe': max_nbr_row_python_recipe,
          'recipe_ids': {}
         }

        # Get all recipes in the project
        recipe_list = self.project.list_recipes()

        # Filter for Python code recipes
        python_recipes_list = [recipe for recipe in recipe_list if recipe['type'] == 'python']

        for recipe in python_recipes_list:
            dss_recipe = recipe.to_recipe()
            python_code = dss_recipe.get_settings().get_code()
            if python_code == None:
                python_code = ""

            # Ignore blank lines, imports, and comments
            lines = [line for line in python_code.split("\n") 
                 if line != "" 
                 and not line.startswith("#")
                 and not line.startswith("import")
                 and not line.startswith("from")
                ]
            if len(lines) > max_nbr_row_python_recipe:
                result['recipe_ids'][dss_recipe.id] = len(lines)
        
        self.value = len(result['recipe_ids'])
        self.run_result = result
        return self
