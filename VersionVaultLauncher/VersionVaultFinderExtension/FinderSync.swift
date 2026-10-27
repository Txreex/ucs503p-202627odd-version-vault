import Cocoa
import FinderSync

class FinderSync: FIFinderSync {
    
    private let appGroup = "group.com.ridham.versionvault.shared"
    
    override init() {
        super.init()
        if let myFolderURL = URL(string: "file:///Users/") {
            FIFinderSyncController.default().directoryURLs = [myFolderURL]
        }
    }
    
    // MARK: - Menu Setup
    
    override func menu(for menuKind: FIMenuKind) -> NSMenu {
        let rootMenu = NSMenu(title: "")
        
        // FIX: Check selected item FIRST, fallback to targeted folder (background click)
        guard let url = FIFinderSyncController.default().selectedItemURLs()?.first ??
                        FIFinderSyncController.default().targetedURL() else {
            return rootMenu
        }
        
        let vaultItem = NSMenuItem(title: "VersionVault", action: nil, keyEquivalent: "")
        let vaultSubmenu = NSMenu(title: "")
        vaultItem.submenu = vaultSubmenu
        rootMenu.addItem(vaultItem)
        
        let isDirectory = (try? url.resourceValues(forKeys: [.isDirectoryKey]).isDirectory) ?? false
        let trackedStatus = trackingStatus(for: url)
        
        if trackedStatus != true {
            if isDirectory {
                let item = NSMenuItem(title: "Track Folder", action: #selector(trackFolderAction(_:)), keyEquivalent: "")
                item.target = self
                vaultSubmenu.addItem(item)
            } else {
                let item = NSMenuItem(title: "Track", action: #selector(trackAction(_:)), keyEquivalent: "")
                item.target = self
                vaultSubmenu.addItem(item)
            }
        } else {
            if isDirectory {
                let item = NSMenuItem(title: "Folder History", action: #selector(historyFolderAction(_:)), keyEquivalent: "")
                item.target = self
                vaultSubmenu.addItem(item)
            } else {
                let item = NSMenuItem(title: "File History", action: #selector(historyAction(_:)), keyEquivalent: "")
                item.target = self
                vaultSubmenu.addItem(item)
            }
        }
        
        return rootMenu
    }
    
    // MARK: - Actions
    
    @IBAction func trackAction(_ sender: AnyObject?) {
        sendPendingRequest(command: "track")
    }
    
    @IBAction func trackFolderAction(_ sender: AnyObject?) {
        sendPendingRequest(command: "track-folder")
    }
    
    @IBAction func historyAction(_ sender: AnyObject?) {
        sendHistoryRequest(command: "history")
    }
    
    @IBAction func historyFolderAction(_ sender: AnyObject?) {
        sendHistoryRequest(command: "history-folder")
    }
    
    // MARK: - App Group Request Helpers
    
    private func appGroupContainer() -> URL? {
        return FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroup)
    }
    
    private func sendPendingRequest(command: String) {
        // FIX: Prioritize selected item here as well
        guard let url = FIFinderSyncController.default().selectedItemURLs()?.first ??
                        FIFinderSyncController.default().targetedURL(),
              let container = appGroupContainer() else { return }
        
        let requestURL = container.appendingPathComponent("pending_request.txt")
        let content = "\(command)\n\(url.path)\n"
        try? content.write(to: requestURL, atomically: true, encoding: .utf8)
    }
    
    private func sendHistoryRequest(command: String) {
        // FIX: Prioritize selected item here as well
        guard let url = FIFinderSyncController.default().selectedItemURLs()?.first ??
                        FIFinderSyncController.default().targetedURL(),
              let container = appGroupContainer() else { return }
        
        let requestURL = container.appendingPathComponent("history_request.txt")
        let content = "\(command)\n\(url.path)\n"
        try? content.write(to: requestURL, atomically: true, encoding: .utf8)
    }
    
    // MARK: - Tracking Status Check
    
    private func trackingStatus(for url: URL) -> Bool? {
        guard let container = appGroupContainer() else {
            NSLog("VV_TRACKED: App Group unavailable")
            return nil
        }

        let requestURL = container.appendingPathComponent("tracked_request.txt")
        let responseURL = container.appendingPathComponent("tracked_response.txt")

        try? FileManager.default.removeItem(at: responseURL)

        do {
            try url.path.write(to: requestURL, atomically: true, encoding: .utf8)
        } catch {
            return nil
        }

        let deadline = Date().addingTimeInterval(1.5)

        while Date() < deadline {
            if let response = try? String(contentsOf: responseURL, encoding: .utf8) {
                try? FileManager.default.removeItem(at: responseURL)

                let lines = response.components(separatedBy: .newlines)
                guard lines.count >= 2, lines[0] == url.path else { return nil }

                switch lines[1].trimmingCharacters(in: .whitespacesAndNewlines) {
                case "tracked": return true
                case "untracked": return false
                default: return nil
                }
            }
            Thread.sleep(forTimeInterval: 0.02)
        }
        return nil
    }
}
