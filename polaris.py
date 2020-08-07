#!/usr/bin/python
'''
Copyright (c) 2020 Synopsys, Inc. All rights reserved worldwide. The information
contained in this file is the proprietary and confidential information of
Synopsys, Inc. and its licensors, and is supplied subject to, and may be used
only by Synopsys customers in accordance with the terms and conditions of a
previously executed license agreement between Synopsys and that customer.
Purpose: library of common Polaris functions
Coding conventions:
4 space indentation, not tabs
getFoo & setFoo function names
lowerUpperCase function and variable names
hide debug output behind if debug: print(foo)
Debug levels:
1 = normal one liners like projectid = projectid
3 = printcurl
5 = various json / dict structs
7 = entire jsonapi response
Variables assumed set in main:
polaris.debug
polaris.api
polaris.token
Requires the following Python modules:
pip install jsonapi_requests
'''

import re
import sys
import requests
import json
import jsonapi_requests
from datetime import datetime
from datetime import timedelta
from urllib.parse import urlparse
import pandas as pd
from _datetime import date

# -----------------------------------------------------------------------------

'''
Function:       printCurl
Description:    output curl command
Input:          endpoint, method, params and/or data
Output:         curl command to act on endpoint
'''
def printCurl(ep, method, limit=500, params=None, data=None):
    # prints out curl representation
    command = "curl -v -g -X {method} {uri} -H {headers}"
    headers = {'Authorization': 'Bearer ' + token}
    header_list = ['"{0}: {1}"'.format(k, v) for k, v in headers.items()]
    header = " -H ".join(header_list)
    path = ep.path
    url = ep.requests.config.API_ROOT + path
    if params:
        if 'page[limit]' not in params:
            params['page[limit]'] = str(limit)
        param_list = ['"{0}={1}"'.format(k, v) for k, v in params.items()]
        param_str = "&".join(param_list).replace('"','')
        # Remove spaces from 'include[issue][]': ['severity', 'related-indicators', 'related-taxa']
        param_str = param_str.replace(' ', '')
        url = url + '?' + param_str
    url = '"' + url + '"'
    if data:
        command = "curl -v -g -X {method} {uri} -H {headers} -D \"{data}\""
        print(command.format(method=method, headers=header, uri=url, data=data))
    else:
        print(command.format(method=method, headers=header, uri=url))

# -----------------------------------------------------------------------------

'''
Function:       printError
Description:    print error and exit
Input:          ApiClientError
Output:         error code and detail
'''
def printError(e):
    content = e.content.decode("utf-8")
    content = json.loads(content)
    print("Error Code " + str(e.status_code) + ": " + content['errors'][0]['detail'])
    sys.exit(2)

# -----------------------------------------------------------------------------
# --- Polaris AUTH functions
# -----------------------------------------------------------------------------

'''
Function:       getJwt
Description:    convert users access token to JSON Web Token. For service accounts,
                pass None for token and supply the email and password.
Input:          url and token or email and password
Output:         jwt
'''
def getJwt(url, token, email=None, password=None):
    apiRoot = url + '/api/auth'
    api = jsonapi_requests.Api.config({
        'API_ROOT': apiRoot,
        'TIMEOUT': 100
    })
    endpoint = api.endpoint('authenticate')
    auth_headers = { 'Content-Type' : 'application/x-www-form-urlencoded' }
    if token != None:
        auth_params = { 'accesstoken' : token }
    else:
        auth_params = { 'email' : email, 'password' : password }

    try:
        response = endpoint.post(headers=auth_headers, params=auth_params)
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    return response.payload['jwt']

# -----------------------------------------------------------------------------

'''
Function:       configApi
Description:    configures jsonapi_requests with JWT auth
                https://github.com/socialwifi/jsonapi-requests/wiki/Configuration
Input:          url
Output:
'''
def configApi(url):
    return jsonapi_requests.Api.config({
        'API_ROOT': url + '/api',
        'AUTH': jwtAuth(),
        'TIMEOUT': 100
    })

# -----------------------------------------------------------------------------

'''
Function:       jwtAuth
Description:
Input:
Output:
'''
class jwtAuth(requests.auth.AuthBase):
    def __call__(self, r):
        r.headers['Authorization'] = 'Bearer ' + token
        return r

# -----------------------------------------------------------------------------
# ---- Polaris GET functions
# -----------------------------------------------------------------------------

'''
Function:       getPaginatedData
Description:    gets paginated data and returns a single concatenated data dictionary
Input:          endpoint
                params
                limit
Output:         data
                included
'''
def getPaginatedData(endpoint, params, limit):
    offset = 0
    total = limit + 1
    data = []
    included = []

    params['page[limit]'] = str(limit)
    params['page[offset]'] = str(offset)

    while (offset < total):
        try:
            response = endpoint.get(params=params)
        except jsonapi_requests.request_factory.ApiClientError as e:
            printError(e)
        if (debug >= 7): print(response)

        if (response.payload['data'] == []):
            # Return empty list (or 2 empty lists for issues endpoint)
            p = re.compile(r'query\/v\d+\/issues')
            if p.match(endpoint.path):
                return [], []
            else:
                return []

        # we actually only need to fetch total once
        total = response.payload['meta']['total']

        data.extend(response.payload['data'])
        if response.payload['included']: included.extend(response.payload['included'])

        # update the offset to the next page
        offset += limit
        params['page[offset]'] = str(offset)

    if (included == []): return data
    else: return data, included

# -----------------------------------------------------------------------------

'''
Function:       getBranchId
Description:
Input:          project id
                branch name
Output:         branch id
'''
def getBranchId(projectId, branch):
    endpoint = api.endpoint('common/v0/branches')
    params = dict([('page[limit]', '500'),
        ('filter[branch][project][id][eq]', str(projectId)),
        ('filter[branch][name][eq]', str(branch))])
    response = endpoint.get(params=params)
    if (response.payload['data'] == []):
        print('branch ' + str(branch) + ' not found')
        sys.exit(2)
    if (debug >= 7): print(response)
    return response.payload['data'][0]['id']

# -----------------------------------------------------------------------------

'''
Function:       getProjectAndBranchId
Description:    Returns both project and branch IDs for a project+branch pair
Input:          project name
                branch name
Output:         project id
                branch id
'''
def getProjectAndBranchId(projectName, branchName, limit):
    endpoint = api.endpoint('common/v0/branches')
    params = dict([('filter[branch][project][name][eq]', str(projectName))])
    pid = None
    bid = None

    branches = getPaginatedData(endpoint, params, limit)
    if (branches == []):
        print('project ' + str(projectName) + ' not found')
        sys.exit(2)

    for branch in branches:
        if branch['attributes']['name'] == branchName:
            bid = branch['id']
            pid = branch['relationships']['project']['data']['id']

    if (bid == None):
        print('branch ' + str(branchName) + ' not found')
        sys.exit(2)

    return pid, bid

# -----------------------------------------------------------------------------

'''
Function:       getGroupId
Description:
Input:          group name
Output:         group id
'''
def getGroupId(groupname):
    endpoint = api.endpoint('auth/groups')
    response = endpoint.get()
    for group in response.payload['data']:
        if (group['attributes']['groupname'] == groupname):
            return group['id']
    print('No group found with name ' + str(groupname) + '.')
    sys.exit(2)

# -----------------------------------------------------------------------------

'''
Function:       getBranches
Description:    create a dictionary of useful branch values for a given project id
Input:          projectId
Output:         dictionary of useful branch values
'''
def getBranches(projectId, project, limit=500):
    endpoint = api.endpoint('common/v0/branches')
    if projectId:
        params = dict([
            ('filter[branch][project][id][eq]', projectId ),
            ])
    else:
        params = dict([
            ('filter[branch][project][name][eq]', project ),
            ])
    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
    branches = getPaginatedData(endpoint, params, limit)
    if branches == []:
        return []

    # loop over the list of runs and grab the fields we want to include in the dictionary
    dictionary = []
    for branch in branches:
        branchId = branch['id']
        name = branch['attributes']['name']
        main = branch['attributes']['main-for-project']
        projectId = branch['relationships']['project']['data']['id']
        trash = branch['meta']['in-trash']

        entry = {
            'branchId': branchId,
            'name': name,
            'projectId': projectId,
            'main': main,
            'trash': trash,
            }

        if (debug >= 5): print(entry)
        dictionary.append(entry)

    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getJobs
Description:    create a dictionary of useful job values for a given branch id
Input:          branchId
                state
                limit
                getRollUpCounts - enables addition API calls for issue count and density
Output:         dictionary of useful job values
'''
def getJobs(branchId, state, limit, getRollUpCounts):
    endpoint = api.endpoint('jobs/jobs')
    params = dict([
        ('filter[jobs][branch][id][eq]', str(branchId)),
        ('filter[jobs][status][state][eq]', str(state))
        ])
    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
    jobs = getPaginatedData(endpoint, params, limit)
    if jobs == []:
        return []

    # loop over the list of jobs and grab the fields we want to include in the dictionary
    dictionary = []
    timeFormat = '%Y-%m-%dT%H:%M:%S.%f+0000'
    for job in jobs:
        jobId = job['id']
        projectId = job['relationships']['project']['data']['id'].split(':')[3]
        branchId = job['relationships']['branch']['data']['id'].split(':')[3]
        state = job['attributes']['status']['state']
        if (state == 'COMPLETED'):
            runId = job['relationships']['runs']['data']['id'].split(':')[3]
            toolVersion = job['attributes']['swip_spi_metadata']['toolversion']
            linesOfCode = job['attributes']['details']['intermediateDirectoryDetails']['linesOfCode']
            try: captureSize = job['attributes']['swip_spi_metadata']['toolMeta']['captureSize']
            except: captureSize = None
            try: artifactSize = job['attributes']['swip_spi_metadata']['artifactSize']
            except: artifactSize = None
            dateQueued = job['attributes']['dateQueued']
            dateStarted = job['attributes']['dateStarted']
            queueTime = datetime.strptime(dateStarted, timeFormat) - datetime.strptime(dateQueued, timeFormat)
            dateCompleted = job['attributes']['dateCompleted']
            totalTime = datetime.strptime(dateCompleted, timeFormat) - datetime.strptime(dateQueued, timeFormat)
            for phase in job['attributes']['lifecyclePhases']:
                if phase['phase'] == "idirUploadDuration": idirUploadDuration = timedelta(milliseconds=phase['durationMillis'])
                if phase['phase'] == "covAnalyzeDuration": covAnalyzeDuration = timedelta(milliseconds=phase['durationMillis'])

            if getRollUpCounts:
                endpoint = api.endpoint('issues/v0/roll-up-counts')
                params = dict([
                    ('project-id', str(projectId)),
                    ('run-id[]', str(runId))
                    ])
                if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
                rollUpCount = getPaginatedData(endpoint, params, limit)
                issueCountTotal = rollUpCount[0][0]['attributes']['value']
                defectDensity = issueCountTotal / linesOfCode * 1000
                issues = {
                    'issues': issueCountTotal,
                    'density': defectDensity,
                }

            entry = {
                'jobId': jobId,
                'projectId': projectId,
                'branchId': branchId,
                'state': state,
                'runId': runId,
                'toolVersion': toolVersion,
                'loc': linesOfCode,
                'idirSize': captureSize,
                'zipSize': artifactSize,
                'dateQueued': dateQueued.split('.')[0],
                'dateStarted': dateStarted.split('.')[0],
                'dateCompleted': dateCompleted.split('.')[0],
                'uploadTime': str(idirUploadDuration).split('.')[0],
                'queueTime': str(queueTime).split('.')[0],
                'scanTime': str(covAnalyzeDuration).split('.')[0],
                'totalTime': str(totalTime).split('.')[0],
                }
            if getRollUpCounts: entry.update(issues)

        if (state == 'FAILED'):
            try: dateFailed = job['attributes']['dateFailed'].split('+')[0]
            except: dateFailed = None
            failureReason = job['attributes']['failureInfo']['userFriendlyFailureReason']
            entry = {
                'jobId': jobId,
                'projectId': projectId,
                'branchId': branchId,
                'state': state,
                'dateFailed' : dateFailed,
                'failureReason' : failureReason,
                }

        if (debug >= 5): print(entry)
        dictionary.append(entry)

    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getRuns
Description:    create a dictionary of useful run values for a given branch id
Input:          project id and branch id
Output:         runs
'''
def getRuns(projectId, branchId, limit=500):
    endpoint = api.endpoint('common/v0/runs')
    params = dict([
        ('filter[run][project][id][eq]', projectId ),
        ('filter[run][revision][branch][id][eq]', branchId),
        ])
    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
    runs = getPaginatedData(endpoint, params, limit)
    if runs == []:
        return []

    # loop over the list of runs and grab the fields we want to include in the dictionary
    dictionary = []
    timeFormat = '%Y-%m-%dT%H:%M:%S.%fZ'
    for run in runs:
        runId = run['id']
        status = run['attributes']['status']
        dateCreated = run['attributes']['creation-date']
        dateCompleted = run['attributes']['completed-date']
        uploadId = run['attributes']['upload-id']
        projectId = run['relationships']['project']['data']['id']
        revisionId = run['relationships']['revision']['data']['id']
        toolId = run['relationships']['tool']['data']['id']
        submitting_userId = run['relationships']['submitting-user']['data']['id']
        submitting_orgId = run['relationships']['submitting-organization']['data']['id']
        try: previous_runId = run['relationships']['previous-run']['data']['id']
        except: previous_runId = None

        entry = {
            'runId': runId,
            'status': status,
            'dateCreated': dateCreated,
            'dateCompleted': dateCompleted,
            'uploadId': uploadId,
            'projectId': projectId,
            'revisionId': revisionId,
            'toolId': toolId,
            'submitting_userId': submitting_userId,
            'submitting_orgId': submitting_orgId,
            'previous_runId': previous_runId,
        }

        if (debug >= 5): print(entry)
        dictionary.append(entry)

    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getIssues
Description:    get issues for a given project+branch
Input:          project id, branch id, optional filter dictionary
                Example filter:
                    dict([('filter[issue][issue-key][$eq]', 'xyz')])
Output:         issues
'''
def getIssues(projectId, branchId, runId, limit, filterlist=None, triage=False, events=False):
    dictionary = []
    issues_data = []
    issues_included = []
    issues_start = datetime.now()
    triage_total_es = 0.0
    events_total_es = 0.0

    endpoint = api.endpoint('query/v1/issues')
    params = dict([
        ('project-id', str(projectId)),
        ('filter[issue][status][$eq]', 'opened'),
        ('include[issue][]', ['severity', 'related-indicators', 'related-taxa'])
        ])

    # filter by runId or branchId but not both
    if runId is not None: params['run-id[]'] = str(runId)
    else: params['branch-id'] = str(branchId)

    # update params with optional user-specified filter
    if filterlist:
        params.update(filterlist)

    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
    issues_data, issues_included = getPaginatedData(endpoint, params, limit)
    if issues_data == []:
        return []

    # create the base url so we can build an issue url later
    baseUrl = issues_data[0]['links']['self']['href']
    data = urlparse(baseUrl)
    baseUrl = data.scheme + '://' + data.netloc
    baseUrl += '/projects/' + projectId
    baseUrl += '/branches/' + branchId

    # loop over the list of issues
    for issue in issues_data:
        key = issue['attributes']['issue-key']
        finding_key = issue['attributes']['finding-key']
        checker = issue['attributes']['sub-tool']
        issue_type_id = issue['relationships']['issue-type']['data']['id']
        issue_path_id = issue['relationships']['path']['data']['id']
        try: severity = issue['relationships']['severity']['data']['id']
        except: severity = None

        # assume single element array
        # TODO Under what conditions is this more than a single element?
        issue_transitions_id = issue['relationships']['transitions']['data'][0]['id']

        # TODO Can we count on this always being a CWE number or can it be something else?
        cwe = None
        try:
            # There can be several CWEs, so merge them all in to a single string
            for taxa_data in issue['relationships']['related-taxa']['data']:
                if cwe is None:
                    cwe = taxa_data['id']
                else:
                    cwe += "," + taxa_data['id']
        except: cwe = None

        indicators = None
        if issue['relationships']['related-indicators']['data']:
            # TODO just pull the id values as a straight list
            indicator_list = []
            for ind_dct in issue['relationships']['related-indicators']['data']:
                for ind_key, val in ind_dct.items():
                    if ind_key == 'id':
                        indicator_list.append(val)
            indicators = ','.join(indicator_list)

        # iterate through included to get name, description, local-effect,
        # issue-type
        # TODO think about performance of this nested loop....
        for issue_included in issues_included:
            if issue_included['id'] == issue_type_id:
                # check for type "issue-type"? Is id unique?
                try: name = issue_included['attributes']['name']
                except: name = None
                try: description = issue_included['attributes']['description']
                except: description = None
                try: local_effect = issue_included['attributes']['local-effect']
                except: local_effect = None
                try: type = issue_included['attributes']['issue-type']
                except: type = None

            if issue_included['id'] == issue_path_id:
                dirsep = '/'
                try: path = dirsep.join(issue_included['attributes']['path'])
                except: path = None

            if issue_included['id'] == issue_transitions_id:
                # TODO should we check for issue_included['type'] == 'transition'??
                first_detected = "unknown"
                first_detected = issue_included['attributes']['transition-date'].split('.')[0]
                # TODO The filter for getIssues filters out issues that are not opened
                # if the filter removes "opened" then the transition-date value
                # would have a different meaning.  For now, this will not be returned.
                # transition_date = issue_included['attributes']['transition-date']

                # TODO Create default values
                # TODO Should this be un-indented by 1 or is this REALLY only when transitions-id is set?
                state = issue_included['attributes']['transition-type']
                cause = issue_included['attributes']['human-readable-cause']
                branchId = issue_included['attributes']['branch-id']
                revisionId = issue_included['attributes']['revision-id']

                # Construct issue URL
                url = baseUrl + '/revisions/'
                url += revisionId
                url += '/issues/' + key

        if triage:
            triage_start = datetime.now()
            # function?
            #     get current triage values
            #        entire triage comment history with timestamps
            #        jira ticket url if found in comments

            triage_owner = 'None'
            triage_dismissed = 'None'
            triage_comment = ''
            triage_jira_ticket = ''
            triage_data = getTriage(key, projectId, limit )

            if triage_data:
                comments = []
                for triage in reversed(triage_data): # go through all history updates from oldest to latest
                    timestmp = triage['attributes']['timestamp']
                    for triage_hist_value in triage['attributes']['triage-history-values']:
                        if triage_hist_value['attribute-semantic-id'] == 'OWNER':
                            triage_owner = triage_hist_value['display-value'] # should always have a value like 'Unassigned'
                        elif triage_hist_value['attribute-semantic-id'] == 'COMMENTARY':
                            if  triage_hist_value['display-value'].startswith('JIRA ticket:'):
                                triage_jira_ticket = triage_hist_value['display-value'][len('JIRA ticket:')] # Jira ticket url should be first
                            if timestmp:
                                comments.append(timestmp + ' ' + triage_hist_value['display-value'] )
                            else:
                                comments.append(triage_hist_value['display-value'] )
                        elif triage_hist_value['attribute-name'] == 'Dismiss':
                            triage_dismissed = triage_hist_value['display-value']
                if comments:
                    triage_comment = ']\n['.join(comments)
                    triage_comment = '[' + triage_comment + ']'

            # create the dictionary entry
            triage_dct = {
                'owner': triage_owner, 'comment': triage_comment, \
                'dismissed': triage_dismissed, 'jira': triage_jira_ticket
                 }
            triage_end = datetime.now()
            triage_total = triage_end - triage_start
            triage_total_es += triage_total.total_seconds()

        if events:
            events_start = datetime.now()
            # Added to grab line numbers as well
            endpoint = api.endpoint('code-analysis/v0/events')
            params = dict([('finding-key', str(finding_key)),
                ('run-id', str(runId)),
                ('locator-path', str(path))
                ])
            headers = {'Authorization': 'Bearer ' + token,
                'Accept-Language': 'en'}

            if (debug >= 3): printCurl(endpoint, 'GET', limit, params)
            try:
                response = endpoint.get(params=params, headers=headers)
                line = response.payload['data'][0]['main-event-line-number']
            except jsonapi_requests.request_factory.ApiClientError as e:
                print(e)
                exit(1)
            line_dct = {'line': line}
            events_end = datetime.now()
            events_total = events_end - events_start
            events_total_es += events_total.total_seconds()

        # create the dictionary entry
        entry = {'projectId': projectId, 'branchId': branchId, \
             'key': key, 'finding-key': finding_key, \
             'checker': checker, 'severity': severity, \
             'type': type, 'local_effect': local_effect, 'name': name, \
             'description': description, 'path': path, \
             'first_detected': first_detected , 'url': url, \
             'state' : state, 'cause' : cause, 'cwe' : cwe, \
             'indicators' : indicators, \
             'branchId' : branchId, 'revisionId' : revisionId
             }
        if triage:
            entry.update(triage_dct)
        if events:
            entry.update(line_dct)

        if (debug >= 5): print(entry)
        dictionary.append(entry)

    if (debug >= 1):
        issues_total = datetime.now() - issues_start
        issues_total_secs = issues_total.total_seconds()
        print('total getIssues elapsed time: ' + str(issues_total_secs))
        if triage:
            print('total triage elapsed time:' + str(triage_total_es))
        if events:
            print('total events elapsed time:' + str(events_total_es))
    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       cmpIssuesForRun
Description:    new = present in current, but not previous scan
                fixed = present in previous, but not current scan
Input:          projectId, curr_runId, prev_runId
Output:         new_issues, fixed_issues, and common_issues dataframes
'''
def cmpIssuesForRuns(projectId, curr_runId, prev_runId, getTriage=False):
    limit=500
    curr_issues = getIssues(projectId, '', curr_runId, limit, None, getTriage)
    prev_issues = getIssues(projectId, '', prev_runId, limit, None, getTriage)
    curr_df = pd.DataFrame(curr_issues)
    prev_df = pd.DataFrame(prev_issues)

    merged_df = pd.merge(curr_df, prev_df, how='outer', on='key', suffixes=('','_y'), indicator=True)

    new_df = merged_df[merged_df['_merge']=='left_only'][curr_df.columns]
    common_df = merged_df[merged_df['_merge']=='both'][curr_df.columns]
    # No suffix is used for current issue columns, but previous issue columns are suffixed with _y
    # only columns with _y are used for fixed
    fixed_df  = merged_df[merged_df['_merge']=='right_only']
    fixed_df  = fixed_df.filter(regex='key|_y$', axis=1).head() # get prev only columns
    fixed_df.columns = fixed_df.columns.str.replace(r'_y$', '') # strip suffix off column name

    return new_df, fixed_df, common_df, merged_df

# -----------------------------------------------------------------------------

'''
Function:       getOrgId
Description:
Input:          none
Output:         org id
'''
def getOrgId():
    endpoint = api.endpoint('auth/organizations')
    try:
        response = endpoint.get()
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)
    return response.payload['data'][0]['id']

# -----------------------------------------------------------------------------

'''
Function:       getOrgOwners
Description:
Input:          org id
Output:         array of org owners
'''
def getOrgOwners(orgid):
    endpoint = api.endpoint('auth/organizations/' + str(orgid))
    try:
        response = endpoint.get()
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)
    return response.payload['data']['relationships']['owners']['data']

# -----------------------------------------------------------------------------

'''
Function:       getProjectId
Description:
Input:          project name
Output:         project id
'''
def getProjectId(project):
    endpoint = api.endpoint('common/v0/projects')
    params = dict([('page[limit]', '500'),
        ('filter[project][name][eq]', str(project))])
    response = endpoint.get(params=params)
    if (response.payload['data'] == []):
        print('project ' + str(project) + ' not found')
        sys.exit(2)
    if (debug >= 7): print(response)
    return response.payload['data'][0]['id']

# -----------------------------------------------------------------------------

'''
Function:       createUserMap
Description:    create an mapping of user ids to username
Input:          limit
Output:         dictionary of usernames indexed by user id
'''
def createUserMap(limit):
    dictionary = {}
    endpoint = api.endpoint('auth/users')
    params = dict([('page[limit]', str(limit))])
    for user in getPaginatedData(endpoint, params, limit):
        dictionary[user['id']] = user['attributes']['username']
    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       createProjectOwnerMap
Description:    create a mapping of project ids to project owner
Input:          limit
Output:         dictionary of project owners indexed by project id
'''
def createProjectOwnerMap(limit):
    dictionary = {}
    userMap = createUserMap(limit)
    endpoint = api.endpoint('auth/role-assignments')
    params = dict([('page[limit]', str(limit))])
    for roleAssignment in getPaginatedData(endpoint, params, limit):
        if 'projects' not in roleAssignment['attributes']['object']: continue
        projectid=roleAssignment['attributes']['object'].split(":")[3]
        try:
            userid = roleAssignment['relationships']['user']['data']['id']
            dictionary[projectid] = userMap[userid]
        except:
            dictionary[projectid] = None
    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getProjects
Description:    create a dictionary of useful project values
Input:          limit
Output:         dictionary of useful project values
'''
def getProjects(limit):
    dictionary = []
    projectOwnerMap = createProjectOwnerMap(limit)

    endpoint = api.endpoint('common/v0/projects')
    params = dict([('page[limit]', str(limit))])
    for project in getPaginatedData(endpoint, params, limit):

        # grab the fields we want to include in the dictionary
        id = project['id']
        name = project['attributes']['name']
        try:
            userid = projectOwnerMap[id]
        except:
            userid = None

        # create the dictionary entry
        entry = {'id': id, 'name': name, 'owner': userid}
        if (debug >= 5): print(entry)

        # append it to the dictionary
        dictionary.append(entry)

    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getRoleId
Description:
Input:          role name
Output:         role id
'''
def getRoleId(rolename):
    endpoint = api.endpoint('auth/roles')
    try:
        response = endpoint.get()
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)

    for role in response.payload['data']:
        if (role['attributes']['rolename'] == rolename ):
            return role['id']

    print('No role found with name ' + str(rolename) + '.')
    sys.exit(2)

# -----------------------------------------------------------------------------

'''
Function:       getRoleMap
Description:
Input:          none
Output:         array of role names indexed by role id
'''
def getRoleMap():
    endpoint = api.endpoint('auth/roles')
    try:
        response = endpoint.get()
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)
    roleMap = {}
    for role in response.payload['data']:
        roleMap[role['id']] = role['attributes']['rolename']
    return roleMap

# -----------------------------------------------------------------------------

'''
Function:       getUserId
Description:
Input:          username or email address
Output:         user id
'''
def getUserId(user):
    endpoint = api.endpoint('auth/users')

    params = dict([('filter[users][username][?eq]', user)])
    try:
        response = endpoint.get(params=params)
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)
    if (response.payload['meta']['total'] != 0): return response.payload['data'][0]['id']

    params = dict([('filter[users][email][?eq]', user)])
    try:
        response = endpoint.get(params=params)
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)
    if (response.payload['meta']['total'] != 0): return response.payload['data'][0]['id']

    print("FATAL: username or email = " + user + " not found")
    sys.exit(2)

# -----------------------------------------------------------------------------

'''
Function:       createUserOrgRoleMap
Description:    create a mapping of user ids to user org role
Input:          limit
Output:         dictionary of user org roles indexed by user id
'''
def createUserOrgRoleMap(limit, service):
    dictionary = {}
    orgid = getOrgId()
    roleMap = getRoleMap()
    endpoint = api.endpoint('auth/role-assignments')
    params = dict([('page[limit]', str(limit))])
    if service: params.update([('filter[role-assignments][user][automated]', 'true')])
    for roleAssignment in getPaginatedData(endpoint, params, limit):
        if orgid not in roleAssignment['attributes']['object']: continue
        userid = roleAssignment['relationships']['user']['data']['id']
        roleid = roleAssignment['relationships']['role']['data']['id']
        dictionary[userid] = roleMap[roleid]
    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getUsers
Description:    create a dictionary of useful user values
Input:          none
Output:         dictionary of useful user values
'''
def getUsers(limit, filter, service):
    endpoint = api.endpoint('auth/users')
    params = dict([('page[limit]', str(limit))])
    if filter: params.update(filter)
    if service: params.update([('filter[users][automated]', 'true')])
    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)

    # improve performance by creating a user org role map
    userIdOrgRoleMap = createUserOrgRoleMap(limit, service)

    # loop over the list of users and grab the fields we want to include in the dictionary
    dictionary = []
    for user in getPaginatedData(endpoint, params, limit):
        id = user['id']
        enabled = user['attributes']['enabled']
        name = user['attributes']['name']
        email = user['attributes']['email']
        username = user['attributes']['username']
        firsttime = user['attributes']['first-time']
        role = userIdOrgRoleMap[id]

        entry = {'id': id, 'username': username, 'name': name, 'email': email, 'enabled': enabled, 'role': role, 'firsttime': firsttime}
        if (debug >= 5): print(entry)
        dictionary.append(entry)

    return dictionary
# -----------------------------------------------------------------------------

'''
Function:       getUsersByEmail
Description:    create a dictionary of useful user values (by email)
Input:          none
Output:         dictionary of useful user values
'''
def getUsersByEmail(limit, filter, service):
    endpoint = api.endpoint('auth/users')
    params = dict([('page[limit]', str(limit))])
    if filter: params.update(filter)
    if service: params.update([('filter[users][automated]', 'true')])
    if (debug >= 3): printCurl(endpoint, 'GET', limit, params)

    # improve performance by creating a user org role map
    userIdOrgRoleMap = createUserOrgRoleMap(limit, service)

    # loop over the list of users and grab the fields we want to include in the dictionary
    dictionary = dict()
    for user in getPaginatedData(endpoint, params, limit):
        id = user['id']
        enabled = user['attributes']['enabled']
        name = user['attributes']['name']
        email = user['attributes']['email']
        username = user['attributes']['username']
        firsttime = user['attributes']['first-time']
        role = userIdOrgRoleMap[id]

        entry = { email: {'id': id, 'username': username, 'name': name, 'enabled': enabled, 'role': role, 'firsttime': firsttime}}
        if (debug >= 5): print(entry)
        dictionary.update(entry)

    return dictionary

# -----------------------------------------------------------------------------

'''
Function:       getTriage
Description:    Returns complete triage history for an issue in a project
Input:          issue id
                project id
Output:         list of triage history items
'''
def getTriage(issueId, projectId, limit):
    endpoint = api.endpoint('triage-query/v0/triage-history-items')
    triageList = []

    params = dict([
        ('filter[triage-history-items][issue-key][$eq]', str(issueId)),
        ('filter[triage-history-items][project-id][$eq]', str(projectId))
    ])

    return getPaginatedData(endpoint, params, limit)

# -----------------------------------------------------------------------------

'''
Function:       getTaxonomyIds
Description:    Returns a dict of all available taxonomies
Input:          limit, url (e.g. "https://mypolaris.synopsys.com")
Output:         Dictionary of taxonomy IDs indexed by name (e.g. "issue-kind")
Notes:          For some reason, this API call does not play nicely with
                jsonapi_requests. A vague "unexpected error" is thrown.
                Here we use "vanilla" requests to work around it. Hence
                the requirement to provide a url argument.
                TODO: paginate... but currently there are only 8 taxons
'''
def getTaxonomyIds(limit, url):
    params = dict([('page[limit]', str(limit))])
    url = url + ('/api/taxonomy/v0/taxonomy-info')
    headers = {"Authorization": "Bearer " + token}
    taxons = {}

    try:
        r = requests.get(url, headers=headers, params=params)
    except requests.exceptions.RequestException as e:
        printError(e)

    for taxon in r.json()['data']:
        id = taxon['id']
        type = taxon['attributes']['type']
        taxons[type] = id

    return taxons

# -----------------------------------------------------------------------------
# ---- Polaris SET functions
# -----------------------------------------------------------------------------

'''
Function:       setOrgRole
Description:
Input:          org id
                user id
                role id
Output:         role assignment id
'''
def setOrgRole(orgid, userid, roleid):
    endpoint = api.endpoint('auth/role-assignments')
    params = dict([('page[limit]', '500'),
       ('filter[role-assignments][user][id][$eq]', str(userid)),
       ('filter[role-assignments][user][automated]', 'true')])
    try:
        response = endpoint.get(params=params)
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print(response)

    #assuming only 1 array element is returned
    roleassid = response.payload['data'][0]['id']

    endpoint = api.endpoint('auth/role-assignments/' + roleassid)
    json_data = {
        "data": {
            "type": "role-assignments",
            "attributes": {
                "object": "urn:x-swip:organizations:" + orgid
            },
            "relationships": {
                "role": {
                    "data": {
                        "type": "roles",
                        "id": roleid
                    }
                },
                "user": {
                    "data": {
                        "type": "users",
                        "id": userid
                    }
                },
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": orgid
                    }
                }
            }
        }
    }

    params = dict([('page[limit]', '500')])

    try:
        response = endpoint.patch(data=json.dumps(json_data))
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if (debug >= 7): print (response)

    return roleassid

# -----------------------------------------------------------------------------

'''
Function:       setProjectRole
Description:
Input:          project id
                user id
                role id
Output:         role assignment id
'''
def setProjectRole(orgid, projectid, groupid, userid, roleid):
    endpoint = api.endpoint('auth/role-assignments')
    json_data = {
           'data' : {
              'type' : 'role-assignments',
              'relationships' : {
                 'organization' : {
                    'data' : {
                       'id' : str(orgid),
                       'type' : 'organizations'
                    }
                 },
                 'role' : {
                    'data' : {
                       'id' : str(roleid),
                       'type' : 'roles',
                    }
                 }
              },
              'attributes' : {
                 'object' : 'urn:x-swip:projects:' + str(projectid),
                 'expires-by' : 'null'
              }
           }
    }

    if userid != None:
        user_data = {
             'user' : {
                'data' : {
                   'id' : str(userid),
                   'type' : 'users'
                }
             }
        }
        json_data['data']['relationships'].update(user_data)

    if groupid is not None:
        group_data = {
             'group' : {
                'data' : {
                   'id' : str(groupid),
                   'type' : 'groups'
                }
             }
        }
        json_data['data']['relationships'].update(group_data)

    if (debug >= 5): print(json_data)

    try:
        resp = endpoint.post(data=json.dumps(json_data))
    except jsonapi_requests.request_factory.ApiClientError as e:
        content = e.content.decode("utf-8")
        content = json.loads(content)
        print("Error Code " + str(e.status_code) + ": " + \
           content['errors'][0]['detail'])
        sys.exit(2)

# -----------------------------------------------------------------------------

'''
Function:       setTriage
Description:    Sets a triage comment for an issue
Input:          project id
                issue id
                triage data dict (ex. {'COMMENTARY': 'my comment', 'OWNER': 'id'})
Output:         API response
'''
def setTriage(projectId, issueId, triage_data):
    endpoint = api.endpoint('triage-command/v0/triage-issues')
    json_data = {
        'data' : {
            'attributes' : {
                'issue-keys': [issueId],
                'project-id': str(projectId),
                'triage-values': triage_data
            },
            'type':'triage-issues'
        }
    }

    try:
        resp = endpoint.post(data=json.dumps(json_data))
    except jsonapi_requests.request_factory.ApiClientError as e:
        content = e.content.decode("utf-8")
        content = json.loads(content)
        print("Error Code " + str(e.status_code) + ": " + \
           content['errors'][0]['detail'])
        sys.exit(2)

    return resp

# -----------------------------------------------------------------------------

'''
Function:       createUser
Description:    create a user
Input:          orgid, username, displayname, email
Output:         userid
'''
def createUser(orgid, username, displayname, email):
    endpoint = api.endpoint('auth/v1/users')
    json_data = {
        'data': {
            'type': 'users',
            'attributes': {
                'email': email,
                'name': displayname,
                'username': username,
                'enabled': True,
            },
            "relationships": {
                "organization": {
                    "data": {
                        "type": "organizations",
                        "id": orgid
                    }
                }
            }
        }
    }
    if (debug >= 5): print(json_data)
    try:
        response = endpoint.post(data=json.dumps(json_data))
    except jsonapi_requests.request_factory.ApiClientError as e:
        printError(e)
    if debug: print(response)
    return response.payload['data']['id']

# -----------------------------------------------------------------------------
