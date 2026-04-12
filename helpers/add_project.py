#!/usr/bin/env python3
"""Manage klodTalk projects. Stores project definitions in config/projects.json.

Each project has: name, users (allowed users list), description, folder.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

PROJECTS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "projects.json")
)


def _sanitize_image_name(project_name: str) -> str:
    """Convert project name to a Docker image name for uniqueness check."""
    name = project_name.lower()
    name = re.sub(r'[^a-z0-9_]', '_', name)
    name = re.sub(r'_+', '_', name)
    name = name.strip('_')
    return f"klodtalk_{name}"


def load_projects() -> list:
    if not os.path.exists(PROJECTS_FILE):
        return []
    with open(PROJECTS_FILE) as f:
        return json.load(f)


def save_projects(projects: list):
    os.makedirs(os.path.dirname(PROJECTS_FILE), exist_ok=True)
    with open(PROJECTS_FILE, "w") as f:
        json.dump(projects, f, indent=2)


def find_project(projects: list, name: str) -> int:
    for i, a in enumerate(projects):
        if a["name"] == name:
            return i
    return -1


def add_project(name: str, users: list[str], description: str, folder: str,
                docker_commit: bool = True, docker_socket: bool = False):
    projects = load_projects()
    if find_project(projects, name) >= 0:
        print(f"Project '{name}' already exists. Use 'modify' to update.")
        sys.exit(1)
    new_image = _sanitize_image_name(name)
    for existing in projects:
        if _sanitize_image_name(existing["name"]) == new_image and existing["name"] != name:
            print(f"Project '{name}' conflicts with '{existing['name']}' "
                  f"(both map to Docker image '{new_image}'). Choose a different name.")
            sys.exit(1)
    projects.append({
        "name": name,
        "users": users,
        "description": description,
        "folder": folder,
        "docker_commit": docker_commit,
        "docker_socket": docker_socket,
        "created": datetime.now().isoformat(),
    })
    save_projects(projects)
    print(f"Project '{name}' added (users={users}).")


def modify_project(name: str, users: list[str] = None, description: str = None, folder: str = None):
    projects = load_projects()
    idx = find_project(projects, name)
    if idx < 0:
        print(f"Project '{name}' not found.")
        sys.exit(1)
    if users is not None:
        projects[idx]["users"] = users
    if description is not None:
        projects[idx]["description"] = description
    if folder is not None:
        projects[idx]["folder"] = folder
    projects[idx]["updated"] = datetime.now().isoformat()
    save_projects(projects)
    print(f"Project '{name}' updated.")


def delete_project(name: str):
    projects = load_projects()
    idx = find_project(projects, name)
    if idx < 0:
        print(f"Project '{name}' not found.")
        sys.exit(1)
    projects.pop(idx)
    save_projects(projects)
    print(f"Project '{name}' deleted.")


def list_projects(user_filter: str = None):
    projects = load_projects()
    if user_filter:
        projects = [a for a in projects if user_filter in a.get("users", [])]
    if not projects:
        print("No projects found.")
        return
    print(f"{'Name':<20} {'Users':<20} {'Description':<30} {'Folder'}")
    print("-" * 95)
    for a in projects:
        users_str = ", ".join(a.get("users", []))
        print(f"{a['name']:<20} {users_str:<20} {a['description']:<30} {a['folder']}")


def main():
    parser = argparse.ArgumentParser(description="Manage klodTalk projects")
    sub = parser.add_subparsers(dest="command", help="Command")

    add_p = sub.add_parser("add", help="Add a new project")
    add_p.add_argument("-n", "--name", help="Project name (unique identifier)")
    add_p.add_argument("-u", "--users", required=True, nargs="+", help="Allowed usernames")
    add_p.add_argument("-d", "--description", required=True, help="Project description")
    add_p.add_argument("-f", "--folder", required=True, help="Project working folder")
    add_p.add_argument("--docker-commit", action="store_true", default=True,
                       dest="docker_commit",
                       help="Enable docker commit on session close (default: true)")
    add_p.add_argument("--no-docker-commit", action="store_false",
                       dest="docker_commit",
                       help="Disable docker commit on session close")
    add_p.add_argument("--docker-socket", action="store_true", default=False,
                       help="Mount Docker socket into container")

    mod_p = sub.add_parser("modify", help="Modify an existing project")
    mod_p.add_argument("name", help="Project name")
    mod_p.add_argument("--users", "-u", nargs="+", help="New allowed usernames")
    mod_p.add_argument("--description", "-d", help="New description")
    mod_p.add_argument("--folder", "-f", help="New folder")

    del_p = sub.add_parser("delete", help="Delete a project")
    del_p.add_argument("name", help="Project name")

    list_p = sub.add_parser("list", help="List projects")
    list_p.add_argument("--user", "-u", help="Filter by user")

    args = parser.parse_args()

    if args.command == "add":
        add_project(args.name, args.users, args.description, args.folder,
                    args.docker_commit, args.docker_socket)
    elif args.command == "modify":
        modify_project(args.name, args.users, args.description, args.folder)
    elif args.command == "delete":
        delete_project(args.name)
    elif args.command == "list":
        list_projects(args.user)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
