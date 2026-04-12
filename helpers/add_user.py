#!/usr/bin/env python3
"""Manage klodTalk users. Stores username + SHA-256 hashed password in config/users.json."""

import argparse
import getpass
import hashlib
import json
import os
import sys
from datetime import datetime

USERS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "config", "users.json")
)


def load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE) as f:
        return json.load(f)


def save_users(users: dict):
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def add_user(username: str, password: str):
    users = load_users()
    if username in users:
        print(f"User '{username}' already exists. Use --update to change password.")
        sys.exit(1)
    users[username] = {
        "password_hash": hash_password(password),
        "created": datetime.now().isoformat(),
    }
    save_users(users)
    print(f"User '{username}' added successfully.")


def update_user(username: str, password: str):
    users = load_users()
    if username not in users:
        print(f"User '{username}' not found. Use 'add' to create.")
        sys.exit(1)
    users[username]["password_hash"] = hash_password(password)
    users[username]["updated"] = datetime.now().isoformat()
    save_users(users)
    print(f"Password updated for '{username}'.")


def delete_user(username: str):
    users = load_users()
    if username not in users:
        print(f"User '{username}' not found.")
        sys.exit(1)
    del users[username]
    save_users(users)
    print(f"User '{username}' deleted.")


def list_users():
    users = load_users()
    if not users:
        print("No users configured.")
        return
    print(f"{'Username':<20} {'Created':<25} {'Updated'}")
    print("-" * 70)
    for name, info in users.items():
        created = info.get("created", "?")
        updated = info.get("updated", "-")
        print(f"{name:<20} {created:<25} {updated}")



def interactive_mode():
    """Interactive mode — no arguments needed."""
    print("=== KlodTalk User Management ===")
    print()
    action = input("Action [add/update/delete/list]: ").strip().lower()

    if action == "list":
        list_users()
        return

    if action not in ("add", "update", "delete"):
        print(f"Unknown action: {action}")
        sys.exit(1)

    username = input("Username: ").strip()
    if not username:
        print("Username cannot be empty.")
        sys.exit(1)

    if action == "delete":
        confirm = input(f"Delete user '{username}'? [y/N]: ").strip().lower()
        if confirm == "y":
            delete_user(username)
        else:
            print("Cancelled.")
        return

    # add or update — need password
    pw = getpass.getpass("Password: ")
    pw_confirm = getpass.getpass("Confirm password: ")
    if pw != pw_confirm:
        print("Passwords do not match.")
        sys.exit(1)

    if action == "add":
        confirm = input(f"Add user '{username}'? [y/N]: ").strip().lower()
        if confirm == "y":
            add_user(username, pw)
        else:
            print("Cancelled.")
    elif action == "update":
        confirm = input(f"Update password for '{username}'? [y/N]: ").strip().lower()
        if confirm == "y":
            update_user(username, pw)
        else:
            print("Cancelled.")


def main():
    parser = argparse.ArgumentParser(description="Manage klodTalk users")
    sub = parser.add_subparsers(dest="command", help="Command")

    add_p = sub.add_parser("add", help="Add a new user")
    add_p.add_argument("username", help="Username")
    add_p.add_argument("--password", "-p", help="Password (prompted if omitted)")

    upd_p = sub.add_parser("update", help="Update a user's password")
    upd_p.add_argument("username", help="Username")
    upd_p.add_argument("--password", "-p", help="Password (prompted if omitted)")

    del_p = sub.add_parser("delete", help="Delete a user")
    del_p.add_argument("username", help="Username")

    sub.add_parser("list", help="List all users")

    args = parser.parse_args()

    if args.command is None:
        interactive_mode()
    elif args.command == "add":
        pw = args.password or getpass.getpass("Password: ")
        add_user(args.username, pw)
    elif args.command == "update":
        pw = args.password or getpass.getpass("New password: ")
        update_user(args.username, pw)
    elif args.command == "delete":
        delete_user(args.username)
    elif args.command == "list":
        list_users()


if __name__ == "__main__":
    main()
