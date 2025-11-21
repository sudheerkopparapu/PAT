# This file is the actual code for the Python runnable sync-checks
import dataiku
from dataiku.runnables import Runnable

import re
import json
import os

class MyRunnable(Runnable):
    """The base interface for a Python runnable"""

    def __init__(self, project_key, config, plugin_config):
        """
        :param project_key: the project in which the runnable executes
        :param config: the dict of the configuration of the object
        :param plugin_config: contains the plugin settings
        """
        self.project_key = project_key
        self.config = config
        self.plugin_config = plugin_config

        self.consider_only_pat_checks = config.get("consider_only_pat_checks", True)
        self.add_to_scope = config.get("add_to_scope", False)
        self.scope_name = config.get("scope", "Default")
        self.ignore_checks = config.get("ignore_checks", False)
        self.checks_to_ignore = config.get("checks_to_ignore", [])
        
        self.client = dataiku.api_client()
        
    def get_progress_target(self):
        """
        If the runnable will return some progress info, have this function return a tuple of 
        (target, unit) where unit is one of: SIZE, FILES, RECORDS, NONE
        """
        return None
    
    def get_project_standard_check_spec_json(self, check_name : str, plugin_id : str):
        """
        Load projet standards check specs
        """

        plugin = self.client.get_plugin(plugin_id)
        check_name = "flow-size"
        file = plugin.get_file(f"python-project-standards-check-specs/{check_name}/project_standards_check_spec.json")

        decoded = file.data.decode('utf-8')
        def remove_comments(text):
            text = re.sub(r'//.*', '', text)
            text = re.sub(r'/\*.*?\*/', '', text, flags=re.DOTALL)
            return text
        cleaned = remove_comments(decoded)
        return json.loads(cleaned)


    def list_project_standard_specs(self):
        """
        Find all the implementations of Project Standards Check Specs in a plugins and return their ID.
        """
        pat_plugin_id = "instance-insights"
        client = dataiku.api_client()
        instance_info = client.get_instance_info()
        data_dir = instance_info.raw.get("dataDirPath")
        
        ps_specs = {}
        for plugin_type in ["installed", "dev"]:
            plugin_type_path = os.path.join(os.path.join(data_dir, "plugins"), plugin_type)
            if os.path.exists(plugin_type_path):
                plugin_names = os.listdir(plugin_type_path)
                for plugin_name in plugin_names:
                    keep_plugin = True
                    if plugin_name.startswith("."):
                        keep_plugin = False
                    if self.consider_only_pat_checks and plugin_name != pat_plugin_id:
                        keep_plugin = False
                    if keep_plugin:
                        ps_folder = os.path.join(plugin_type_path,plugin_name , "python-project-standards-check-specs")
                        if os.path.exists(ps_folder):
                            checks = os.listdir(ps_folder)
                            for check in checks:
                                ps_specs[f"project_standards_check_spec_{plugin_name}_{check}"] = {
                                    "ps_name" : check,
                                    "plugin_type" : plugin_type,
                                    "plugin_id" : plugin_name

                                }  
        return ps_specs
    
    def run(self, progress_callback):
        
        proj_stds = self.client.get_project_standards()
        ps_specs = self.list_project_standard_specs()
        
        # Find checks that are not added yet
        existing_checks = proj_stds.list_checks()
        existing_check_ids = [check.check_element_type for check in existing_checks]
        checks_to_add = set(ps_specs.keys()) - set(existing_check_ids)
        if self.ignore_checks:
            checks_to_add = checks_to_add - set(self.checks_to_ignore)
        
        ps_specs_to_add = {key: ps_specs[key] for key in checks_to_add}
        
        # Add the missing checks
        added_checks = []
        for ps_id in ps_specs_to_add.keys():
            added_checks.append(proj_stds.create_checks(ps_id)[0])

        # Update the scope
        if self.add_to_scope:
            # get scope
            scope = proj_stds.get_scope(self.scope_name)

            # Add newly added checks to scope
            checks = set(scope.checks)
            [checks.add(check.id) for check in added_checks]
            scope.checks = list(checks)

            # update scope
            scope.save()

        if not added_checks:
            message = "All PAT checks are up to date"
        else:
            message = f"Added {len(added_checks)} checks to the Project Standards Check lib.\nChecks : {[check.name for check in added_checks]} "
            if self.add_to_scope:
                message += f"scope {scope.name} was updated and now contains the following check : {scope.checks}"
        return message
