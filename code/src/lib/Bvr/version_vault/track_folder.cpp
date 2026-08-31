#include <cstdlib>
#include <cstdio>
#include <string>
#include <vector>
#include <filesystem>
#include <iostream>

using namespace std;
namespace fs = std::filesystem;


// ============================================================
// Command Helpers
// ============================================================

string runCommand(const string& command) {
    FILE* pipe = popen(command.c_str(), "r");

    if (!pipe)
        return "";

    char buffer[256];
    string result;

    while (fgets(buffer, sizeof(buffer), pipe)) {
        result += buffer;
    }

    pclose(pipe);

    if (!result.empty() && result.back() == '\n')
        result.pop_back();

    return result;
}


bool executeCommand(const string& command) {
    return system(command.c_str()) == 0;
}


// ============================================================
// Folder Tracking
// ============================================================

// Initialize the folder as a Git repository
bool trackFolder(const string& folderPath) {

    if (!fs::exists(folderPath)) {
        cerr << "Error: Folder does not exist.\n";
        return false;
    }

    if (!fs::is_directory(folderPath)) {
        cerr << "Error: Path is not a directory.\n";
        return false;
    }

    // Check if already a Git repository
    if (fs::exists(fs::path(folderPath) / ".git")) {
        cout << "Folder is already being tracked.\n";
        return true;
    }

    string command =
        "git init \"" + folderPath + "\"";

    return executeCommand(command);
}


// ============================================================
// Save Folder Version
// ============================================================

bool saveFolderVersion(
    const string& folderPath,
    const string& message = "New folder version"
) {

    if (!fs::exists(fs::path(folderPath) / ".git")) {
        cerr << "Error: Folder is not a VersionVault repository.\n";
        return false;
    }

    string command =
        "cd \"" + folderPath + "\" && "
        "git add . && "
        "git commit -m \"" + message + "\"";

    return executeCommand(command);
}


// ============================================================
// Get Folder History
// ============================================================

vector<string> getFolderHistory(
    const string& folderPath
) {

    vector<string> history;

    if (!fs::exists(fs::path(folderPath) / ".git")) {
        cerr << "Error: Folder is not a Git repository.\n";
        return history;
    }

    string command =
        "cd \"" + folderPath + "\" && "
        "git log --format=%H";

    FILE* pipe = popen(command.c_str(), "r");

    if (!pipe)
        return history;

    char buffer[256];

    while (fgets(buffer, sizeof(buffer), pipe)) {

        string commit = buffer;

        if (!commit.empty() && commit.back() == '\n')
            commit.pop_back();

        history.push_back(commit);
    }

    pclose(pipe);

    return history;
}


// ============================================================
// Restore Folder Version
// ============================================================

bool restoreFolderVersion(
    const string& folderPath,
    const string& commitHash
) {

    if (!fs::exists(fs::path(folderPath) / ".git")) {
        cerr << "Error: Folder is not a Git repository.\n";
        return false;
    }

    // Restore all tracked files to the selected commit
    string command =
        "cd \"" + folderPath + "\" && "
        "git checkout " + commitHash + " -- .";

    return executeCommand(command);
}


// ============================================================
// Check Folder Status
// ============================================================

bool hasFolderChanged(
    const string& folderPath
) {

    string command =
        "cd \"" + folderPath + "\" && "
        "git status --porcelain";

    string result = runCommand(command);

    return !result.empty();
}


// ============================================================
// Simple Test
// ============================================================

#ifdef FOLDER_TRACKER_TEST

int main() {

    const string folder =
        "/Users/tanaysingh/Desktop/test_folder";

    cout << "\n=== VersionVault Folder Tracker Test ===\n\n";


    // Track folder
    cout << "Initializing folder...\n";

    if (trackFolder(folder))
        cout << "SUCCESS: Folder initialized as repository.\n";
    else
        cout << "FAILED: Could not initialize folder.\n";


    // Check changes
    cout << "\nChecking folder status...\n";

    if (hasFolderChanged(folder))
        cout << "Changes detected.\n";
    else
        cout << "No changes detected.\n";


    // Save version
    cout << "\nSaving folder version...\n";

    if (saveFolderVersion(folder, "Initial Version"))
        cout << "SUCCESS: Version saved.\n";
    else
        cout << "FAILED: Could not save version.\n";


    // Get history
    cout << "\nFolder History:\n";

    vector<string> history =
        getFolderHistory(folder);

    for (int i = 0; i < history.size(); i++) {
        cout << i + 1 << ". "
             << history[i] << "\n";
    }


    cout << "\n=== Test Complete ===\n";

    return 0;
}

#endif