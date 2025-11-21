import dataikuapi
from datetime import datetime
from typing import List
from packaging.version import Version

from project_advisor.assessments.metrics import AssessmentMetricType
from project_advisor.assessments.metrics.project_metric import ProjectMetric
from project_advisor.assessments.config import DSSAssessmentConfig
from collections import Counter


class NumberOfWikiArticles(ProjectMetric):
    """
    List all the wiki articles in the project.
    """

    def __init__(
        self,
        client: dataikuapi.dssclient.DSSClient,
        config: DSSAssessmentConfig,
        project: dataikuapi.dss.project.DSSProject,
    ):
        """
        Initializes the Metric class with the provided client, config, and project.
        """
        super().__init__(
            client=client,
            config=config,
            project=project,
            name="nbr_of_wiki_articles",
            metric_type=AssessmentMetricType.INT,
            description="Number of wiki articles in the project.",
            dss_version_min=Version("5.0.0"),
            dss_version_max=None,  # Latest
            tags = ["FEATURE_USAGE"]
        )

    def run(self) -> ProjectMetric:
        """
        Computes the number of wiki articles in the project.
        :return: self
        """
        result = {}

        articles_list = self.project.get_wiki().list_articles()
        article_titles = [
            l.get_data().get_metadata().get("name") for l in articles_list
        ]

        days_since_last_update = None
        if len(articles_list) > 0:
            latest_ts_ms = max(
                [
                    (
                        l.get_data()
                        .get_metadata()
                        .get("versionTag")
                        .get("lastModifiedOn")
                        if l.get_data().get_metadata().get("versionTag")
                        else 0
                    ) # some articles have no 'last modified' (likely because projects were imported)
                    for l in articles_list
                ]
            )
            days_since_last_update = (
                datetime.now() - datetime.fromtimestamp(latest_ts_ms / 1000)
            ).days

        result["article_titles"] = article_titles
        result["days_since_last_wiki_update"] = days_since_last_update

        self.run_result = result
        self.value = len(articles_list)

        return self
