# Project Assessment Tool - PAT Plugin

![GitHub release (latest by date)](https://img.shields.io/github/v/release/dataiku/dss-plugin-project-advisor) ![Build status](https://img.shields.io/badge/build-passing-brightgreen) ![Support level](https://img.shields.io/badge/support-Unsupported-orange)

This plugin helps automate the review of a DSS project all the way up to the whole Instance based on instance wide defined best practices.\
The tool will generate and save a set of **assessments** (**metrics** and **checks**) as part of the review. 

# How To Use
Following are all the steps to use the plugin.
## Installing the tool in DSS.
1. Add the plugin onto your DSS instance.
2. Configure ALL the **plugin presets** (to set the instance default best practice configurations & filters) and **plugin settings** for plugin/admin level configurations.

## Using the tool
There are 3 way to use the tool
1. Over a single project -> Runs all the assessments for a given project (scenario step)
2. Over a set of projects -> Runs all the the project assessments (macro)
3. Over the whole instance -> Runs all the project assessments & instance assessments (macro)

## Viewing the reports
The results are appended in two report datasets:
1. A metrics dataset
2. A checks dataset

At the project level, a Dashboard is generated or updated un the PAT run. (TODO)\
At the instance level, a webapp component is generated or updated on the IAT run. (TODO)\


# How to Contribute

## Add an assessment to the backlog.
New checks can be requested through [this form](https://form.asana.com/?k=jfs7vGXHZzx90v7ce8PDMg&d=8646845799314).\
Please find the existing backlog and implemented checks [here](https://app.asana.com/0/1207314309440131/1207314459344785).\
Once validated they will be assigned to be implemented.\
An assessment can be a project/instance metric or check.\
Project Checks are divided into 8 categories & Instance Checks are divided into 4 distinct categories.\
Metrics do not have a category & will all be computed at each run.

# How to Implement an Assessment

To implement an assessment:
1. Pull the plugin onto your local DSS instance.
2. Create a feature branch for the assessment from the current release branch following the format : **feat-name-of-assessment**
3. Build a the assessment class extending the correct class *(use existing metrics/ checks implementations as examples)*\
    *Note:*
    - **Project Checks** have access to computed project metrics.
    - **Instance Metrics** have access to the metrics and check results of ALL projects on the instance.
    - **Instance Checks** have access to the instance metrics & the metrics and checks results of all projects on the instance.
4. Add the new class in the corresponding folder and file `python-lib/project_advisor/assessments/..` folder.
    - Follow the existing folder structure.
    - Docstrings should follow the [reST](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html) format.
    - Each assessment should have their own file.   
5. Submit a pull request for review.

*Tip : To build and test the class outside of the plugin (Ex: In a DSS notebook), you can import the **python-lib** part of the plugin in the project code libraries to have access to the base classes*

# Extra Assessment Configuration
To allow users to configure and filter assessments, the plugin components' UI and the assessment filtering logic can be modified.

## Set the assessment's compatible upper and lowerbound DSS version.
In the assessment class constuctor, optionally pass a **dss_version_min** & **dss_version_min** with values:
- Version("x.y.z") imported *from packaging.version import Version*
- None (if there are no version limit)

## Add a Best Practice Parameter or an Assessent Filter in the UI
1. Add the parameter in the relvant presets json.
    - **instance-check-config** : For instance best practice settings.
    - **instance-check-filter** : For instance assessments filters.
    - **project-check-config** : For project best practice settings.
    - **project-check-config** : For project assessments filters.
2. Load the added parameters from the presets and add them to the DSSConfiguration.
    - Do this in all the relevant component (Project Advisor, Batch Project Advisor & Instance Advisor)
3. All assessment implementations can then load the param from the config if needed.

## Apply an Assessment Filter
Use **has_llm** as an example.
1. Add a class attribute to the **DSSAssessment** base class and initilize it with a default value.
2. Set the attribute in the constructor of all assessment classes that need a different value than the default. Ex: **python_recipe_to_visual_check**.
3. Add the filter input in the UI (see instructions above)
4. Add the filter logic in the **filter** function in the **DSSAssessment** base class.
    - Note : If the filter is specific to a type of assessment, add the filter logic to that child class.
    
## Building checks using the deployer and automation nodes.
Use checks in the project check category **DEPLOYMENT** as examples.
- To get a handle on the deployer leverage the `self.config.deployer_client` variable (always check if not None!)
- To get a handel on an infra client use the `self.config.infra_to_client` variable (at contains mappings from infra IDs to their DSSClient)
Example workflow: "I want to check that my project is deployed on all it's deployments"
1. Get a handle on the deployer client from the `deployer_client` in the config.
2. List the deployments for that client
3. Extract the infra ID for all the deployments and retrieve the client from the `infra_to_client` mapping.
4. Query each retrieved automation node clients to check if the project exists.


## License
This plugin is distributed under the [Apache License version 2.0](LICENSE).
