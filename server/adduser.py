"""Create or update a Gabrino login.

Usage:
    python adduser.py <username> [password]

If password is omitted you'll be prompted (input hidden).
"""

import getpass
import sys

from auth import add_user, USERS_FILE


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    username = sys.argv[1]
    if len(sys.argv) >= 3:
        password = sys.argv[2]
    else:
        password = getpass.getpass(f"Password for {username}: ")
        confirm = getpass.getpass("Confirm: ")
        if password != confirm:
            print("Passwords do not match.")
            sys.exit(1)

    if not password:
        print("Password cannot be empty.")
        sys.exit(1)

    add_user(username, password)
    print(f"Saved user '{username}' to {USERS_FILE}")


if __name__ == "__main__":
    main()
