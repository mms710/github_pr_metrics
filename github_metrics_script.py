# import json, csv, API request (requests), regex parser (re), and command line interface
# package (click)
import json
import csv
import requests
import re
import click

# TODO:
# 1) Add options for all time vs specific time range
# 2) Add option and functionality for just pulling your repos

# Generate a GitHub auth token at https://github.com/settings/tokens. It only requires
# the "public_repo" permission.
GITHUB_OAUTH_TOKEN = '<INSERT TOKEN HERE>'
# change this list of org names to have this work on other GitHub orgs
org_list = [<INSERT LIST OF ORG NAMES HERE>]

# This is the authentication header we'll use throughout this script
auth_header = {'Authorization': 'token ' + GITHUB_OAUTH_TOKEN}

# dummy date inputs until I put click functionality in here
start_date = '2019-04-22'
end_date = '2019-04-23'

# Define a paginationChecker function. This function's input is a GitHub API request and
# it determines if your results are paginated, then returns a true or false result and 
# the number of pages in the paginated results
def paginationChecker(api_request):
    api_request_headers = api_request.headers
    page = 0
    if 'Link' in api_request_headers.keys():
        paginated = True # sets pagination value to true if the results are paginated
        header = api_request_headers['Link'] # the "Link" key only exists if it's paginated
        # create regex for last page number
        end_page_regex = re.compile('.*page=(\d+).*rel="last"')
        end_page_number = re.match(end_page_regex, header) # find match in header
        page_list = end_page_number.groups() # list the matching regexes
        # grab the first element of the list, which is the last page number of the
        # paginated results, and make it an integer so we can do maths with it
        page = int(page_list[0])
    else:
        paginated = False
    return {'paginated': paginated, 'page_num': page}

# Define a repoListMaker function. This function takes an input of an org name (a string).
# calls the GitHub API and returns dictionary of repos in an org
def repoListMaker (org_name):
    # create URL for repos curl command, substituting the org name into the API call
    # and grabbing only the first page of results for consistency
    url = 'https://api.github.com/orgs/{}/repos?page=1'.format(org_name)
    #create header for auth, substituting the auth token defined above
    repos_request = requests.get(url, headers = auth_header) # make API request
    # check to make sure the request went through; if not print us the error code
    if repos_request.status_code != 200:
        print "Repos request page 1 status code " + str(repos_request.status_code)
    repos_data_list = json.loads(repos_request.text) #load the json response in list form 
    repo_names = {} #create a dictionary for the repos
    # Run paginationChecker function to see if the results are paginated
    page_info_dict = paginationChecker(repos_request)
    x = 0 # create variable to use in for loop, starting at list index 0
    # if the results are paginated, iterate through the pages, making an API call for
    # each page (note that we're going backwards through the pages because that was 
    # easier to do
    if page_info_dict['paginated'] == True:
        page = page_info_dict['page_num']
        while page > 0:
            x = 0 # reset x to 0 every time you look at a new page
            #change the API request to specify which page of results you're looking at
            url = 'https://api.github.com/orgs/{}/repos?page={}'.format(org_name, page)
            repos_request = requests.get(url, headers = auth_header) # make API request
            # check to make sure the request went through; if not print us the error code
            if repos_request.status_code != 200:
                print "Repos request status code other pages " + str(repos_request.status_code)
            #load the json response in list form
            repos_data_list = json.loads(repos_request.text)
            for repos in repos_data_list:
                entry = repos_data_list[x] # look at the current entry
                repo_name = entry['name'] # pull the name info out of the current entry
                repo_names.setdefault(org_name, []).append(repo_name)
                x +=1
            page = page - 1
    # go through all elements in API response list and put repo names in the repo_names
    # list
    else:
        for repos in repos_data_list:
            entry = repos_data_list[x] # look at the current entry
            repo_name = entry['name'] # pull the name info out of the current entry
            repo_names.setdefault(org_name, []).append(repo_name)
            x +=1
    return repo_names

#run repoListMaker function for all orgs in list defined at the beginning
y = 0 #create variable to use in for loop, starting at list index 0
for org in org_list:
    repoListMaker(org_list[y])
    y +=1
    
# Define a prCreationMetrics function. This function takes an input of a list of PR data
# dictionaries and outputs a dictionary of format {'org': 'zcash', 'repo': 'zips',
# 'pr_opener': 'str4d', 'pr_number': '226', 'pr_opened_time': '2011-04-10T20:09:31Z'}
pr_creation_dict = {} # create global dict for pr creation metrics
total_pr_list = [] # declaring global list to append PR dictionaries
def prCreationMetrics(org_name, repo_name, prs_data_list):
    for pr in prs_data_list:
        pr_dict = {} # create pr entry dictionary
        pr_number = pr['number'] #get PR number from entry
        pr_user_info = pr['user'] # get user info from entry
        pr_opener = pr_user_info['login'] # get PR opener's login name
        pr_opened_time = pr['created_at']
        pr_dict['org'] = org_name # set org name from input of function
        pr_dict['repo_name'] = repo_name #set repo name from input of function
        pr_dict['pr_number'] = pr_number
        pr_dict['pr_opener'] = pr_opener
        pr_dict['pr_opened_time'] = pr_opened_time
        if pr_opener in pr_creation_dict.keys():
            pr_creation_dict[pr_opener] +=1
        else:
            pr_creation_dict[pr_opener] = 1
        total_pr_list.append(pr_dict)
        
# Define a prReviewMetrics function. This function takes an input of a list of review
# data dictionaries from GitHub and returns a dictionary of PR reviewers with total
# review counts
pr_review_dict = {} # create global dict for pr review metrics
def prReviewMetrics(review_data):
    for pr_review in review_data:
        if pr_review in review_data:
            reviewer_info = pr_review['user']
        else:
            break
        if reviewer_info and 'login' in reviewer_info:
            reviewer = reviewer_info['login']
        else:
            break
        if reviewer in pr_review_dict.keys():
            pr_review_dict[reviewer] +=1
        else:
            pr_review_dict[reviewer] = 1
        return pr_review_dict
     

# function that collects PR data from the GitHub API and outputs PR creation and review 
# data
pr_review_error_data = {} # create a global dict for PR error data
def prCreationDataCollection(org_name, repo_name):
    #create header for API calls in this function, substituting the auth token defined above
    auth_header = {'Authorization': 'token ' + GITHUB_OAUTH_TOKEN}
    #create a URL for PRs curl command, substituting the repo name into the API call
    # and grabbing only the first page of results for consistency
    url = 'https://api.github.com/repos/{}/{}/pulls?page=1&state=all'.format(org_name, repo_name)
    prs_request = requests.get(url, headers = auth_header) # make API request
    # check to make sure the request went through; if not print us the error code
    if prs_request.status_code != 200:
        print "List of PRs page 1 status code " + str(prs_request.status_code)
    prs_data_list = json.loads(prs_request.text) # turn json payload into string
    # only record the PR info if there is PR data to record
    if prs_request != []:
        # Run paginationChecker function to see if the results are paginated
        page_info_dict = paginationChecker(prs_request)
        # if the results are paginated, iterate through the pages, making an API call for
        # each page (note that we're going backwards through the pages because that was 
        # easier to do)
        if page_info_dict['paginated'] == True:
            page = page_info_dict['page_num']
            while page > 0:
                url = 'https://api.github.com/repos/{}/{}/pulls?page={}&state=all'.format(org_name, repo_name, page)
                prs_request = requests.get(url, headers = auth_header) # make API request
                if prs_request == []: # if there are no PRs, move onto the next repo
                    break
                # check to make sure the request went through; if not print us the error code
                if prs_request.status_code != 200:
                    print "List of PRs other pages status code " + str(prs_request.status_code)
                prs_data_list = json.loads(prs_request.text) # turn json payload into dictionary
                prCreationMetrics(org_name, repo_name, prs_data_list)
                page = page - 1
        else:
            prCreationMetrics(org_name, repo_name, prs_data_list)
        # Go through all the entries of the global prs list and create URL for PR reviewers
        # curl command, substituting org name, repo name, and pull request numbers into the
        # API call, and grabbing only the first page of results for consistency
        for pr_dict_entry in total_pr_list:
            url = 'https://api.github.com/repos/{}/{}/pulls/{}/reviews?page=1'.format(org_name, repo_name, pr_dict_entry['pr_number'])
            review_request = requests.get(url, headers = auth_header) # make API request
            # check to make sure the request went through; if not print us the error code
            if review_request.status_code != 200:
                print "List of reviews page 1 status code " + str(review_request.status_code)
                print org_name
                print repo_name
                print pr_dict_entry['pr_number']
                pr_review_error_data[repo_name] = pr_dict_entry['pr_number']
                break
            review_data = json.loads(review_request.text) # turn json payload into dictionary
            # run paginationChecker function to see if the results are paginated
            page_info_dict = paginationChecker(review_request)
            # if the results are paginated, iterate through the pages, making an API call for
            # each page (note that we're going backwards through the pages because that was 
            # easier to do)
            if page_info_dict['paginated'] == True:
                page = page_info_dict['page_num']
                while page > 0:
                    url = 'https://api.github.com/repos/{}/{}/pulls/{}/reviews?page={}'.format(org_name, repo_name, pr_dict_entry['pr_number'], page)
                    review_request = requests.get(url, headers = auth_header)
                    # check to make sure the request went through; if not print us the error code
                    if review_request.status_code != 200:
                        print "List of reviews other pages status code " + str(review_request.status_code)
                    review_data = json.loads(review_request.text)
                    pr_review_dict = prReviewMetrics(review_data)
                    page = page - 1
            else:
                pr_review_dict = prReviewMetrics(review_data) 
    return;

# Now let's put this all together and run the prCreationDataCollection function on every
# repo in every org
for org in org_list:
    repo_names = repoListMaker(org)
    for org_name in repo_names.keys():
        for repo in repo_names[org_name]:
            prCreationDataCollection(org_name, repo) 

# Great! Now let's put everything in a csv. We'll put the PR creation metrics in one csv,
# the PR review metrics in another csv, and the PR metrics error data in a third csv.
# Open a csv file in write mode for PR creation metrics in the directory you're running
# the script

# open a csv in write mode for the PR opening metrics
with open('pr_creation_metrics.csv', 'w') as csvfile:
    metrics_writer = csv.writer(csvfile)
    # create the column names for the PR creation metrics csv
    pr_creation_headers = ['GitHub Username', 'PRs Created']
    metrics_writer.writerow(pr_creation_headers) # write the headers to the csv file
    # go through the PR creation data dictionary and write the key and
    # value in the corresponding columns of the csv
    for pr_record in pr_creation_dict:
        metrics_writer.writerow([pr_record, pr_creation_dict[pr_record]])

# open a csv in write mode for the PR review metrics
with open('pr_review_metrics.csv', 'w') as csvfile2:
    review_metrics_writer = csv.writer(csvfile2)
    # create the column names for the PR review metrics csv
    pr_review_headers =  ['GitHub Username', 'PRs Reviewed']
    review_metrics_writer.writerow(pr_review_headers) # write the headers to the csv file
    # go through the PR review data dictionary and write the key and value in the
    # corresponding columns of the csv
    for review_record in pr_review_dict:
        review_metrics_writer.writerow([review_record, pr_review_dict[review_record]])

# open a csv in write mode for the PR error data
with open('pr_review_error_data.csv', 'w') as csvfile3:
    error_metrics_writer = csv.writer(csvfile3)
    # create the column names for the PR error metrics csv
    pr_error_headers =  ['Repo', 'PR Number']
    error_metrics_writer.writerow(pr_error_headers) # write the headers to the csv file
    # go through the PR error dictionary and write the key and value in the corresponding
    # columns of the csv
    for error_record in pr_review_error_data:
        error_metrics_writer.writerow([error_record, pr_review_error_data[error_record]])

