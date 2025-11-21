# This file is the implementation of custom agent tool project-standards
from dataiku.llm.agent_tools import BaseAgentTool
import dataiku
import json

class CustomAgentTool(BaseAgentTool):
    def set_config(self, config, plugin_config):
        self.config = config

    def get_descriptor(self, tool):
        return {
            "description": "Takes a project key and runs the Project Standards and return the status of each Project Standards.",
            "inputSchema" : {
                "$id": "https://dataiku.com/agents/tools/project_standards",
                "title": "Run Project Standards",
                "type": "object",
                "properties" : {
                    "project_key" : {
                        "type": "string",
                        "description": "Project key to run the project standards on. Do not set to use the default project"
                    }
                },
                "required": []
            }
        }

    def invoke(self, input, trace):
        """
        Run Project Standards on a project
        """
        args = input["input"]
        project_key = args.get("project_key")
        client = dataiku.api_client()

        if not project_key:
            project = client.get_default_project()
        else:
            project = client.get_project(project_key)

        ps_result = project.start_run_project_standards_checks().wait_for_result()

        return {
            "output":  json.dumps(ps_result.data),
            "sources":  [{
                "toolCallDescription": f"Project Standards ran for project {project_key}"
            }]
        }
