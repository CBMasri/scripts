"""
This script provides some useful commands for batch removal of all
GitHub Actions workflow runs until such time as the GitHub UI
provides a way to do so. When a workflow has no references to
workflow runs, it is considered deleted and will no longer
appear in the GitHub UI.

At the moment, the maximum number of workflow runs that can be
deleted in a single go is 100. If you have more than 100 workflow
runs to delete, run the script multiple times.

Commands:

list_workflows: List all workflows in a repository, along with their IDs.
delete_workflow_runs: Delete all workflow runs for a specific workflow ID.

Usage:

python delete_workflow_runs.py
"""

import getpass
import http.client
import json
from urllib.parse import urlencode

def http_get(url, headers, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"

    print(f'GET {url}')

    conn = http.client.HTTPSConnection("api.github.com")
    conn.request("GET", url, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return response.status, data

def http_delete(url, headers, params=None):
    if params:
        url = f"{url}?{urlencode(params)}"

    print(f'DELETE {url}')

    conn = http.client.HTTPSConnection("api.github.com")
    conn.request("DELETE", url, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return response.status, data

def list_workflows(owner, repo, token):
    url = f"/repos/{owner}/{repo}/actions/workflows"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Python",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    status, data = http_get(url, headers, params={"per_page": 100})

    if status == 200:
        workflows = json.loads(data)["workflows"]
        print("\nWorkflow ID\tWorkflow Name\n")
        for workflow in workflows:
            print(f"{workflow['id']}\t{workflow['name']}")
        print(f"\nTotal: {len(workflows)}")
    else:
        print(f"Failed to list workflows: {status}")
        print(data.decode('utf-8'))

def delete_workflow_runs(owner, repo, workflow_id, token):
    url = f"/repos/{owner}/{repo}/actions/workflows/{workflow_id}/runs"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "Python",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    status, data = http_get(url, headers, params={"per_page": 100})

    if status == 200:
        runs = json.loads(data)["workflow_runs"]

        if not runs:
            print("No workflow runs found.")
            return

        print(f"\nAre you sure you want to delete all {len(runs)} workflow runs?")
        confirm = input("This action cannot be undone! (y/n): ")

        if confirm.lower() != 'y':
            print("Aborted.")
            return

        print("\nAs you wish...\n")

        for run in runs:
            run_id = run['id']
            delete_url = f"/repos/{owner}/{repo}/actions/runs/{run_id}"
            delete_status, delete_data = http_delete(delete_url, headers)

            if delete_status == 204:
                print(f"Success")
            else:
                print(f"Failed: {delete_status}")
                print(delete_data.decode('utf-8'))

        print("\nDone.")
    else:
        print(f"Failed to list workflow runs: {status}")
        print(data.decode('utf-8'))

def main():
    token = getpass.getpass("Enter your GitHub personal access token: ")
    command = input("Enter command (list_workflows / delete_workflow_runs): ")

    if command == "list_workflows":
        owner = input("Enter the repository owner: ")
        repo = input("Enter the repository name: ")
        list_workflows(owner, repo, token)
    elif command == "delete_workflow_runs":
        owner = input("Enter the repository owner: ")
        repo = input("Enter the repository name: ")
        workflow_id = input("Enter the workflow ID: ")
        delete_workflow_runs(owner, repo, workflow_id, token)
    else:
        print("Invalid command")

if __name__ == "__main__":
    main()
