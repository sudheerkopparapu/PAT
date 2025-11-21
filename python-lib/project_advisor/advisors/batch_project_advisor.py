from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import dataiku
import dataikuapi
from project_advisor.advisors import DSSAdvisor
from project_advisor.advisors.project_advisor import ProjectAdvisor
from project_advisor.assessments import CheckSeverity
from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.metrics import DSSMetric
from project_advisor.pat_logging import logger


@dataclass
class ProjectFilters:
    """
    The ProjectFilters Class is used to filter projects when running the BatchProjectAdvisor.
    """

    project_keys: List[str] = field(default_factory=list)
    project_statuses: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    folder_id: str = ""


class BatchProjectAdvisor(DSSAdvisor):
    """
    The BatchProjectAdvisor Class runs the ProjectAdvisor on a set of projects.
    """
    project_folder : dataikuapi.dss.projectfolder.DSSProjectFolder
    project_advisors :List[ProjectAdvisor] = None

    def __init__(self,
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 project_filters: ProjectFilters,
                 pat_report_folder : dataiku.Folder
    ):

        super().__init__(client = client, 
                         config = config,
                         pat_report_folder = pat_report_folder
                       )
        logger.info("Init of BatchProjectAdvisor")
        self.project_filters = project_filters
        self.init_project_advisors()
        
    
    def run_checks(self) -> List[ProjectAdvisor]:
        """
        Run all the project checks over all of the projects.
        """
        logger.info(f"Running project checks on all the project advisors")
        [proj_advisor.run_checks() for proj_advisor in self.project_advisors]
        return self.project_advisors
    

    def run_metrics(self) -> List[ProjectAdvisor]:
        """
        Run the project metrics on all of the projects.
        """
        logger.info(f"Running metrics on all the project advisors")
        [proj_advisor.run_metrics() for proj_advisor in self.project_advisors]
        return self.project_advisors
    
    def run(self) -> None:
        """
        Run all the metrics and checks for a project.
        """
        logger.info(f"Running all of the project advisors")
        
        # Parallel run
        if self.config.config.get("run_config",{}).get("run_pat_in_parallel", False):  
            n_jobs = self.config.config.get("run_config",{}).get("nbr_parallel_runs",1)
            logger.info(f"Running {n_jobs} Project Advisors in parallel at a time")
            
            def parallel_run(pa):
                return pa.run()
            
            with ThreadPoolExecutor(max_workers = n_jobs) as executor:
                results = list(executor.map(parallel_run, self.project_advisors)) 
        else:
            logger.info(f"Running Project Advisors sequentially")
            [pa.run() for pa in self.project_advisors]
        
        return
    
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Save the metrics and checks for all the projects
        """
        logger.info(f"Saving all the metrics and checks for every project")
        
        metrics = []
        checks = []
        for pa in self.project_advisors:
            metrics.extend(pa.metrics)
            checks.extend(pa.checks)
        self.save_metrics(metrics, timestamp = timestamp, metric_type = "project")
        self.save_checks(checks, timestamp = timestamp, check_type = "project")
        return 
  
    def get_max_severity(self) -> str:
        """
        Return the average project score
        """
        logger.debug(f"Computing the batch project Max Severity")
        if len(self.project_advisors) == 0:
            return CheckSeverity.OK.name
        return CheckSeverity(max([project_advisor.get_max_severity_level() for project_advisor in self.project_advisors])).name
    
    def get_project_metric_list(self, metric_name : str) -> List[DSSMetric]:
        """
        Return the list of project metrics that match the metric_name
        """
        logger.debug(f"Return the list of projet metrics that match the metric_name {metric_name}")
        metric_list = []
        for pa in self.project_advisors:
            for m in pa.metrics:
                if m.name == metric_name:
                    metric_list.append(m)
        return metric_list
    
    def recursive_project_search(self, folder: dataikuapi.dss.projectfolder.DSSProjectFolder) -> List[str]:
        """
        Recursive function to find all projects in a given folder.
        """
        project_keys = []
        project_keys.extend(folder.list_project_keys())
        for child_folder in folder.list_child_folders():
            project_keys.extend(self.recursive_project_search(child_folder))
        return project_keys
            
        
    def init_project_advisors(self) -> None:
        """
        Finds all the relevant project.
        Build and save a ProjectAdvisor for each project.
        """
        logger.info(
            f"Creating a ProjectAdvisor for every project that fit the filter description : {self.project_filters}"
        )

        # Process filter settings
        project_status_list = self.project_filters.project_statuses
        folder_id = self.project_filters.folder_id
        tags = self.project_filters.tags

        # Keep projects filter folder (FILTER 1)
        if len(folder_id) == 0:
            self.project_folder = self.client.get_root_project_folder()
        else:
            self.project_folder = self.client.get_project_folder(folder_id)
        project_keys = self.recursive_project_search(self.project_folder)

        # Filter by project keys (FILTER 2)
        if len(self.project_filters.project_keys) > 0:
            project_keys = [pk for pk in project_keys if pk in self.project_filters.project_keys]

        # Helper function
        def init_or_filter_project_advisor(project_key : str) -> Optional[ProjectAdvisor]:
            """
            init or filter project advsior to run in parallel
            Retir
            """
            project = self.client.get_project(project_key)

            # Filter by projet status (FILTER 3 - Requiring Project Object)
            if len(project_status_list) > 0:
                # Filter out project with status not in list.
                proj_status = project.get_settings().settings.get("projectStatus")
                if proj_status not in project_status_list:
                    logger.debug(f"Removing project {project_key} because project status {proj_status} is filtered out")
                    return None

            # Filter by project tags (FILTER 4 - Requiring Project Object)
            if len(tags) > 0:
                # Filter out project with no tags in list.
                proj_tags = project.get_tags()["tags"].keys()
                if not any(tag in tags for tag in proj_tags):
                    logger.debug(f"Removing project {project_key} because project tags {proj_tags} are filtered out")
                    return None

            proj_advisor = ProjectAdvisor(
                client=self.client, config=self.config, project=project, pat_report_folder=self.pat_report_folder
            )
            if proj_advisor.user_has_permissions(user_id):
                logger.debug(f"Project {project_key} has been added")
                return proj_advisor
            else:
                logger.warning(
                    f"Removing project {project_key} because user {user_id} doesn't have permissions to run PAT on this project"
                )
                return None

        # Build project_advisor list
        project_advisors = []
        user_id = ProjectAdvisor.get_auth_user()
        
        # Parallel run
        if self.config.config.get("run_config",{}).get("run_pat_in_parallel", False):  
            n_jobs = self.config.config.get("run_config",{}).get("nbr_parallel_runs",1)
            logger.info(f"Initializing {n_jobs} Project Advisors in parallel at a time")

            with ThreadPoolExecutor(max_workers = n_jobs) as executor:
                project_advisors = list(executor.map(init_or_filter_project_advisor, project_keys)) 
        else:
            logger.info(f"Initializing Project Advisors sequentially")
            project_advisors = [init_or_filter_project_advisor(project_key) for project_key in project_keys]
        
        # Remove None from the project_advisor list (comming from second filtering)
        project_advisors = [x for x in project_advisors if x is not None]
        self.project_advisors = project_advisors
        
        
        
        
        