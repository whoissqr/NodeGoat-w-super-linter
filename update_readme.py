from python_graphql_client import GraphqlClient
from blackduck.HubRestApi import HubInstance
import pathlib
import pprint
import os
import polarisAPI

root = pathlib.Path(__file__).parent.resolve()


if __name__ == "__main__":

    readme = root / "README.md"
    pp = pprint.PrettyPrinter(indent=4)

    rewritten = "## === scan result for last PR/commit status === \n"
    rewritten += "<br/><br/>\n"

    urlbase = "https://poc94.blackduck.synopsys.com/"
    BD_TOKEN = os.environ.get("HUB_94_TOKEN", "")
    print("BD_TOKEN = " + BD_TOKEN)
    hub = HubInstance(urlbase, api_token=BD_TOKEN, insecure=True)

    # get the get_bom_component_policy_violations
    p = os.environ.get("PROJECT_NAME", "")
    v = os.environ.get("PROJECT_VERSION", "")

    print("p = " + p)
    print("v = " + v)

    project = hub.get_project_by_name(p)
    version = hub.get_version_by_name(project, v)

    if project and version:
        bom_components = hub.get_version_components(version)
    else:
        sys.exit()

    # SCA table header
    rewritten += "###### SCA scan by Synopsys Black Duck\n"
    rewritten += "|OSS component | Version | Status | Link|\n"
    rewritten += "| --- | --- | --- | --- |\n"
    for bom_component in bom_components.get('items'):
        if bom_component.get('policyStatus') == "IN_VIOLATION":
            try:
                component_name = bom_component['componentName']
                component_version_name = bom_component['componentVersionName']
                link = hub.get_link(bom_component, "policy-rules")
                rewritten += "|" + component_name
                rewritten += "|" + component_version_name
                rewritten += "| in VIOLATION"
                rewritten += "|[link](" + link + ")" + "|\n"
                print(component_name + " is IN_VIOLATION")
            except Exception:
                logging.error(
                    "Unable to retrieve policies for BOM component {}".
                    format(bom_component), exc_info=True)

    # get the polaris scanning issues
    rewritten += "###### SAST scan by Synopsys Coverity\n"
    rewritten += polarisAPI.getIssues("NodeGoat-w-super-linter", "master")
    rewritten += "<br/>"

    rewritten += "::: warning\n"
    rewritten += "*This is a personal hobbby project only.*\n"
    rewritten += "*Not associated or supported by Synopsys SIG.*\n"
    rewritten += ":::\n"
    # flush to readme.md
    readme.open("w").write(rewritten)