"""
This script provides some useful commands for batch removal of all
GitHub Actions workflow runs until such time as the GitHub UI
provides a way to do so. When a workflow has no references to
workflow runs, it is considered deleted and will no longer
appear in the GitHub UI.

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
    if params and '?' not in url:
        url = f"{url}?{urlencode(params)}"

    print(f'GET {url}')

    conn = http.client.HTTPSConnection("api.github.com")
    conn.request("GET", url, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return response.status, data, response.headers

def http_delete(url, headers, params=None):
    if params and '?' not in url:
        url = f"{url}?{urlencode(params)}"

    print(f'DELETE {url}')

    conn = http.client.HTTPSConnection("api.github.com")
    conn.request("DELETE", url, headers=headers)
    response = conn.getresponse()
    data = response.read()
    conn.close()

    return response.status, data

def parse_link_header(link_header):
    if not link_header:
        return None

    links = link_header.split(',')
    link_dict = {}

    for link in links:
        section = link.split(';')
        url = section[0].strip()[1:-1]
        rel = section[1].strip().split('=')[1][1:-1]
        link_dict[rel] = url

    return link_dict

def paginate(initial_url, request_headers, params=None):
    response_data = []
    url = initial_url

    while url:
        status, data, response_headers = http_get(url, request_headers, params)

        if status == 200:
            response_data.append(json.loads(data))
            links = parse_link_header(response_headers.get('Link'))
            url = links.get('next') if links else None
        else:
            print(f"Failed to retrieve items: {status}")
            print(data.decode('utf-8'))
            break

    return response_data

class DeleteWorkflowRuns:
    def __init__(self):
        self.owner = None
        self.repo = None
        self.token = None

    @property
    def headers(self):
        return {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "Python",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def list_workflows(self):
        url = f"/repos/{self.owner}/{self.repo}/actions/workflows"
        responses = paginate(url, self.headers, params={"per_page": 20})
        workflows = [workflow for response in responses for workflow in response["workflows"]]

        if not workflows:
            print("No workflows found.")
            return

        print("\nWorkflow ID\tWorkflow Name\n")

        for workflow in workflows:
            print(f"{workflow['id']}\t{workflow['name']}")

        print(f"\nTotal: {len(workflows)}")

    def list_workflow_runs(self, workflow_id):
        url = f"/repos/{self.owner}/{self.repo}/actions/workflows/{workflow_id}/runs"
        responses = paginate(url, self.headers, params={"per_page": 20})

        return [workflow_run for response in responses for workflow_run in response["workflow_runs"]]

    def delete_workflow_runs(self, workflow_id):
        workflow_runs = self.list_workflow_runs(workflow_id)

        if not workflow_runs:
            print("No workflow runs found.")
            return

        print(f"\nAre you sure you want to delete all {len(workflow_runs)} workflow runs?")
        confirm = input("This action cannot be undone! (y/n): ")

        if confirm.lower() != 'y':
            print("Aborted.")
            return

        print("\nAs you wish...\n")

        for run in workflow_runs:
            run_id = run['id']
            url = f"/repos/{self.owner}/{self.repo}/actions/runs/{run_id}"

            status, data = http_delete(url, headers=self.headers)

            if status == 204:
                print(f"Success")
            else:
                print(f"Failed: {status}")
                print(data.decode('utf-8'))

        print("\nDone.")

    def run(self):
        self.token = getpass.getpass("Enter your GitHub personal access token: ")

        commands = ["list_workflows", "delete_workflow_runs"]
        command = input(f"Enter command ({" / ".join(commands)}): ")

        if command not in commands:
            print("Invalid command")
            return

        self.owner = input("Enter the repository owner: ")
        self.repo = input("Enter the repository name: ")

        if command == "list_workflows":
            self.list_workflows()
        elif command == "delete_workflow_runs":
            workflow_id = input("Enter the workflow ID: ")
            self.delete_workflow_runs(workflow_id)

if __name__ == "__main__":
    DeleteWorkflowRuns().run()
