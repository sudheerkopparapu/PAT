import dataikuapi
import dataiku
from typing import List, Any
from abc import ABC, abstractmethod
from types import ModuleType
from pathlib import Path
import os
import io
import importlib
import sys, inspect
import pandas as pd
import json

from datetime import datetime

from project_advisor.pat_backend import PATBackendClient

from project_advisor.assessments.config import DSSAssessmentConfig
from project_advisor.assessments.dss_assessment import DSSAssessment

from project_advisor.assessments.metrics import DSSMetric
from project_advisor.assessments.metrics.project_metric import ProjectMetric

from project_advisor.assessments.checks import DSSCheck
from project_advisor.assessments.checks.project_check import ProjectCheck

from project_advisor.pat_logging import logger

class DSSAdvisor(ABC):
    """
    An abstract base class for computing metrics and checks on DSS.
    """

    client: dataikuapi.dssclient.DSSClient = None
    config: DSSAssessmentConfig = None
    metrics : List[DSSMetric] = None
    checks : List[DSSCheck] = None
    pat_report_folder : dataiku.Folder = None

    def __init__(self, 
                 client: dataikuapi.dssclient.DSSClient, 
                 config: DSSAssessmentConfig,
                 pat_report_folder : dataiku.Folder
                ):
        """
        Initializes the DSSAdvisor with the provided client and configuration.
        """
        self.client = client
        self.config = config
        self.pat_report_folder = pat_report_folder


    @abstractmethod
    def run_metrics(self, timestamp : datetime) -> List[DSSMetric]:
        """
        Abstract method to run all metrics and return the Metrics.
        """
        return
  
    @abstractmethod
    def run_checks(self, timestamp : datetime) -> List[DSSCheck]:
        """
        Abstract method to run all checks and return the Checks.
        """
        return

    @abstractmethod
    def run(self) -> None:
        """
        Abstract method to run all the metrics and checks.
        """
        return
    
    @abstractmethod
    def get_max_severity(self) -> float:
        """
        Abstract method to compute the score overall score of the advisor.
        """
        return
    
    @abstractmethod
    def save(self, timestamp : datetime = datetime.now()) -> None:
        """
        Abstract method to save all the checks to a dataset in the flow.
        """
        return
    
    def format_ts(self, timestamp : datetime):
        """
        Format timestamp to act as the ID of the Assessment.
        """
        return timestamp.isoformat().split(".")[0]
    
    def safe_json_to_str(self, data : dict) -> str:
        try:
            return json.dumps(data)
        except Exception as error:
            return json.dumps({"pat_report_logging_error" : str(error)})
    
    def write_dataframe_to_pat_report_folder(self, path_in_folder: str, filename: str, df : pd.DataFrame):
        """
        Writes a pandas DataFrame to a Dataiku folder as a CSV using the stream method.
        """
        # Construct full path in folder
        filename = filename +".csv"
        full_path = f"{path_in_folder}/{filename}" if path_in_folder else filename

        # Write DataFrame to a CSV string
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)

        with self.pat_report_folder.get_writer(full_path) as stream:
            stream.write(buffer.getvalue().encode("utf-8"))
    
    def save_metrics(self, metrics : List[DSSMetric], timestamp : datetime, metric_type : str) -> None:
        """
        Method to save the metrics to a report folder in the flow.
        """
        logger.debug(f"Logging {len(metrics)} metrics to the flow")
        #self.init_metric_logging_dataset()

        ts_str = self.format_ts(timestamp)
        metric_records = []
        for metric in metrics:
            project_key = ""
            if isinstance(metric, ProjectMetric):
                project_key = metric.project.project_key
            metric_record = {
                    "timestamp": ts_str,
                    "project_id": project_key,
                    "tags" : metric.print_tags(),
                    "metric_name": metric.name,
                    "metric_value": metric.value,
                    "metric_type" : metric.metric_type.name,
                    "status": metric.status.name,
                    "result_data": self.safe_json_to_str(metric.get_metadata()),
                }
            logger.debug(f"[metric_record]{json.dumps(metric_record)}") # Logging report metric to job log
            metric_records.append(metric_record)
        
        new_metrics_df = pd.DataFrame.from_dict(metric_records)
        self.write_dataframe_to_pat_report_folder(path_in_folder = f"metrics/{metric_type}", filename = ts_str, df = new_metrics_df)


    def save_checks(self,checks : List[DSSCheck], timestamp : datetime, check_type : str) -> None:
        """
        Method to save all the checks to a report folder in the flow.
        """
        logger.debug(f"Logging {len(checks)} checks to the flow")
        
        #self.init_check_logging_dataset()
        
        ts_str = self.format_ts(timestamp)
        check_records = []
        for check in checks:
            project_key = ""
            if isinstance(check, ProjectCheck):
                project_key = check.project.project_key

            check_record = {
                                "timestamp": ts_str,
                                "project_id": project_key,
                                "tags" : check.print_tags(),
                                "check_name": check.name,
                                "severity": check.check_severity.value,
                                "message": check.message,
                                "check_params" : self.safe_json_to_str(check.check_params),
                                "status": check.status.name,
                                "result_data": self.safe_json_to_str(check.get_metadata()),
                            }

            logger.debug(f"[check_record]{json.dumps(check_record)}") # Logging report metric to job logs
            check_records.append(check_record)

        new_checks_df = pd.DataFrame.from_dict(check_records)
        self.write_dataframe_to_pat_report_folder(path_in_folder = f"checks/{check_type}", filename = ts_str, df = new_checks_df)
        return
    

#     def init_metric_logging_dataset(self) -> None:
#         """
#         Init the metric logging dataset if empty or if there is no data.
#         """
#         logger.debug(f"Init the metric logging dataset if empty or if there is no data.")
        
#         df_init = pd.DataFrame(
#             {
#                 "timestamp": pd.Series(dtype="str"),
#                 "project_id": pd.Series(dtype="str"),
#                 "tags": pd.Series(dtype="str"),
#                 "metric_name": pd.Series(dtype="str"),
#                 "metric_value": pd.Series(dtype="str"),
#                 "metric_type": pd.Series(dtype="str"),
#                 "status": pd.Series(dtype="str"),
#                 "result_data": pd.Series(dtype="str"),
#             }
#         )
#         try:
#             self.metric_report_dataset.get_dataframe()
#         except:
#             self.metric_report_dataset.write_schema_from_dataframe(df_init)
#             self.metric_report_dataset.write_from_dataframe(df_init)
#         return
    
#     def init_check_logging_dataset(self) -> None:
#         """
#         Init the check logging dataset if empty or if there is no data.
#         """
#         logger.debug(f"Init the check logging dataset if empty or if there is no data.")
        
#         df_init = pd.DataFrame(
#             {
#                 "timestamp": pd.Series(dtype="str"),
#                 "project_id": pd.Series(dtype="str"),
#                 "tags": pd.Series(dtype="str"),
#                 "check_name": pd.Series(dtype="str"),
#                 "severity": pd.Series(dtype="int"),
#                 "message": pd.Series(dtype="str"),
#                 "check_params" : pd.Series(dtype="str"),
#                 "status": pd.Series(dtype="str"),
#                 "result_data": pd.Series(dtype="str"),
#             }
#         )
#         try:
#             self.check_report_dataset.get_dataframe()
#         except:
#             self.check_report_dataset.write_schema_from_dataframe(df_init)
#             self.check_report_dataset.write_from_dataframe(df_init)
#         return
    
    def fetch_built_in_and_add_on_classes(self, root_module : ModuleType, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the built-in and add on module_class sub classes.
        This requires the macro to be impersonated.
        """
        logger.debug(f"Find all the built-in and add on subclasses of {module_class}")
        
        built_in_classes = self.fetch_classes(root_module, module_class)
        add_on_classes = self.fetch_add_on_classes(module_class)
        return built_in_classes + add_on_classes

    def fetch_add_on_classes(self, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the module_class sub classes within the default project lib.
        """
        logger.debug(f"Find all custom subclasses of {module_class} in default project lib")
        
        try:
            local_client = dataiku.api_client()
            project_key = local_client.get_default_project().project_key
            dataDirPath = local_client.get_instance_info().raw["dataDirPath"]
            proj_py_lib_root = dataDirPath + f"/config/projects/{project_key}/lib/python"
            sys.path.append(proj_py_lib_root)
            
            import pat_custom_assessments
            
            classes = self.fetch_classes(pat_custom_assessments, module_class)
            return classes
        except Exception as error:
            # Case were no custom assessments have been provided in the "pat_custom_assessments" Folder.
            logger.debug(f"Failed to load custom assessment classes from project libraries folder 'pat_custom_assessments', error : {str(error)}")
            return []
    
    
    def fetch_classes(self, root_module : ModuleType, module_class : ModuleType) -> List[ModuleType]:
        """
        Find all the module_class sub classes within a root_module.
        """
        logger.debug(f"Finding all subclasses of {module_class}")
        
        module_folder_root = Path(root_module.__path__[0])
        base_module_name = root_module.__name__

        modules = []
        for root, subFolder, files in os.walk(module_folder_root):
            for item in files:
                if item.endswith(".py") and item != "__init__.py":
                    path = Path(root, item)
                    rel_path = path.relative_to(module_folder_root)
                    module_name = (
                        base_module_name
                        + "."
                        + rel_path.as_posix()[:-3].replace("/", ".")
                    )
                    module = importlib.import_module(module_name, package=None)
                    modules.append(module)

        classes = []
        for module in modules:
            for _, c in inspect.getmembers(module, inspect.isclass):
                if (
                    issubclass(c, module_class)
                    and module_class != c
                ):
                    classes.append(c)
        return classes
    
    def filter_assessments(self, assessments : List[DSSAssessment]) -> List[DSSAssessment]:
        """
        Filter DSSAssessment based on the DSSAssessmentConfig and Class parameters.
        """
        logger.debug(f"Filtering assessments bases on assessment configurations")
        
        start_count_assessments = len(assessments)
        if start_count_assessments==0:
            return assessments
        
        # Load filters
        filter_config = self.config.get_config().get("check_filters",{})
        
        # Run filtering all all assessments
        filtered_assessments = [assessment for assessment in assessments if not assessment.filter(filter_config)]
        
        logger.debug(f"Assessments filtered from {start_count_assessments} to {len(filtered_assessments)}")
        return filtered_assessments
    
    
