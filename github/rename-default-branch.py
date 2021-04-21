from github import Github, GithubException
import sys
import logging
import datetime
import requests
import argparse
import re

parser = argparse.ArgumentParser()
parser.add_argument(
    "-t", "--token", help="Github personal access token for auth", required=True
)
parser.add_argument(
    "-b", "--new_branch_name", help="Name of the new default branch", required=True
)
# could be improved by accepting multiple values
# could make pattern or topic filter optional (so that only one must be provided)
parser.add_argument(
    "-f",
    "--topic_filter",
    help="Name of a topic to filter repositories on",
    required=True,
)
# using regex instead of the built in github search as it's more explicit
parser.add_argument(
    "-p",
    "--pattern",
    help="Regex pattern to match repository name. Multiple patterns can be provided, matching done as an OR",
    required=True,
    action="append",
)
parser.add_argument(
    "-d",
    "--dry_run",
    help="Dry run doesn't make changes but logs what would happen",
    required=False,
    default=False,
    action="store_true",
)

args = parser.parse_args()
runtime = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
log_file = f"github-branch-rename-{runtime}.log"

logging.basicConfig(filename=log_file, encoding="utf-8", level=logging.INFO)

repositories = 0
errors = 0

if args.dry_run:
    logging.warning(
        "Dry run enabled - logging indicates what would happen. No changes will be made."
    )

# using an access token
g = Github(args.token)

search_query = f"topic:{args.topic_filter} org:KPMG-UK archived:false fork:false"

for repo in g.search_repositories(query=search_query):
    new_default_branch_exists = True
    regex_match = False
    for p in args.pattern:
        if re.match(p, repo.name):
            regex_match = True
    if regex_match:
        repositories += 1
        logging.info(f"Processing repository {repo.full_name}")
        if repo.default_branch != args.new_branch_name:
            # check if the branch already exists
            try:
                repo.get_branch(args.new_branch_name)
            except GithubException as e:
                new_default_branch_exists = False

            if not new_default_branch_exists:
                logging.info(
                    f"Renaming default branch, {repo.default_branch} to {args.new_branch_name} on repository {repo.full_name}"
                )

                request_headers = {
                    "Authorization": f"token {args.token}",
                    "Content-Type": "application/json",
                }

                if not args.dry_run:
                    # python Github library doesn't support branch renaming yet so using REST API
                    # ref: https://github.com/PyGithub/PyGithub/issues/1901
                    r = requests.post(
                        f"https://api.github.com/repos/{repo.full_name}/branches/{repo.default_branch}/rename",
                        headers=request_headers,
                        json={"new_name": args.new_branch_name},
                    )

                    if r.status_code != 201:
                        logging.error(
                            f"Failed to rename branch {repo.default_branch} to {args.new_branch_name}. API response code {r.status_code}"
                        )
                        errors += 1
            else:
                logging.error(
                    f"{args.new_branch_name} branch already exists on repository {repo.name}"
                )
                errors += 1

        else:
            logging.info(
                f"Repository {repo.full_name} already uses {args.new_branch_name} as default branch"
            )

print(
    f"\nBranch renaming complete.\n\nNumber of repositories found: {repositories}\nErrors: {errors}\n\nRefer to the log file for more information: {log_file}"
)
