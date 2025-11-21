import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class MLUsageMetric(ProjectMetric):
    """
    Count the number of code recipes in a project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the MLUsageMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="ml_usage",
            metric_type=AssessmentMetricType.BOOLEAN,
            description="Usage of ML",
            dss_version_min=Version("3.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of ML elements in the project. ML can be:
        - LLM Recipes
        - Saved Models
        - Evaluation Stores
        - Score recipes
        - Knowledge bank
        - ML Flow experiment tracking.
        :return: self
        """
        result = {}
        overall_result = False
        # LLM related
        ml_recipe_types = ["score", "nlp_llm_user_provided_classification", "nlp_llm_rag_embedding", "nlp_llm_model_provided_classification","prompt", "nlp_llm_summarization", "nlp_llm_evaluation","nlp_llm_finetuning"]
        ml_recipe_counter = 0
        ml_recipe_ids = []
        recipes = self.project.list_recipes()

        for r in recipes:
            if r.type in ml_recipe_types:
                ml_recipe_counter += 1
                ml_recipe_ids.append(r.id)
        
        #other ML elements
        saved_models=self.project.list_saved_models()
        saved_model_ids = []
        saved_model_counter = 0
        for s in saved_models:
            saved_model_counter+= 1
            saved_model_ids.append(s['id'])

        model_evaluation_stores = self.project.list_model_evaluation_stores()
        model_evaluation_store_ids = []
        model_evaluation_store_counter = 0
        for me in model_evaluation_stores:
            model_evaluation_store_counter+= 1
            model_evaluation_store_ids.append(me.get_settings().get_raw()['id'])

        knowledge_banks = self.project.list_knowledge_banks(as_type='listitems')
        knowledge_bank_ids = []
        knowledge_bank_counter = 0 
        for kb in knowledge_banks:
            knowledge_bank_counter+= 1
            knowledge_bank_ids.append(kb['id'])

        mlflow_experiments= self.project.get_mlflow_extension().list_experiments(view_type='ACTIVE_ONLY', max_results=1000)
        mlflow_experiment_ids = []
        mlflow_experiment_counter = 0
        if bool(mlflow_experiments):
            for fl in mlflow_experiments['experiments']:
                mlflow_experiment_counter+= 1
                mlflow_experiment_ids.append(fl['experimentId'])

        total_count = ml_recipe_counter + saved_model_counter + model_evaluation_store_counter + knowledge_bank_counter + mlflow_experiment_counter
        if total_count>0:
            overall_result=True

        result["ml_recipe_types"] = ml_recipe_ids
        result["saved_model_ids"] = saved_model_ids
        result["model_evaluation_store_ids"] = model_evaluation_store_ids
        result["knowledge_bank_ids"] = knowledge_bank_ids
        result["mlflow_experiment_ids"] = mlflow_experiment_ids
        result["total_count"]= total_count

        self.value = overall_result
        self.run_result = result
        return self
