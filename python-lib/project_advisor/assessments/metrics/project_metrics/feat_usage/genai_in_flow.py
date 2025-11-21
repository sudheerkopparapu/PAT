import dataikuapi
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig


class GenAIinFlowMetric(ProjectMetric):
    """
    Metric to find out whether or not a project uses GenAI.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the GenAIinFlowMetric metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="has_genai_component",
            metric_type=AssessmentMetricType.BOOLEAN,
            description="GenAI component present in flow",
            dss_version_min=Version("12.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Metric to find out whether or not a project uses GenAI, meaning:
        Uses answers
        Uses prompt recipe
        Uses prompt studios
        Uses KB
        Uses llm powered nlp recipes
        Uses fine tuning.
        Uses LLM mesh python API in python recipe OR webapp

        :return: self
        """
        result = {}
        overall_result = False
        
        # Part 1:
        #  Uses llm powered nlp recipes
        #  Uses prompt recipe
        #  Uses fine tuning.

        genai_recipe_types = ["nlp_llm_user_provided_classification", "nlp_llm_rag_embedding", "nlp_llm_model_provided_classification","prompt", "nlp_llm_summarization", "nlp_llm_evaluation","nlp_llm_finetuning"]
        genai_recipe_counter = 0
        genai_recipe_ids = []
        recipes = self.project.list_recipes()

        for r in recipes:
            if r.type in genai_recipe_types:
                genai_recipe_counter += 1
                genai_recipe_ids.append(r.id)

        # Part 2 :
        # Uses KB

        knowledge_banks = self.project.list_knowledge_banks(as_type='listitems')
        knowledge_bank_ids = []
        knowledge_bank_counter = 0 
        for kb in knowledge_banks:
            knowledge_bank_counter+= 1
            knowledge_bank_ids.append(kb.get('id'))


        #  Uses prompt studios: API call not possible as of now 

        #  Uses LLM mesh python API in python recipe OR webapp: usage of get_llm()
        project_webapps= self.project.list_webapps()
        python_webapps_list = [w for w in project_webapps if w.get('type') in ['DASH','BOKEH','STANDARD']]


        genai_webapp_ids = []
        genai_webapp_counter=0
        for webapp in python_webapps_list:
            webapp_name = webapp.get("name")
            webapp_current = self.project.get_webapp(webapp.get("id"))
            settings = webapp_current.get_settings().get_raw()
            python_code = settings.get("params",{}).get("python")
            if python_code == None:
                python_code = ""
            if "get_llm(" in python_code:
                genai_webapp_counter+= 1
                genai_webapp_ids.append(webapp.get('id'))

        recipe_list = self.project.list_recipes()

        # Filter for Python code recipes
        python_recipes_list = [recipe for recipe in recipe_list if recipe.get('type') == 'python']
        genai_pythonrecipe_ids = []
        genai_pythonrecipe_counter=0 
        genai_used=False     
        for recipe in python_recipes_list:
            recipe_name = recipe.get("name")
            recipe = self.project.get_recipe(recipe_name)
            settings = recipe.get_settings()
            python_code = settings.get_payload()
                    
            if python_code == None:
                python_code = ""   
                
            list_of_strings = ['get_llm(', 'DKUChatLLM', 'DKUChatModel', 'langchain' ]

            for substring in list_of_strings:
                if substring in python_code:
                    genai_used=True
                    break
            if genai_used:
                genai_pythonrecipe_counter+= 1
                genai_pythonrecipe_ids.append(recipe_name)
            genai_used=False

                    
        #  Uses Answers

        project_webapps= self.project.list_webapps()
        answers_webapp_ids = []
        answers_webapp_counter=0
        for answers in project_webapps:
            if answers.get("type")=="webapp_document-question-answering_document-intelligence-explorer":
                answers_webapp_counter+= 1
                answers_webapp_ids.append(answers.get('id'))
        
        
        #Summary
        
        total_count = genai_recipe_counter + knowledge_bank_counter + answers_webapp_counter + genai_webapp_counter + genai_pythonrecipe_counter

        if total_count>0:
            overall_result=True 

        result["genai_recipe_ids"] = genai_recipe_ids
        result["genai_pythonrecipe_ids"] = genai_pythonrecipe_ids
        result["knowledge_bank_ids"] = knowledge_bank_ids
        result["answers_webapp_ids"]= answers_webapp_ids
        result["genai_webapp_ids"] = genai_webapp_ids
        result["total_count"]= total_count

        self.value = overall_result
        self.run_result = result    

        return self
