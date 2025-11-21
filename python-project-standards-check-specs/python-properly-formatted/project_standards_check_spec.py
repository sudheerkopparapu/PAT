import dataiku
import dataikuapi
from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from yapf.yapflib.yapf_api import FormatCode
from yapf.yapflib.errors import YapfError

from typing import List, Dict, Tuple
from dataikuapi.dss.projectlibrary import DSSLibraryFile
from dataikuapi.dss.projectlibrary import DSSLibraryFolder


class ProjectStandardsCheck(ProjectStandardsCheckSpec):

    def _get_formatting_status(
        self, py_scripts: List[Tuple[str, str]]
    ) -> List[Dict[str, int]]:
        """

        Args:
            py_scripts (List[Tuple[str,str]]): Tuple containing file names (for exception handling) and string Python script

        Returns:
            List[Dict[str, int]]: Dictionary contain number of lines in script and number of lines to be formatted
        """
        results = []
        for script in py_scripts:
            n_lines = script[1].count("\n")
            try:
                n_lines_to_format = FormatCode(
                    script[1], print_diff=True, style_config=self.format_style
                )[0].count("\n-")
            except YapfError:
                raise Exception(
                    f"Found a syntax error in {script[0]}; unable to evaluate formatting.",
                )

            results.append(
                {
                    "name": script[0],
                    "n_lines": n_lines,
                    "n_lines_to_format": n_lines_to_format,
                }
            )
        return results

    def _get_py_files_from_dss_library(self) -> List[DSSLibraryFile]:

        def _get_dss_library_files_from_folder(
            files_flattened: List[DSSLibraryFile], folder: DSSLibraryFolder
        ) -> None:

            for item in folder.list():
                if isinstance(item, dataikuapi.dss.projectlibrary.DSSLibraryFolder):
                    _get_dss_library_files_from_folder(files_flattened, item)
                else:
                    files_flattened.append(item)

        files_flattened = []
        for item in self.project.get_library().list():
            if isinstance(item, dataikuapi.dss.projectlibrary.DSSLibraryFolder):
                _get_dss_library_files_from_folder(files_flattened, item)
            else:
                files_flattened.append(item)

        return [file for file in files_flattened if ".py" in file.name]

    def _get_python_recipe_formatting_status(self) -> List[Dict[str, int]]:
        all_recipes = self.project.list_recipes()
        python_recipe_names = [d["name"] for d in all_recipes if d["type"] == "python"]

        py_scripts = [
            (name, self.project.get_recipe(name).get_settings().get_code())
            for name in python_recipe_names
        ]
        return self._get_formatting_status(py_scripts)

    def _get_project_library_formatting_status(self) -> List[Dict[str, int]]:

        py_files = self._get_py_files_from_dss_library()
        py_scripts = [(file.name, file.read()) for file in py_files]
        return self._get_formatting_status(py_scripts)

    def run(self):

        self.format_style = self.config.get("formatter")

        lowest_threshold = self.config.get("lowest")
        low_threshold = self.config.get("low")
        medium_threshold = self.config.get("medium")
        high_threshold = self.config.get("high")
        critical_threshold = self.config.get("critical")
        
        details = {}

        global_results = []
        global_results.extend(self._get_python_recipe_formatting_status())
        global_results.extend(self._get_project_library_formatting_status())

        total_lines_of_code = sum([d.get("n_lines") for d in global_results])
        lines_needing_formatting = sum(
            [d.get("n_lines_to_format") for d in global_results]
        )
        if total_lines_of_code > 0:
            perc_lines_needing_formatting = (
                lines_needing_formatting / total_lines_of_code
            ) * 100
            perc_lines_needing_formatting = round(perc_lines_needing_formatting, 2)
        else:
            perc_lines_needing_formatting = 0
            
        details.update({d.get("name"): f"{d.get('n_lines_to_format')} lines" for d in global_results})

        error_message = f"{perc_lines_needing_formatting}% of project Python Recipe and Python Library modules require reformatting."

        if perc_lines_needing_formatting > critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=5, message=error_message, details=details
            )
        elif perc_lines_needing_formatting > high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=4, message=error_message, details=details
            )
        elif perc_lines_needing_formatting > medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=3, message=error_message, details=details
            )
        elif perc_lines_needing_formatting > low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=2, message=error_message, details=details
            )
        elif perc_lines_needing_formatting > lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity=1, message=error_message, details=details
            )
        else:
            return ProjectStandardsCheckRunResult.success(
                message=f"Minimal lines of code in project Python Recipe and Python Library modules require reformatting.",
                details=details,
            )
