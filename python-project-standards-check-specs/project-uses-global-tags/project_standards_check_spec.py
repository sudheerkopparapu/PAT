import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

from project_advisor.pat_tools import md_print_list

class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check that the project only uses global tags
        """
        self.client = dataiku.api_client()

        details = {}
        inst_tagCat= self.client.get_general_settings().get_raw()["globalTagsCategories"]
        all_global_tags=[]
        for i in inst_tagCat:
            category=i["name"]
            inst_globalTag=i["globalTags"]   
            for j in inst_globalTag:
                text=category + ":" + j["name"]
                all_global_tags.append(text)
        
        all_global_tags.extend(self.config.get("local_tags_to_ignore", []))

        #project tags
        project_tags = self.project.get_metadata()["tags"]
        local_project_tags = set(project_tags) - set(all_global_tags)

        details["local_project_tags"] = ", ".join(local_project_tags)
        
        project_to_review = False
        if local_project_tags:
            project_to_review = True

        #dataset tags
        project_datasets = self.project.list_datasets()
        datasets_to_review = set()
        non_global_dateset_tags = set()
        for dataset in project_datasets:
            dataset_tags = dataset["tags"]
            local_tags = set(dataset_tags) - set(all_global_tags)
            if len(local_tags) > 0:
                non_global_dateset_tags.update(local_tags)
                datasets_to_review.add(dataset.id)

        details["dataset_tags"] = ", ".join(non_global_dateset_tags)
        details["datasets_to_review"] = md_print_list(datasets_to_review, "dataset", self.original_project_key)

        #Webapp tags
        project_webapps = self.project.list_webapps()
        webapps_to_review = set()
        non_global_webapp_tags = set()

        for webapp in project_webapps:
            webapp_tags=webapp["tags"]
            local_tags = set(webapp_tags) - set(all_global_tags)
            if len(local_tags) > 0:
                non_global_webapp_tags.update(local_tags)
                webapps_to_review.add(webapp.id)
                  
        details["webapp_tags"] = ", ".join(non_global_webapp_tags)
        details["webapps_to_review"] = md_print_list(webapps_to_review, "webapp", self.original_project_key)

        #Dashboard tags
        project_dashboards = self.project.list_dashboards()
        dashboards_to_review = set()
        non_global_dashboard_tags = set()

        for dashboard in project_dashboards:
            dashboard_tags=dashboard["tags"]
            local_tags = set(dashboard_tags) - set(all_global_tags)
            if len(local_tags) > 0:
                non_global_dashboard_tags.update(local_tags)
                dashboards_to_review.add(dashboard.id)
        
        details["dashboard_tags"] = ", ".join(non_global_dashboard_tags)
        details["dashboards_to_review"] = md_print_list(dashboards_to_review, "dashboard", self.original_project_key)

        #Recipe tags
        project_recipes = self.project.list_recipes()
        recipes_to_review = set()
        non_global_recipe_tags = set()

        for recipe in project_recipes:
            recipes_tags=recipe["tags"]

            local_tags = set(recipes_tags) - set(all_global_tags)
            
            if len(local_tags) > 0:
                non_global_recipe_tags.update(local_tags)
                recipes_to_review.add(recipe.id)
        
        details["recipe_tags"] = ", ".join(non_global_recipe_tags)
        details["recipes_to_review"] = md_print_list(recipes_to_review, "recipe", self.original_project_key)
        
        # Summarize results
        if (project_to_review
            or datasets_to_review
            or webapps_to_review
            or dashboards_to_review 
            or recipes_to_review ):
            
            message = f"Local Tags are used in this project instead of global tags"
            if project_to_review:
                message += f", {len(local_project_tags)} local project tags to review"
            if datasets_to_review:
                message += f", {len(datasets_to_review)} dataset(s) to review"
            if webapps_to_review:
                message += f", {len(webapps_to_review)} webbapp(s) to review"
            if dashboards_to_review:
                message += f", {len(dashboards_to_review)} dashboard(s) to review"
            if recipes_to_review:
                message += f", {len(recipes_to_review)} recipe(s) to review"
            
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = message,
                    details = details
                )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = "This project leverages global tags properly",
                details = details
            )


