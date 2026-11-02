import sys
import subprocess
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from src.lib.Bvr.version_vault.core import (
    initRepo,
    trackFile,
    saveVersion,
    getHistory,
    restoreVersion
)

from src.lib.Bvr.version_vault.track_folder import (
    trackFolder,
    saveFolderVersion,
    getFolderHistory,
    restoreFolderVersion,
    hasFolderChanged
)

from src.lib.Bvr.version_vault.database import (
    addItem,
    getItemByPath,
    generateItemId
)


REPO_PATH = "/tmp/version_vault_repo"


def executeCommand(command, cwd=None):
    return subprocess.run(
        command,
        cwd=cwd
    ).returncode == 0


def printUsage():
    print("""
VersionVault CLI

Single File Commands:

    vv init
    vv track <file-path>
    vv save <file-path>
    vv history <file-path>
    vv restore <commit-hash> <file-path>

Folder Commands:

    vv track-folder <folder-path>
    vv status <folder-path>
    vv save-folder <folder-path> "<message>"
    vv history-folder <folder-path>
    vv restore-folder <folder-path> <commit-hash>

Ignore Commands:

    vv ignore <folder-path> <file-or-folder>
    vv ignore <folder-path> <file-or-folder> --remove
""")


def updateGitIgnore(folderPath, pattern, remove=False):
    """
    Add or remove a rule in .gitignore.

    When adding a rule, remove matching ignored files from
    Git's index without deleting them from the filesystem.
    """

    folder = Path(folderPath).expanduser().resolve()

    if not folder.is_dir():
        print("Error: Folder does not exist.")
        return False

    if not (folder / ".git").exists():
        print("Error: Folder is not a Git repository.")
        return False

    pattern = pattern.strip()

    if not pattern:
        print("Error: Ignore pattern cannot be empty.")
        return False

    # Convert absolute paths inside the folder to relative paths.
    candidate = Path(pattern).expanduser()

    if candidate.is_absolute():
        candidate = candidate.resolve()

        try:
            pattern = candidate.relative_to(folder).as_posix()
        except ValueError:
            print("Error: Path must be inside the tracked folder.")
            return False

    # Prevent relative paths from escaping the tracked folder.
    if not any(char in pattern for char in ("*", "?", "[")):
        normalized = pattern.rstrip("/")

        if normalized:
            candidate = (folder / normalized).resolve()

            try:
                pattern = candidate.relative_to(folder).as_posix()
            except ValueError:
                print("Error: Path must be inside the tracked folder.")
                return False

    gitignore = folder / ".gitignore"

    # Read existing rules.
    if gitignore.exists():
        try:
            content = gitignore.read_text(encoding="utf-8")
        except OSError as error:
            print(f"Error reading .gitignore: {error}")
            return False
    else:
        content = ""

    lines = content.splitlines()

    if remove:
        # Remove matching rules.
        updatedLines = [
            line for line in lines
            if line.strip() != pattern
        ]

        if len(updatedLines) == len(lines):
            print("Ignore rule not found.")
            return False

        updatedContent = "\n".join(updatedLines)

        if updatedContent:
            updatedContent += "\n"

        try:
            gitignore.write_text(
                updatedContent,
                encoding="utf-8"
            )
        except OSError as error:
            print(f"Error updating .gitignore: {error}")
            return False

        # Stage the changed .gitignore.
        if not executeCommand(
            ["git", "add", "--", ".gitignore"],
            cwd=folder
        ):
            print("Error staging .gitignore.")
            return False

        print(f"Removed ignore rule: {pattern}")
        print("Run vv save-folder to save the change.")

        return True

    # Don't add duplicate rules.
    if pattern in [line.strip() for line in lines]:
        print(f"Ignore rule already exists: {pattern}")
    else:
        try:
            with gitignore.open(
                "a",
                encoding="utf-8"
            ) as file:
                if content and not content.endswith("\n"):
                    file.write("\n")

                file.write(pattern + "\n")

        except OSError as error:
            print(f"Error updating .gitignore: {error}")
            return False

        print(f"Added ignore rule: {pattern}")

    # Find tracked files that are now ignored.
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "-ci",
            "--exclude-standard",
            "-z"
        ],
        cwd=folder,
        capture_output=True
    )

    if result.returncode != 0:
        print("Error checking tracked files.")
        return False

    ignoredFiles = [
        path.decode("utf-8", errors="surrogateescape")
        for path in result.stdout.split(b"\0")
        if path
    ]

    # Remove only ignored files from the index.
    # Their actual filesystem contents are preserved.
    if ignoredFiles:
        result = subprocess.run(
            [
                "git",
                "rm",
                "-r",
                "--cached",
                "--ignore-unmatch",
                "--",
                *ignoredFiles
            ],
            cwd=folder,
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(
                "Error removing ignored files from Git index:",
                result.stderr
            )
            return False

        print(
            f"Untracked {len(ignoredFiles)} ignored file(s) "
            "from Git's index. Files remain on disk."
        )
    else:
        print("No currently tracked ignored files need untracking.")

    # Stage .gitignore so the rule is included in the next version.
    if not executeCommand(
        ["git", "add", "--", ".gitignore"],
        cwd=folder
    ):
        print("Error staging .gitignore.")
        return False

    print("Ignore rule applied successfully.")
    print('Run vv save-folder "<folder-path>" "<message>" to commit it.')

    return True


def main():

    if len(sys.argv) < 2:
        printUsage()
        return 1

    command = sys.argv[1]

    # ========================================================
    # INIT
    # ========================================================

    if command == "init":

        if initRepo(REPO_PATH):
            print("Repository initialized successfully.")
        else:
            print("Failed to initialize repository.")

    # ========================================================
    # SINGLE FILE TRACK
    # ========================================================

    elif command == "track":

        if len(sys.argv) != 3:
            print("Usage: vv track <file-path>")
            return 1

        filePath = sys.argv[2]

        existingItem = getItemByPath(filePath)

        if existingItem:
            print(
                f"Error: File is already being tracked "
                f"with ID {existingItem[0]}."
            )
            return 1

        fileId = generateItemId("file")

        if not trackFile(
            REPO_PATH,
            fileId,
            filePath
        ):
            print("Failed to track file.")
            return 1

        if not addItem(
            fileId,
            "file",
            filePath
        ):
            print("Failed to register file in database.")
            return 1

        print(f"File tracked successfully with ID: {fileId}")

    # ========================================================
    # SINGLE FILE SAVE
    # ========================================================

    elif command == "save":

        if len(sys.argv) != 3:
            print("Usage: vv save <file-path>")
            return 1

        filePath = sys.argv[2]
        item = getItemByPath(filePath)

        if not item:
            print("Error: File is not being tracked.")
            return 1

        if item[1] != "file":
            print("Error: Path is not a tracked file.")
            return 1

        fileId = item[0]

        if saveVersion(
            REPO_PATH,
            fileId,
            filePath
        ):
            print("New version saved successfully.")
        else:
            print("Failed to save version.")

    # ========================================================
    # SINGLE FILE HISTORY
    # ========================================================

    elif command == "history":

        if len(sys.argv) != 3:
            print("Usage: vv history <file-path>")
            return 1

        filePath = sys.argv[2]
        item = getItemByPath(filePath)

        if not item:
            print("Error: File is not being tracked.")
            return 1

        if item[1] != "file":
            print("Error: Path is not a tracked file.")
            return 1

        fileId = item[0]

        history = getHistory(
            REPO_PATH,
            fileId
        )

        if not history:
            print("No version history found.")
            return 0

        print("\nVersion History")
        print("================")

        for i, commit in enumerate(history):
            print(f"{i + 1}. {commit}")

    # ========================================================
    # SINGLE FILE RESTORE
    # ========================================================

    elif command == "restore":

        if len(sys.argv) != 4:
            print(
                "Usage: vv restore "
                "<commit-hash> <file-path>"
            )
            return 1

        commitHash = sys.argv[2]
        filePath = sys.argv[3]

        if restoreVersion(
            REPO_PATH,
            commitHash,
            filePath
        ):
            print("Version restored successfully.")
        else:
            print("Failed to restore version.")

    # ========================================================
    # FOLDER TRACK
    # ========================================================

    elif command == "track-folder":

        if len(sys.argv) != 3:
            print("Usage: vv track-folder <folder-path>")
            return 1

        folderPath = sys.argv[2]
        existingItem = getItemByPath(folderPath)

        if existingItem:
            print(
                f"Error: Folder is already being tracked "
                f"with ID {existingItem[0]}."
            )
            return 1

        if not trackFolder(folderPath):
            print("FAILED: Could not track folder.")
            return 1

        folderId = generateItemId("folder")

        if not addItem(
            folderId,
            "folder",
            folderPath
        ):
            print("FAILED: Could not register folder.")
            return 1

        print(
            f"SUCCESS: Folder is now being tracked "
            f"with ID: {folderId}"
        )

    # ========================================================
    # FOLDER STATUS
    # ========================================================

    elif command == "status":

        if len(sys.argv) != 3:
            print("Usage: vv status <folder-path>")
            return 1

        folderPath = sys.argv[2]
        item = getItemByPath(folderPath)

        if not item:
            print("Error: Folder is not being tracked.")
            return 1

        if item[1] != "folder":
            print("Error: Path is not a tracked folder.")
            return 1

        if hasFolderChanged(folderPath):
            print("Changes detected.")
        else:
            print("No changes detected.")

    # ========================================================
    # FOLDER SAVE
    # ========================================================

    elif command == "save-folder":

        if len(sys.argv) != 4:
            print(
                'Usage: vv save-folder '
                '<folder-path> "<message>"'
            )
            return 1

        folderPath = sys.argv[2]
        message = sys.argv[3]

        item = getItemByPath(folderPath)

        if not item:
            print("Error: Folder is not being tracked.")
            return 1

        if item[1] != "folder":
            print("Error: Path is not a tracked folder.")
            return 1

        if saveFolderVersion(
            folderPath,
            message
        ):
            print("SUCCESS: Folder version saved.")
        else:
            print("FAILED: Could not save version.")

    # ========================================================
    # FOLDER HISTORY
    # ========================================================

    elif command == "history-folder":

        if len(sys.argv) != 3:
            print(
                "Usage: vv history-folder "
                "<folder-path>"
            )
            return 1

        folderPath = sys.argv[2]
        item = getItemByPath(folderPath)

        if not item:
            print("Error: Folder is not being tracked.")
            return 1

        if item[1] != "folder":
            print("Error: Path is not a tracked folder.")
            return 1

        history = getFolderHistory(folderPath)

        if not history:
            print("No versions found.")
            return 0

        print("\nFolder Version History")
        print("======================")

        for i, commit in enumerate(history):
            print(f"{i + 1}. {commit}")

    # ========================================================
    # FOLDER RESTORE
    # ========================================================

    elif command == "restore-folder":

        if len(sys.argv) != 4:
            print(
                "Usage: vv restore-folder "
                "<folder-path> <commit-hash>"
            )
            return 1

        folderPath = sys.argv[2]
        commitHash = sys.argv[3]

        item = getItemByPath(folderPath)

        if not item:
            print("Error: Folder is not being tracked.")
            return 1

        if item[1] != "folder":
            print("Error: Path is not a tracked folder.")
            return 1

        if restoreFolderVersion(
            folderPath,
            commitHash
        ):
            print("SUCCESS: Folder restored.")
        else:
            print("FAILED: Could not restore version.")

    # ========================================================
    # IGNORE / UNIGNORE
    # ========================================================

    elif command == "ignore":

        if len(sys.argv) not in (4, 5):
            print(
                "Usage: vv ignore <folder-path> "
                "<file-or-folder> [--remove]"
            )
            return 1

        folderPath = sys.argv[2]
        pattern = sys.argv[3]

        remove = (
            len(sys.argv) == 5
            and sys.argv[4] == "--remove"
        )

        if len(sys.argv) == 5 and not remove:
            print("Error: The only supported option is --remove.")
            return 1

        item = getItemByPath(folderPath)

        if not item:
            print("Error: Folder is not being tracked.")
            return 1

        if item[1] != "folder":
            print("Error: Path is not a tracked folder.")
            return 1

        if not updateGitIgnore(
            folderPath,
            pattern,
            remove
        ):
            return 1

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