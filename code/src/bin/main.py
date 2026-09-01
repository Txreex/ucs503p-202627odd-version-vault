
import sys

# Change this import based on the actual project structure
# from lib.Bvr.version_vault.core import (
#     initRepo,
#     trackFile,
#     saveVersion,
#     getHistory,
#     restoreVersion
# )
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.lib.Bvr.version_vault.core import (
    initRepo,
    trackFile,
    saveVersion,
    getHistory,
    restoreVersion
)

REPO_PATH = "/tmp/version_vault_repo"


def printUsage():
    print("""
VersionVault CLI

Usage:
  vv init
  vv track <file-id> <file-path>
  vv save <file-id> <file-path>
  vv history <file-id>
  vv restore <commit-hash> <file-path>
""")


def main():
    if len(sys.argv) < 2:
        printUsage()
        return 1

    command = sys.argv[1]

    # vv init
    if command == "init":
        if initRepo(REPO_PATH):
            print("Repository initialized successfully.")
        else:
            print("Failed to initialize repository.")

    # vv track f1 notes.txt
    elif command == "track":
        if len(sys.argv) != 4:
            print("Usage: vv track <file-id> <file-path>")
            return 1

        if trackFile(REPO_PATH, sys.argv[2], sys.argv[3]):
            print("File tracked successfully.")
        else:
            print("Failed to track file.")

    # vv save f1 notes.txt
    elif command == "save":
        if len(sys.argv) != 4:
            print("Usage: vv save <file-id> <file-path>")
            return 1

        if saveVersion(REPO_PATH, sys.argv[2], sys.argv[3]):
            print("New version saved successfully.")
        else:
            print("Failed to save version.")

    # vv history f1
    elif command == "history":
        if len(sys.argv) != 3:
            print("Usage: vv history <file-id>")
            return 1

        history = getHistory(REPO_PATH, sys.argv[2])

        if not history:
            print("No version history found.")
            return 0

        print("\nVersion History")
        print("===============")

        for i, commit in enumerate(history):
            print(f"{i + 1}. {commit}")

    # vv restore <commit-hash> <file-path>
    elif command == "restore":
        if len(sys.argv) != 4:
            print("Usage: vv restore <commit-hash> <file-path>")
            return 1

        if restoreVersion(REPO_PATH, sys.argv[2], sys.argv[3]):
            print("Version restored successfully.")
        else:
            print("Failed to restore version.")

    else:
        print(f"Unknown command: {command}")
        printUsage()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

