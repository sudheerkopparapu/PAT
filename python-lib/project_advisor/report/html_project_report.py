import dataikuapi
import pandas as pd

from project_advisor.advisors.project_advisor import ProjectAdvisor
from project_advisor.assessments.dss_assessment import DSSAssessment

from typing import Any, Dict, List
from abc import ABC

from project_advisor.pat_logging import logger

class HtmlProjectReportGenerator(ABC):
    """
    Class to generate an html report for a ProjectAdvisor
    """
    
    project_advisor : ProjectAdvisor = None
    
    def __init__(self, project_advisor : dataikuapi.dss.project.DSSProject):
        """
        Initializes Html Project Report Generator
        """
        self.project_advisor = project_advisor
    
    def generate(self) -> str:
        """
        Generating project report.
        """
        
        max_severity = self.project_advisor.get_max_severity()
        
        checks_df = self.get_checks_df()
        logger.info(f"Generating HTML report for {len(checks_df.index)} checks")
        checks_df = checks_df[checks_df["status"] == "RUN_SUCCESS"]
        checks_df.drop(columns=['status'], inplace = True)
        
        severity_counts = checks_df["severity_level"].value_counts().to_dict()
        logger.debug(f" check severity counts : {severity_counts}")
        
        nbr_critical_checks = severity_counts.get(5,0)
        nbr_high_checks = severity_counts.get(4,0)
        nbr_medium_checks = severity_counts.get(3,0)
        nbr_low_checks = severity_counts.get(2,0)
        nbr_lowest_checks = severity_counts.get(1,0)
        nbr_ok_checks = severity_counts.get(0,0)
        recommendation_tables = self.get_failed_checks_html(checks_df)
        style = self.get_style_html()
        status_message = f"You have {len(checks_df.index) - nbr_ok_checks} remaining recommendations on how to improve your project with the following severities"
        project_name = self.project_advisor.project.get_metadata().get("label")

        # Build report HTML
        report_html = """
                <head>
                  {style}
                  <title>PAT Report</title>
                  <h1>PAT Report for {project_name}</h1>
                  <h2>Max Project Severity : {max_severity}</h2>
                  <h3 class="success"> You have successfully passed {nbr_ok_checks} checks! </h3>
                  <h3 class="status"> {status_message} </h3>
                  <h4 > CRITICAL : {nbr_critical_checks} </h4>
                  <h4 > HIGH : {nbr_high_checks} </h4>
                  <h4 > MEDIUM : {nbr_medium_checks} </h4>
                  <h4 > LOW : {nbr_low_checks} </h4>
                  <h4 > LOWEST : {nbr_lowest_checks} </h4>
                  <h3>See the following recommendations</h3>
                </head>
                <body>
                {recommendation_tables}
                </body>
                """.format(style = style,
                           project_name = project_name,
                           max_severity = max_severity,
                           status_message = status_message,
                           nbr_ok_checks = nbr_ok_checks, 
                           nbr_critical_checks = nbr_critical_checks, 
                           nbr_high_checks = nbr_high_checks, 
                           nbr_medium_checks = nbr_medium_checks, 
                           nbr_low_checks = nbr_low_checks, 
                           nbr_lowest_checks = nbr_lowest_checks, 
                           recommendation_tables = recommendation_tables)
        

        return report_html
    
    def get_style_html(self):
        status = self.project_advisor.get_max_severity()
        if status == "OK":
            color = "green"
        elif status in ["CRITICAL"]:
            color = "red"
        elif status in ["HIGH"]:
            color = "orange"
        else:
            color = "blue"
        
        style = """
            <style>
                h3.status {{
                  color: {color};
                  font-family: verdana;
                  font-size: 100%;
                }}
                h3.success {{
                  color: green;
                  font-family: verdana;
                  font-size: 100%;
                }}
            </style>
            """.format(color = color)
        return style
    
    def get_checks_df(self) -> pd.DataFrame:
        
        check_records = []
        for check in self.project_advisor.checks:
            check_record = {
                "check_name": check.name,
                "tags": check.print_tags(),
                "description": check.description,
                "check_params" : check.check_params,
                "severity": check.check_severity.name,
                "severity_level": check.check_severity.value,
                "status" : check.status.name,
            }
            check_records.append(check_record)
        
        if len(check_records) == 0:
            column_names = ["check_name","tags","description","check_params", "severity","severity_level","status"]
            checks_df = pd.DataFrame(columns=column_names)
        else:    
            checks_df = pd.DataFrame.from_dict(check_records)
        return checks_df
    
    
    def get_failed_checks_html(self, df) -> str:
        """
        Return html table of all the failed checks by category
        """
        
        failed_check_df = df[df["severity"] != "OK"]
        all_tags = set()
        for tags in failed_check_df["tags"]:
            all_tags.update(DSSAssessment.load_tags_str(tags))
        
        tag_tables_html = ""
        for tag in all_tags:
            logger.debug(f"Building table for tag : {tag}")
            has_tag = [tag in tags for tags in failed_check_df["tags"]]
            tag_df = failed_check_df[has_tag]
            tag_df.sort_values(by='severity_level', inplace = True, ascending=False)
            tag_df.drop(columns=['tags', 'severity_level'], inplace = True)
            
            tag_tables_html += "<h1>{tag}</h1>".format(tag = tag)
            
            
            tag_tables_html += tag_df.to_html(index = False)
        
        return tag_tables_html