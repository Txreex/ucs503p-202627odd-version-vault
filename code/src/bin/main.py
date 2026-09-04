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

from src.lib.Bvr.version_vault.folder_tracker import (
    trackFolder,
    saveFolderVersion,
    getFolderHistory,
    restoreFolderVersion,
    hasFolderChanged
)


REPO_PATH = "/tmp/version_vault_repo"


def printUsage():
    print("""
VersionVault CLI

Single File Commands:
    vv init
    vv track <file-id> <file-path>
    vv save <file-id> <file-path>
    vv history <file-id>
    vv restore <commit-hash> <file-path>

Folder Commands:
    vv track-folder <folder-path>
    vv status <folder-path>
    vv save-folder <folder-path> "<message>"
    vv history-folder <folder-path>
    vv restore-folder <folder-path> <commit-hash>
""")


def main():

    if len(sys.argv) < 2:
        printUsage()
        return 1

    command = sys.argv[1]

    # ========================================================
    # SINGLE FILE COMMANDS
    # ========================================================

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

        if trackFile(
            REPO_PATH,
            sys.argv[2],
            sys.argv[3]
        ):
            print("File tracked successfully.")
        else:
            print("Failed to track file.")

    # vv save f1 notes.txt
    elif command == "save":

        if len(sys.argv) != 4:
            print("Usage: vv save <file-id> <file-path>")
            return 1

        if saveVersion(
            REPO_PATH,
            sys.argv[2],
            sys.argv[3]
        ):
            print("New version saved successfully.")
        else:
            print("Failed to save version.")

    # vv history f1
    elif command == "history":

        if len(sys.argv) != 3:
            print("Usage: vv history <file-id>")
            return 1

        history = getHistory(
            REPO_PATH,
            sys.argv[2]
        )

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

        if restoreVersion(
            REPO_PATH,
            sys.argv[2],
            sys.argv[3]
        ):
            print("Version restored successfully.")
        else:
            print("Failed to restore version.")

    # ========================================================
    # FOLDER COMMANDS
    # ========================================================

    # vv track-folder <folder-path>
    elif command == "track-folder":

        if len(sys.argv) != 3:
            print("Usage: vv track-folder <folder-path>")
            return 1

        if trackFolder(sys.argv[2]):
            print("SUCCESS: Folder is now being tracked.")
        else:
            print("FAILED: Could not track folder.")

    # vv status <folder-path>
    elif command == "status":

        if len(sys.argv) != 3:
            print("Usage: vv status <folder-path>")
            return 1

        if hasFolderChanged(sys.argv[2]):
            print("Changes detected.")
        else:
            print("No changes detected.")

    # vv save-folder <folder-path> "<message>"
    elif command == "save-folder":

        if len(sys.argv) != 4:
            print("Usage: vv save-folder <folder-path> \"<message>\"")
            return 1

        if saveFolderVersion(
            sys.argv[2],
            sys.argv[3]
        ):
            print("SUCCESS: Folder version saved.")
        else:
            print("FAILED: Could not save version.")

    # vv history-folder <folder-path>
    elif command == "history-folder":

        if len(sys.argv) != 3:
            print("Usage: vv history-folder <folder-path>")
            return 1

        history = getFolderHistory(sys.argv[2])

        if not history:
            print("No versions found.")
            return 0

        print("\nFolder Version History")
        print("======================")

        for i, commit in enumerate(history):
            print(f"{i + 1}. {commit}")

    # vv restore-folder <folder-path> <commit-hash>
    elif command == "restore-folder":

        if len(sys.argv) != 4:
            print("Usage: vv restore-folder <folder-path> <commit-hash>")
            return 1

        if restoreFolderVersion(
            sys.argv[2],
            sys.argv[3]
        ):
            print("SUCCESS: Folder restored.")
        else:
            print("FAILED: Could not restore version.")

    # ========================================================
    # UNKNOWN COMMAND
    # ========================================================

    else:
        print(f"Unknown command: {command}")
        printUsage()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())