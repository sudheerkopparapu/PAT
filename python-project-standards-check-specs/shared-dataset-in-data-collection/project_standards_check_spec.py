import dataiku
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from project_advisor.pat_tools import md_print_list

class HeavilySharedDatasetsAreInCollection(ProjectStandardsCheckSpec):

    def run(self):
        """
        Check if datasets shared in more than N projects exist in data collections.
        If they do, also check their documentation completeness.
        """     
        
        problem_count = 0
        problem_datasets = []
        documentation_issues = []
        datasets_with_doc_issues = []
        details = {}
        max_nb_downstream_projects = int(self.config.get('max_nb_downstream_projects'))
        check_documentation = self.config.get('check_documentation')
        check_if_dataset_contains_tag = self.config.get('check_if_dataset_contains_tag')
        check_if_dataset_contains_description = self.config.get('check_if_dataset_contains_description')
        check_if_dataset_columns_contains_description = self.config.get('check_if_dataset_columns_contains_description')

        
        # Checking Datasets in Data Collections
        
        self.client = dataiku.api_client()
        
        # Step 1: Get datasets shared in more than 2 projects
        exposed_objects = self.project.get_settings().get_raw().get("exposedObjects", {})
        datasets_to_check = []
        for obj in exposed_objects.get('objects', []):
            if obj['type'] == 'DATASET' and len(obj['rules']) > max_nb_downstream_projects:
                datasets_to_check.append(obj['localName'])
        print(f"Datasets shared to more than {max_nb_downstream_projects} projects: {datasets_to_check}")
        
        # Step 2: Check all data collections for these datasets
        matches = []
        all_collections = self.client.list_data_collections()
        for dc in all_collections:
            if dc.item_count > 0:  # Skip empty collections
                collection = self.client.get_data_collection(dc.id)
                objects = collection.list_objects()
                
                for obj in objects:
                    if obj.data['type'] == 'DATASET' and obj.data['id'] in datasets_to_check:
                        matches.append({
                            'dataset': obj.data['id'],
                            'collection': dc.display_name,
                            'project': obj.data['projectKey']
                        })
        
        # Step 3: Find datasets that are NOT in collections (the problem)
        datasets_in_collections = [match['dataset'] for match in matches]
        for dataset in datasets_to_check:
            if dataset not in datasets_in_collections:
                problem_count += 1
                problem_datasets.append(dataset)
        
        # Step 4: For datasets IN collections, check documentation completeness
        if check_documentation:
            for match in matches:
                dataset_name = match['dataset']
                project_key = match['project']
                collection_name = match['collection']

                print(f"Checking documentation for {dataset_name} in project {project_key}")

                try:
                    # Get the dataset from the project where it's stored
                    project_client = self.client.get_project(project_key)
                    dataset = project_client.get_dataset(dataset_name)
                    
                    # Check 0: Tags
                    tags = dataset.get_definition().get("tags", [])
                    has_tag = bool(tags and len(tags) > 0)
                    
                    # Check 1: Short description
                    short_desc = dataset.get_info().get_raw().get("shortDesc", "")
                    has_short_desc = bool(short_desc and short_desc.strip())

                    # Check 2: Long description
                    description = dataset.get_info().get_raw().get("description", "")
                    has_long_desc = bool(description and description.strip())

                    # Check 3: Column descriptions
                    schema = dataset.get_schema()
                    columns = schema.get('columns', [])
                    columns_without_comment = []

                    for col in columns:
                        if 'comment' not in col or not col['comment'].strip():
                            columns_without_comment.append(col['name'])

                    has_all_column_desc = len(columns_without_comment) == 0

                    # Build documentation issues
                    issues = []
                    
                    if not has_tag and check_if_dataset_contains_tag:
                        issues.append("missing tag")
                    if not has_short_desc and check_if_dataset_contains_description:
                        issues.append("missing short description")
                    if not has_long_desc and check_if_dataset_contains_description:
                        issues.append("missing long description")
                    if not has_all_column_desc and check_if_dataset_columns_contains_description:
                        issues.append(f"missing description in {len(columns_without_comment)} columns")
                    if issues:
                        problem_count += 1
                        datasets_with_doc_issues.append(dataset_name)
                        documentation_issues.append(f"{dataset_name} (in {collection_name}): {'; '.join(issues)}")

                except Exception as e:
                    problem_count += 1
                    datasets_with_doc_issues.append(dataset_name)
                    documentation_issues.append(f"{dataset_name}: Error checking documentation - {str(e)}")
        
        # Prepare details - combine all problematic datasets
        all_problem_datasets = list(set(problem_datasets + datasets_with_doc_issues))
        
        if problem_datasets:
            details[f"Dataset heavily shared (more than {max_nb_downstream_projects} times) not it data collections"] = md_print_list(problem_datasets, "dataset", self.original_project_key)
        
        if datasets_with_doc_issues:
            details["Datasets in data collections without complete documentation"] = md_print_list(datasets_with_doc_issues, "dataset", self.original_project_key)
        
        if all_problem_datasets:
            details["Datasets with data collection issues"] = md_print_list(all_problem_datasets, "dataset", self.original_project_key)
        
        # Return results
        if problem_count == 0:
            return ProjectStandardsCheckRunResult.success(
                message = "All heavily-shared datasets are properly documented and shared to data collections"
            )
        else:
            total_missing = len(problem_datasets)
            total_doc_issues = len(datasets_with_doc_issues)
            
            message_parts = []
            if total_missing > 0:
                message_parts.append(f"{total_missing} heavy-shared dataset(s) not in any data collection")
            if total_doc_issues > 0:
                message_parts.append(f"{total_doc_issues} dataset(s) with incomplete documentation: {documentation_issues}")
            
            summary_message = f"Issues found: {'; '.join(message_parts)}." if message_parts else f"Issues found with {len(all_problem_datasets)} dataset(s)."
            
            return ProjectStandardsCheckRunResult.failure(
                severity = int(self.config.get("severity")), 
                message = summary_message,
                details = details
            )
