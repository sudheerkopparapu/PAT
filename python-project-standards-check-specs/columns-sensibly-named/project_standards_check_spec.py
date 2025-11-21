from dataiku.project_standards import (
    ProjectStandardsCheckRunResult,
    ProjectStandardsCheckSpec,
)
from collections import defaultdict
from project_advisor.pat_tools import md_print_list
import re
from typing import List, Optional, Set


def _parse_allowed_from_charclass_pattern(pattern: str) -> Optional[Set[str]]:
    """
    Parse simple charclass forms like: ^[a-z0-9_]+$ and build an allowed ASCII set.
    Returns None if the pattern is more complex (fallback will handle).
    """
    m = re.match(r'^\^\[([^\]]+)\][+*]\$$', pattern or "")
    if not m:
        return None
    body = m.group(1)
    allowed: Set[str] = set()
    i = 0
    while i < len(body):
        ch = body[i]
        # escaped char
        if ch == '\\' and i + 1 < len(body):
            allowed.add(body[i + 1])
            i += 2
            continue
        # range a-z / 0-9
        if i + 2 < len(body) and body[i + 1] == '-' and body[i + 2] not in (']',):
            start, end = ord(body[i]), ord(body[i + 2])
            if start <= end:
                for c in range(start, end + 1):
                    allowed.add(chr(c))
            i += 3
            continue
        # literal
        allowed.add(ch)
        i += 1
    return allowed


def diagnose_nonmatch(name: str, pattern: str) -> List[str]:
    """
    Return human-readable reasons why 'name' failed 'pattern'.
    If the only issue is the presence of spaces, return just ["contains spaces"].
    """
    reasons: List[str] = []
    if name == "":
        return ["empty/blank name"]

    # Detect spaces (not generic whitespace)
    has_spaces = (' ' in name)
    if has_spaces:
        reasons.append("contains spaces")
        # Note: we'll compress to only ["contains spaces"] at the end if that's the sole issue
        if name != name.strip(' '):
            reasons.append("leading/trailing whitespace")

    # Non-ASCII
    if any(not c.isascii() for c in name):
        reasons.append("contains non-ASCII characters")

    # Starts-with rules
    if pattern.startswith('^[A-Za-z]') or pattern.startswith('^[a-zA-Z]'):
        if not re.match(r'^[A-Za-z]', name or ""):
            reasons.append("must start with a letter")

    # Lowercase-only heads (e.g., ^[a-z][a-z0-9_]*$)
    if pattern.startswith('^[a-z]') and re.search(r'[A-Z]', name):
        reasons.append("uppercase letters not allowed")

    # Character-class analysis (ignore spaces when categorizing special chars)
    allowed = _parse_allowed_from_charclass_pattern(pattern or "")
    if allowed is not None:
        offenders = {c for c in name if c not in allowed}
        offenders_no_space = offenders - {' '}  # <-- key change: ignore spaces here

        if offenders_no_space:
            if any(c in "-–—" for c in offenders_no_space):
                reasons.append("contains hyphen/dash")
            if "." in offenders_no_space:
                reasons.append("contains dot")
            if any(c in "/\\" for c in offenders_no_space):
                reasons.append("contains slash or backslash")
            if any(c in "'\"" for c in offenders_no_space):
                reasons.append("contains quotes")
            if any(c in "()[]{}" for c in offenders_no_space):
                reasons.append("contains brackets/parentheses")

            remaining = [c for c in offenders_no_space if c not in set("-–—./\\'\"()[]{}")]
            if remaining:
                reasons.append(f"contains special characters: {''.join(sorted(set(remaining)))}")
    else:
        if not reasons:
            reasons.append("does not satisfy the selected naming rule")

    seen = set()
    reasons = [r for r in reasons if not (r in seen or seen.add(r))]

    # If spaces are the only problem, return only that reason
    only_spaces_issue = all(r in {"contains spaces", "leading/trailing whitespace"} for r in reasons) and has_spaces
    if only_spaces_issue:
        return ["contains spaces"]

    return reasons


    # dedupe, preserve order
    seen = set()
    out = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


class MyProjectStandardsCheckSpec(ProjectStandardsCheckSpec):
    """
    Write your own logic by modifying the body of the run() method.

    .. important::
        This class will be automatically instantiated by DSS, do not add a custom constructor on it.

    The superclass is setting those fields for you:
    self.config: the dict of the configuration of the object
    self.plugin_config: the dict of the plugin settings
    self.project: the current `DSSProject` to use in your check spec
    self.original_project_key: the project key of the original project

    .. note::
        self.project.project_key and self.original_project_key are different because Project Standards is never run on the original project.
        A temporary project will be created just to run checks on it and will be deleted afterward.
        If you are running Project Standards on a project, the temporary project is a copy of the original one.
        If you are running Project Standards on a bundle, the temporary project is a copy of the content of the bundle.
    """

    def _add(self, usage, dataset, where):
        if dataset:
            dataset = str(dataset).strip()
            if dataset:
                usage[dataset].add(where)
    
    def run(self):
        """
        Run the check

        :returns: the run result.
            Use `ProjectStandardsCheckRunResult.success(message)` or `ProjectStandardsCheckRunResult.failure(severity, message)` depending on the result.
            Use `ProjectStandardsCheckRunResult.not_applicable(message)` if the check is not applicable to the project.
            Use `ProjectStandardsCheckRunResult.error(message)` if you want to mark the check as an error. You can also raise an Exception.
        """
        lowest_threshold = self.config.get('lowest')
        low_threshold = self.config.get('low')
        medium_threshold = self.config.get('medium')
        high_threshold = self.config.get('high')
        critical_threshold = self.config.get('critical')
        
        pattern = self.config.get('pattern')
        connections_in_scope = self.config.get('connection_types')
        
        details = {}
        datasets_with_non_conforming_columns = []
        non_conforming_column_names = defaultdict(set)

        # NEW: collect unique reasons across entire scan
        rejection_reasons = set()

        datasets = [dataset for dataset in self.project.list_datasets() if dataset['type'] in connections_in_scope]

        # Check each dataset name
        for dataset in datasets:
            column_names = [item['name'] for item in dataset['schema']['columns']]
            for column_name in column_names:
                if re.fullmatch(pattern, column_name):
                    continue
                else:
                    datasets_with_non_conforming_columns.append(dataset['name'])
                    self._add(non_conforming_column_names, dataset['name'], column_name)

                    # NEW: aggregate reasons globally
                    for r in diagnose_nonmatch(column_name, pattern):
                        rejection_reasons.add(r)

        non_conforming_column_names = dict(non_conforming_column_names)
        total_non_conforming_columns = sum(len(v) for v in non_conforming_column_names.values())
        datasets_with_non_conforming_columns = list(set(datasets_with_non_conforming_columns))
        
        # add col names and datasets to details to display
        for dataset, cols in non_conforming_column_names.items():
            column_list = list(set(cols))
            md_formatted_dataset =  md_print_list([dataset], "dataset", self.original_project_key)
            details['dataset: ' + dataset] = f"Link: {md_formatted_dataset}, Columns: {column_list}"

        # NEW: simple list of all unique reasons across the scan
        details['rejection_reasons'] = sorted(rejection_reasons)
        

        message = f"There is/are {total_non_conforming_columns} columns using a non conforming naming convention. Consider renaming them by removing spaces and special characters."

        if not non_conforming_column_names:
            return ProjectStandardsCheckRunResult.success(
                message = "All columns use the appropriate naming convention specified.",
                details = details
            )
        
        if total_non_conforming_columns >= critical_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 5,
                message = message,
                details = details
            )
        elif total_non_conforming_columns >= high_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 4,
                message = message,
                details = details
            )
        elif total_non_conforming_columns >= medium_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 3,
                message = message,
                details = details
            )
        elif total_non_conforming_columns >= low_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 2,
                message = message,
                details = details
            )
        elif total_non_conforming_columns >= lowest_threshold:
            return ProjectStandardsCheckRunResult.failure(
                severity = 1,
                message = message,
                details = details
            )
