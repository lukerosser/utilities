from github import Github
import sys

# using an access token
g = Github(sys.argv[1])

for repo in g.get_user().get_repos():
    if repo.full_name.startswith("KPMG-UK/terraform12-"):
        if repo.get_clones_traffic()["count"] != 0:
            print(f"{repo.name} | {repo.get_clones_traffic()['count']}")
