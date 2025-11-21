import dataikuapi
import pandas as pd
from itertools import combinations
from typing import List
import time

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments import InstanceCheckCategory, CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.checks.instance_check import InstanceCheck


from project_advisor.advisors.batch_project_advisor import BatchProjectAdvisor


class CodeEnvEmbeddedCheck(InstanceCheck):
    """
    A class used to check if any code environments are contained within others.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        batch_project_advisor : BatchProjectAdvisor,
        metrics : List[DSSMetric]
    ):
        """
        Initializes the CodeEnvEmbeddedCheck instance with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            metrics = metrics,
            batch_project_advisor = batch_project_advisor,
            tags=[InstanceCheckCategory.USAGE.name],
            name="code_env_embedded_check",
            description="Check if any code environments are contained within others.",
        )


    def get_code_environments(self, lang):
        """
        Retrieve all code environments of a specific language, excluding plugins, those with names starting with 'solution_' or 'INTERNAL_' 
        """
        return [
            env for env in self.client.list_code_envs() if env['envLang'] == lang and env['deploymentMode'] != 'PLUGIN_MANAGED' 
            and not env['envName'].startswith('solution_') and not env['envName'].startswith('INTERNAL_')
        ]

    def get_code_env_packages(self, env_lang, env_name):
        """
        Retrieve package list for a specific code environment
        """
        code_env = self.client.get_code_env(env_lang=env_lang, env_name=env_name)
        packages = code_env.get_definition().get('actualPackageList', "")

        if env_lang == 'PYTHON':
            package_set = {(pkg.split('==')[0], pkg.split('==')[1]) for pkg in packages.split('\n') if '==' in pkg}
        elif env_lang == 'R':
            package_set = {(pkg.split(',')[0].strip('"'), pkg.split(',')[1].strip('"')) for pkg in packages.split('\n') if ',' in pkg}
        else:
            package_set = set()

        return package_set

    def is_contained(self, smaller, larger):
        """
        Check if smaller environment's packages are contained in the larger environment
        """
        smaller_dict = dict(smaller)
        larger_dict = dict(larger)
        return all(
            smaller_dict.get(pkg, None) == larger_dict.get(pkg, None)
            for pkg in smaller_dict
        )

    def find_contained_environments(self, lang):
        """
        Main function to find contained environments for a specific language
        """
        code_envs = self.get_code_environments(lang)
        env_packages = {}

        # Retrieve packages for all filtered code environments
        for env in code_envs:
            env_name = env['envName']
            env_packages[env_name] = self.get_code_env_packages(lang, env_name)

        contained_envs = set()
        equal_envs = set()
        explanations = []
        env_names = list(env_packages.keys())

        # Sort environments by the number of packages
        env_names.sort(key=lambda name: len(env_packages[name]))

        # Compare each pair of environments, considering length of package lists
        for i, env1 in enumerate(env_names):
            for j in range(i + 1, len(env_names)):
                env2 = env_names[j]
                if self.is_contained(env_packages[env1], env_packages[env2]):
                    contained_envs.add(env1)
                    explanations.append(f"Code environment '{env1}' is contained in code environment '{env2}'")
                    break
                elif len(env_packages[env1]) == len(env_packages[env2]) and env_packages[env1] == env_packages[env2]:
                    equal_envs.add((env1, env2))

        if contained_envs or equal_envs:
            result = {lang: list(contained_envs)}
            if equal_envs:
                result[f"equal_code_env_{lang}"] = list(equal_envs)
            return True, f"there are {len(contained_envs)} {lang} code environment(s) contained in other code environments", result, explanations
        else:
            return False, f"there is no embedded {lang} code environment", {}, explanations

    def run(self) -> InstanceCheck:
        """
        Check that no code environement is contained in another.
        :return: self
        """
        start_time = time.time()  # Start timing

        explanations = []

        # Check for Python code environments
        python_envs = self.get_code_environments('PYTHON')
        if len(python_envs) < 2:
            python_check = False
            python_message = "there is not enough Python code environments to perform the search"
            python_result = {}
            python_explanations = []
        else:
            python_check, python_message, python_result, python_explanations = self.find_contained_environments('PYTHON')

        explanations.extend(python_explanations)

        # Check for R code environments
        r_envs = self.get_code_environments('R')
        if len(r_envs) < 2:
            r_check = False
            r_message = "there is not enough R code environments to perform the search"
            r_result = {}
            r_explanations = []
        else:
            r_check, r_message, r_result, r_explanations = self.find_contained_environments('R')

        explanations.extend(r_explanations)

        # Aggregate results
        if python_check or r_check: # Ie. There is at least one code env (python or R) that is contained in another one.
            check_pass = False 
            message = f"For Python, {python_message} ; For R, {r_message}"
            self.run_result = {
                        'PYTHON': python_result.get('PYTHON', []),
                        'R': r_result.get('R', []),
                        'equal_code_env_PYTHON': python_result.get('equal_code_env_PYTHON', []),
                        'equal_code_env_R': r_result.get('equal_code_env_R', []),
                        'explanations': explanations,
                        'execution_time': time.time() - start_time
                    }
        else:
            check_pass = True
            if len(python_envs) < 2 and len(r_envs) < 2:
                message = "There are not enough code environments to perform the search"
            else:
                message = "The search ran and there are no embedded code envs"
                self.run_result = {
                        'explanations': explanations,
                        'execution_time': time.time() - start_time
                    }

        if check_pass:    
            self.check_severity = CheckSeverity.OK
        else:
            self.check_severity = CheckSeverity.MEDIUM
        self.message = message

        return self