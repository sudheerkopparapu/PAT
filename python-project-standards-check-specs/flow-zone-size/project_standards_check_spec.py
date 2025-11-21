import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from dataikuapi.dss.flow import DSSProjectFlowGraph


class ProjectStandardsCheck(ProjectStandardsCheckSpec):
  
    def count_datasets_in_graph(self, graph: DSSProjectFlowGraph):
        nodes = graph.nodes
        count = len([name for name in nodes.keys() if "DATASET" in nodes[name]["type"]])
        return count
    
    def run(self):
        """
        Check that the Project flow zones are not too big
        """
 
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        flow = self.project.get_flow()
        zones = flow.list_zones()

        details = {}
        flow_zone_sizes = []
        
        if len(zones) == 0:
            nodes = flow.get_graph().nodes
            count = self.count_datasets_in_graph(flow.get_graph())
            flow_zone_sizes.append(count)
            message = f"This flow with no flow zones has too many datasets ({count}), split them up in into separate flow zones"
        else:
            big_zones = []
            for zone in zones:
                count = self.count_datasets_in_graph(zone.get_graph())
                flow_zone_sizes.append(count)
                if count > lowest_threshold:
                    big_zones.append(zone.name)
            message = f"{len(big_zones)} flow zone(s) identified with too many datasets. See: {big_zones}."
            details["big_zones"] = big_zones
        
        max_flow_zone_size = max(flow_zone_sizes)
        details["max_flow_zone_size"] = max_flow_zone_size
        details["avg_flow_zone_size"] = sum(flow_zone_sizes)/len(flow_zone_sizes)
        details["nbr_flow_zones"] = len(zones)
  
        if max_flow_zone_size > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif max_flow_zone_size > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif max_flow_zone_size > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif max_flow_zone_size > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif max_flow_zone_size > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message = f"The project's flow zones are under the recommended max number of datasets: {int(lowest_threshold)}",
                details = details
            )
        
