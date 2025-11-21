import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)

import re
from collections import defaultdict

from project_advisor.pat_tools import md_print_list

def _add(usage, env, where):
    if env:
        env = str(env).strip()
        if env:
            usage["code env: " + env].add(where)

class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
        
    def run(self):
        """
        Checks that the instance does not have any code environments with depreciated versions of python selected by the admin.
        Minimum acceptable version is used as the cutoff.
        """     

        self.client = dataiku.api_client()

        details = {}
        flagged_env_names = []
        code_env_usage = defaultdict(set)
        min_py_version = int(float(self.config.get("py_version")))
        
        # get project code env
        project_code_env = []
        project_settings = self.project.get_settings().get_raw()
        code_env_settings = project_settings['settings']['codeEnvs']['python']

        if code_env_settings['mode'] == 'EXPLICIT_ENV':
            code_env = code_env_settings['envName']
            project_code_env.append(code_env)

        details['project_code_evn'] = project_code_env[0] if project_code_env else 'BUILTIN or INHERITED'
        
        
        # get all code envs in python recipe explicity selected by the user
        py_recipe_code_envs = []
        py_code_recipes = []

        for recipe in self.project.list_recipes():

            if recipe['type'] == 'python' and recipe['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                code_env = recipe['params']['envSelection']['envName']
                py_recipe_code_envs.append(code_env)

                _add(code_env_usage, code_env, f"CODE_RECIPE : {recipe['name']}")
        
        
        # get all code envs in prepare recipes with python function steps
        prepare_recipe_code_envs = []
        prepare_recipe_names = [recipe['name'] for recipe in self.project.list_recipes() if recipe['type'] == 'shaker']

        for recipe_name in prepare_recipe_names:
            prepare_recipe_steps = self.project.get_recipe(recipe_name).get_settings().get_json_payload()['steps']
        
            for step in prepare_recipe_steps:
                try:
                    if step['type'] == 'PythonUDF' and step['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                        code_env = step['params']['envSelection']['envName']
                        prepare_recipe_code_envs.append(code_env)

                        _add(code_env_usage, code_env, f"PREPARED_RECIPE : {recipe_name}")
                except:
                    continue
         
        
        # get all code envs used in custom data quality checks
        checks_code_envs = []
        dataset_checks = [dataset['metricsChecks'] for dataset in self.project.list_datasets()]

        for checks in dataset_checks:
            for check in checks['checks']:
                if check['type'] == 'python' and check['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    code_env = check['envSelection']['envName']
                    checks_code_envs.append(code_env)
 
                    _add(code_env_usage, code_env, f"DATA_QUALITY_CHECK : {check['displayName']}")
                    
         
        
        # get all code envs used in custom metrics
        metrics_code_envs = []
        dataset_metrics = [dataset['metrics'] for dataset in self.project.list_datasets()]

        for metrics in dataset_metrics:
            for metric in metrics['probes']:
                if metric['type'] == 'python' and metric['configuration']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    code_env = metric['configuration']['envSelection']['envName']
                    metrics_code_envs.append(code_env)

                    _add(code_env_usage, code_env, f"METRIC : {metric['meta']['name']}")
             
            
        # get all code envs used notebooks
        notebook_code_envs = []

        notebooks = self.project.list_jupyter_notebooks()
        for notebook in notebooks:
            try:
                if notebook.get_content().get_metadata()['language_info']['name'] == 'python':
                    notebook_metadata = notebook.get_content().get_metadata()
                    display_name = notebook_metadata['kernelspec']['display_name']

                    match = re.search(r'env\s+([^)]+)', display_name)
                    if match:
                        code_env = match.group(1)
                        notebook_code_envs.append(code_env)

                        notebook_name = notebook.get_content().get_metadata()['kernelspec']['name']
                        _add(code_env_usage, code_env, f"PY_NOTEBOOK : {notebook_name}")
            except:
                continue
        
        # get all code envs used in webapps
        webapp_code_envs = []

        webapp_ids = [webapp['id'] for webapp in self.project.list_webapps()]
        for webapp_id in webapp_ids:
            webapp_settings = self.project.get_webapp(webapp_id).get_settings().get_raw()
            if webapp_settings['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                code_env = webapp_settings['params']['envSelection']['envName']
                webapp_code_envs.append(code_env)
                _add(code_env_usage, code_env, f"WEBAPP : {webapp_settings['name']}")
        
        
        # get all code envs used in custom scenarios and their triggers
        custom_scenario_code_env = []

        custom_scenario_ids = [scenario['id'] for scenario in self.project.list_scenarios() if scenario['type'] == 'custom_python']

        for scenario_id in custom_scenario_ids:
            custom_scenario = self.project.get_scenario(scenario_id)
            scenario_settings = custom_scenario.get_settings().get_raw()

            scenario_triggers = scenario_settings['triggers']
            custom_triggers = [trigger for trigger in scenario_triggers if trigger['type'] == 'custom_python']

            for custom_trigger in custom_triggers:
                if custom_trigger['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    trigger_code_env = custom_trigger['params']['envSelection']['envName']
                    custom_scenario_code_env.append(trigger_code_env)

                    _add(code_env_usage, trigger_code_env, f"SCENARIO_TRIGGER : {scenario_settings['name']}")

            if scenario_settings['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                code_env = scenario_settings['params']['envSelection']['envName']
                custom_scenario_code_env.append(code_env)

                _add(code_env_usage, code_env, f"SCENARIO : {scenario_settings['name']}")

        
        # get all code envs used in scenario steps and their triggers
        scenario_code_env = []

        scenario_ids = [scenario['id'] for scenario in self.project.list_scenarios() if scenario['type'] != 'custom_python']

        for scenario_id in scenario_ids:
            scenario = self.project.get_scenario(scenario_id)
            scenario_settings = scenario.get_settings().get_raw()

            scenario_triggers = scenario_settings['triggers']
            custom_triggers = [trigger for trigger in scenario_triggers if trigger['type'] == 'custom_python']

            for custom_trigger in custom_triggers:
                if custom_trigger['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    trigger_code_env = custom_trigger['params']['envSelection']['envName']
                    scenario_code_env.append(trigger_code_env)

                    _add(code_env_usage, trigger_code_env, f"SCENARIO_TRIGGER : {scenario_settings['name']}")

            scenario_steps = scenario_settings['params']['steps']
            for step in scenario_steps:
                if step['type'] == 'custom_python' and step['params']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    code_evn = step['params']['envSelection']['envName']
                    scenario_code_env.append(code_evn)

                    _add(code_env_usage, code_env, f"SCENARIO : {scenario_settings['name']}")
        
        
        # get code env used in agents
        agent_code_envs = []

        agent_ids = [agent['id'] for agent in self.project.list_saved_models() if agent['savedModelType'] == 'PYTHON_AGENT']
        for agent_id in agent_ids:
            agent_settings = self.project.get_saved_model(agent_id).get_settings().get_raw()
            
            if agent_settings['inlineVersions'][0]['pythonAgentSettings']['codeEnvSelection']['envMode'] == 'EXPLICIT_ENV':
                code_env = agent_settings['inlineVersions'][0]['pythonAgentSettings']['codeEnvSelection']['envName']
                agent_code_envs.append(code_env)

                _add(code_env_usage, code_env, f"AGENT : {agent_settings['name']}")
        
        
        # get code env used in saved model
        saved_model_code_envs = []

        model_ids = [model['id'] for model in self.project.list_saved_models() if model['savedModelType'] != 'PYTHON_AGENT']
        for model_id in model_ids:
            model_settings = self.project.get_saved_model(model_id).get_settings().get_raw()

            try:
                if model_settings['miniTask']['envSelection']['envMode'] == 'EXPLICIT_ENV':
                    code_env = model_settings['miniTask']['envSelection']['envName']
                    saved_model_code_envs.append(code_env)

                    _add(code_env_usage, code_env, f"SAVED_MODEL : {model_settings['name']}")
            except:
                continue
                
        # get code envs used in knowledge banks
        kb_code_envs = []

        knowledge_banks = self.project.list_knowledge_banks()

        for kb in knowledge_banks:

            kb['envSelection']['envMode'] == 'EXPLICIT_ENV'
            code_env = kb['envSelection']['envName']
            kb_code_envs.append(code_env)

            _add(code_env_usage, code_env, f"KNOWLEDGE_BANK : {kb['name']}")
        
       # get code env used in API services
        api_endpoint_code_evns = []

        api_services_ids = []
        for api_service in self.project.list_api_services():
            for endpoint in api_service['endpoints']:
                if endpoint['type'] in ['PY_FUNCTION', 'CUSTOM_PREDICTION']:
                    api_services_ids.append(api_service['id'])

        api_service_ids = list(set(api_services_ids))

        for api_service_id in api_service_ids:
            api_service_settings = self.project.get_api_service(api_service_id).get_settings().get_raw()
            endpoints = api_service_settings['endpoints']
            for endpoint in endpoints:
                try:
                    if endpoint['envSelection']['envMode'] == 'EXPLICIT_ENV':
                        code_env = endpoint['envSelection']['envName']
                        api_endpoint_code_evns.append(code_env)

                        _add(code_env_usage, code_env, f"API_SERVICE : {api_service_settings['name']}")
                except:
                    continue 
        
        # It isn't necessary to check these since they do not affect anything that is put into production. Check Saved Models instead
        # # get all code envs used in analysis & machine learning tasks
        # ml_task_code_envs = []

        # ml_tasks = project.list_ml_tasks()['mlTasks']

        # for ml_task in ml_tasks:
        #     ml_task_settings = project.get_ml_task(ml_task['analysisId'], ml_task['mlTaskId']).get_settings().get_raw()
        #     if ml_task_settings['envSelection']['envMode'] == 'EXPLICIT_ENV':
        #         code_env = ml_task_settings['envSelection']['envName']
        #         ml_task_code_envs.append(code_env)

        ### NOT POSSIBLE AT THE MOMENT ###
        # # get tool python envs 
        # tool_ids = [tool['id'] for tool in project.list_agent_tools()]
        

        # add code env names and usage to details to display       
        for env, locs in dict(code_env_usage).items():
            details[env] = list(set(locs))   # use set to dedupe
               
        # Combine all code env lists into one
        all_code_env_lists = [
            project_code_env,
            py_recipe_code_envs,
            prepare_recipe_code_envs,
            checks_code_envs,
            metrics_code_envs,
            notebook_code_envs,
            webapp_code_envs,
            custom_scenario_code_env,
            scenario_code_env,
            agent_code_envs,
            saved_model_code_envs,
            kb_code_envs,
            api_endpoint_code_evns
        ]

        # Flatten into one set to remove duplicates, then convert back to list
        project_code_envs = list(set().union(*all_code_env_lists))

        # Optional: sort for consistent output
        project_code_envs.sort()
        


        for code_env in project_code_envs: 
            code_env_settings = self.client.get_code_env('PYTHON', code_env).get_settings().get_raw()
            interpreter = code_env_settings['desc']['pythonInterpreter']
            py_version = interpreter.replace('PYTHON', '')
            print('hello')
            print(py_version)
            if int(py_version) < min_py_version:
                flagged_env_names.append(code_env)
                
        details['depreciated_interpreters'] = md_print_list(flagged_env_names, 'py_code_env', self.original_project_key) if flagged_env_names else 'None'

        if not project_code_envs:
            return ProjectStandardsCheckRunResult.not_applicable(
                message = f"This project has no code environments explicitly selected by a user.",
                details = details
            )
        
        if not flagged_env_names:
            return ProjectStandardsCheckRunResult.success(
                message = "There are no depreciated code environments used in the project.",
                details = details
            )
        
        else:
            return ProjectStandardsCheckRunResult.failure(
                    severity = int(self.config.get("severity")), 
                    message = f"Identified {len(flagged_env_names)} code environment(s) that use a depreciated interpreter.",
                    details = details
                )
            
