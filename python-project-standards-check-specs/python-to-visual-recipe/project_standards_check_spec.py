from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
import json

from langchain_core.messages import SystemMessage
from langchain_core.prompts.chat import HumanMessagePromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables.base import RunnableSequence

from project_advisor.pat_tools import dss_obj_to_dss_obj_md_link

class ProjectStandardsCheck(ProjectStandardsCheckSpec):
 
    def get_python_to_visual_chain(self) -> RunnableSequence:
        system_message_prompt = """
        You are a Dataiku DSS expert and a python expert.
        Your job is to identify if python code in a python recipe in Dataiku can be replaced by a visual recipe.
        As a reminder, the visual transformation recipes are:
        Sync : copy data from an input to an output Dataset
        Prepare : Transforms the data row by row
        Sample / Filter : Sample filter rows in a Dataset
        Group :  Aggregate the values of columns by the values of one or more keys.
        Distinct : Allows you to filter a dataset in order to remove some of its duplicate rows.
        Window :  Compute ordered window aggregations of columns by the values of one or more keys.
        Join : enrich one dataset with columns from another.
        Fuzzy join : joining datasets based on similarity matching conditions
        Geo join : joining datasets based on geographic conditions
        Split : Divides a dataset into two or more parts based on a condition
        Top N : Allows you to filter a dataset based on the top and bottom values of some of its rows.
        Sort : Allows you to sort the rows of an input dataset by the values of one or more columns in the dataset.
        Pivot : transforms datasets into pivot tables, which are tables of summary statistics
        Stack : Combines the rows of two or more datasets into a single output dataset
        """

        human_message = """
        Here is the python code recipe:
        {python_code}
        Please tell me if this python code can be replaced by a visual recipe in Dataiku DSS and which one to use. Format the response in a json format with the following keys:
        explanation : String
        convertible : Boolean
        visual_recipe : List[DSS visual recipes]

        If it is not possible reply {{"convertible" : false}}
        """
        model = self.llm.as_langchain_chat_model()
        messages = [
            SystemMessage(content=system_message_prompt),
            HumanMessagePromptTemplate(
                prompt=PromptTemplate.from_template(human_message)
            ),
        ]
        chat_template = ChatPromptTemplate.from_messages(messages)
        chain = chat_template | model | JsonOutputParser()
        return chain
    
    def run(self):
        """
        Check if python recipes can be converted to visual recipes
        """

        self.use_llm_powered_checks = self.plugin_config.get("use_llm_powered_checks")
        self.llm = self.project.get_llm(self.plugin_config.get("llm_id"))
        
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        details = {}
        
        if not self.use_llm_powered_checks:
            return ProjectStandardsCheckRunResult.not_applicable(
                message =  "PAT is not configured to run LLM Powered checks",
                details = details
            )
            
        python_recipes = []
        for recipe in self.project.list_recipes():
            if recipe["type"] == "python":
                python_recipes.append(recipe)
        
        if not python_recipes:
            return ProjectStandardsCheckRunResult.not_applicable(
                message =  "There are no python recipes to check in the project",
                details = details
            )
        
        chain = self.get_python_to_visual_chain()

        convertible_py_recipes = {}
        lines_of_code_to_save = 0
        for recipe in python_recipes:
            recipe_name = recipe["name"]
            recipe = self.project.get_recipe(recipe_name)
            settings = recipe.get_settings()
            python_code = settings.get_code()
            if python_code == None:
                res = {"convertible" : True, "explanation" : "Python Recipe has never been edited", "visual_recipe" : ["Sync"]}
            else:
                res = chain.invoke({"python_code": python_code})
            if res["convertible"] == True:
                link = dss_obj_to_dss_obj_md_link("recipe", self.original_project_key, recipe_name)
                convertible_py_recipes[recipe_name] = link + " " + res.get("explanation")
                lines_of_code_to_save += len(python_code.split("\n"))

        nbr_convertible_recipes = len(convertible_py_recipes)
        details["nbr_convertible_recipes"] = nbr_convertible_recipes
        details["lines_of_code_to_save"] = lines_of_code_to_save
        details.update(convertible_py_recipes)
        error_message = f"{nbr_convertible_recipes} python recipe(s) have been identified as convertible to visual recipes."
        

        if nbr_convertible_recipes >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = error_message,
                details = details
            )
        elif nbr_convertible_recipes >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = error_message,
                details = details
            )
        elif nbr_convertible_recipes >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = error_message,
                details = details
            )
        elif nbr_convertible_recipes >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = error_message,
                details = details
            )
        elif nbr_convertible_recipes >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = error_message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"None of the {len(python_recipes)} python recipes can be converted to visual recipes",
                details = details
            )
        
