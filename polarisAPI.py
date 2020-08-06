#!/usr/bin/python
'''
Copyright (c) 2020 Synopsys, Inc. All rights reserved worldwide. The information
contained in this file is the proprietary and confidential information of
Synopsys, Inc. and its licensors, and is supplied subject to, and may be used
only by Synopsys customers in accordance with the terms and conditions of a
previously executed license agreement between Synopsys and that customer.
Purpose: get issues for a given project & branch
Author: chuck.aude@synopsys.com
Date: 2019-12-05
Requires:
pip install jsonapi_requests pandas
Usage:
getIssues.py [-h] [--debug DEBUG] [--url URL] [--token TOKEN] --project PROJECT
             [--branch BRANCH] [--compare COMPARE]
             [--spec SPEC] [--new] [--fixed] [--date DATE]
             [--exit1-if-issues] [--csv] [--html] [--email EMAIL]
get issues for a given project & branch
optional arguments:
  -h, --help         show this help message and exit
  --debug DEBUG      set debug level [0-9]
  --url URL          Polaris URL
  --token TOKEN      Polaris Access Token
  --project PROJECT  project name
  --branch BRANCH    branch name
  --compare COMPARE  comparison branch name for new or fixed
  --spec SPEC        report specification
  --new              newly detected issues only
  --fixed            fixed issues only
  --date DATE        issues newer than date YYYY-MM-DDTHH:MM:SSZ
  --exit1-if-issues  exit with error code 1 if issues found
  --csv              output to CSV
  --html             output to HTML
  --email EMAIL      comma delimited list of email addresses
where SPEC is a comma delimited list of one or more of the following:
  project_id        project ID
  branch_id         branch ID
  key               issue key
  finding-key       issue finding key
  checker           checker aka subtool
  severity          severity
  type              issue type
  local_effect      local effect
  name              issue name
  description       issue description
  path              issue filepath
  first_detected    date first detected on
  url               URL to issue on Polaris
Examples:
list open issues:
python getIssues.py --url $POLARIS_SERVER_URL --token $POLARIS_ACCESS_TOKEN --project chuckaude-roller
list new issues since previous scan and send as email:
python getIssues.py --url $POLARIS_SERVER_URL --token $POLARIS_ACCESS_TOKEN --project chuckaude-roller \
    --new --email aude@synopsys.com
list issues detected after 2020-01-01 and output to csv:
python getIssues.py --url $POLARIS_SERVER_URL --token $POLARIS_ACCESS_TOKEN --project chuckaude-roller \
    --date 2020-01-01T00:00:00 --csv
break the build if any new issues are detected:
python getIssues.py --url $POLARIS_SERVER_URL --token $POLARIS_ACCESS_TOKEN --project chuckaude-roller \
    --new --exit1-if-issues
list new issues compared to master and fail the merge request with email:
python getIssues.py --url $POLARIS_SERVER_URL --token $POLARIS_ACCESS_TOKEN --project chuckaude-roller \
    --branch my-test-branch --compare master --new --email aude@synopsys.com --exit1-if-issues
'''

import sys
import os
import jsonapi_requests
import polaris

import pandas as pd
pd.set_option('display.max_rows', 100000)
pd.set_option('display.max_columns', 50)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', 300)

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# -----------------------------------------------------------------------------

def send_email(receiver_email):

    # @TODO read from config, this is my free sendgrid account
    smtp_server = 'smtp.sendgrid.net'
    smtp_port = 465
    smtp_username = 'apikey'
    smtp_password = 'SGc'

    sender_email = 'noreply@synopsys.com'

    message = MIMEMultipart('alternative')
    message['Subject'] = 'issue report for ' + project + '/' + branch
    if new: message['Subject'] = 'new ' + message['Subject']
    if fixed: message['Subject'] = 'fixed ' + message['Subject']
    message['From'] = sender_email
    message['To'] = receiver_email

    # Create the plain-text and HTML version of your message
    text = str(df)
    html = '<html>\n<body>\n' + df.to_html(escape=False) + '\n</body>\n</html>\n'

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    try:
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.ehlo()
        server.login(smtp_username, smtp_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.close()
        print('email sent')
    except:
        print('email failure')

# -----------------------------------------------------------------------------
def getIssues(project, branch):

    PAGE_LIMIT = 500

    url = os.getenv("POLARIS_URL", "")
    token = os.getenv("POLARIS_TOKEN", "")
    polaris.debug = debug = 0
    new = False
    fixed = False
    getTriage = False
    email = False
    html = False
    compare = None
    csv = False
    date = None
    exit1 = False
    reportSpec = 'path,checker,severity,url'.split(',')

    if ((url == None) or (token == None)):
        print('FATAL: POLARIS_SERVER_URL and POLARIS_ACCESS_TOKEN must be set via environment variables or the CLI')
        sys.exit(1)

    # convert token to JWT and configure jsonapi_requests
    polaris.token = polaris.getJwt(url, token)
    polaris.api = polaris.configApi(url)

    projectId = polaris.getProjectId(project)
    #if debug: print('project = ' + project + '\nprojectId = ' + projectId)

    branchId = polaris.getBranchId(projectId, branch)
    if debug: print('branch = ' + branch + '\nbranchId = ' + branchId)

    if date:
        # @TODO fix getPaginatedData to not exit when total=0
        filter=dict([('filter[issue][status-opened-date][$gte]', str(date) + 'Z')])
        issues = polaris.getIssues(projectId, branchId, None, PAGE_LIMIT, filter, getTriage)
    elif new or fixed:
        runs = polaris.getRuns(projectId, branchId)
        currRunId = runs[0]['runId']
        if debug: print ('currRunId = ' + currRunId)
        if (compare == None):
            try: cmpRunId = runs[1]['runId']
            # if no previous run, compare with self
            except: cmpRunId = currRunId
        else:
            compareId = polaris.getBranchId(projectId, compare)
            if debug: print('comprare = ' + compare + '\ncompareId = ' + compareId)
            runs = polaris.getRuns(projectId, compareId)
            cmpRunId = runs[0]['runId']
        if debug: print ('cmpRunId = ' + cmpRunId)
        new_issues_df, fixed_issues_df, common_issues_df, merged_df = polaris.cmpIssuesForRuns(projectId, currRunId, cmpRunId, getTriage)
        if new: issues = new_issues_df
        if fixed: issues = fixed_issues_df
    else:
        issues = polaris.getIssues(projectId, branchId, None, PAGE_LIMIT, None, getTriage)
    if (debug > 3): print(issues)

    # create a dataframe from issues dictionary
    df = pd.DataFrame(issues)

    # get issue count
    count = len(df.index)
    if (count == 0):
        print ('no issues')
        sys.exit(0)

    # link path to url
    if email or html: df['path'] = '<a href=' + df['url'] + '>' + df['path'] + '</a>'

    # select what we want from the dataframe
    df = df[reportSpec]

    # display the report
    if csv: df.to_csv(sys.stdout)
    elif html: df.to_html(sys.stdout, escape=False)
    elif email: send_email(email)
    else: print(df)

    return df.to_html()
