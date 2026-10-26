
    // MARK: - Tracking Status

    private func trackingStatus(for url: URL) -> Bool? {
        guard let container = appGroupContainer() else {
            NSLog("VV_TRACKED: App Group unavailable")
            return nil
        }

        let requestURL = container.appendingPathComponent("tracked_request.txt")
        let responseURL = container.appendingPathComponent("tracked_response.txt")

        try? FileManager.default.removeItem(at: responseURL)

        do {
            try url.path.write(
                to: requestURL,
                atomically: true,
                encoding: .utf8
            )
        } catch {
            NSLog(
                "VV_TRACKED: Request write failed: %@",
                error.localizedDescription
            )
            return nil
        }

        let deadline = Date().addingTimeInterval(1.5)

        while Date() < deadline {
            if let response = try? String(
                contentsOf: responseURL,
                encoding: .utf8
            ) {
                try? FileManager.default.removeItem(at: responseURL)

                let lines = response.components(separatedBy: .newlines)

                guard lines.count >= 2, lines[0] == url.path else {
                    NSLog("VV_TRACKED: Invalid response for %@", url.path)
                    return nil
                }

                switch lines[1].trimmingCharacters(
                    in: .whitespacesAndNewlines
                ) {
                case "tracked":
                    return true
                case "untracked":
                    return false
                default:
                    NSLog("VV_TRACKED: Unexpected response: %@", response)
                    return nil
                }
            }

            Thread.sleep(forTimeInterval: 0.02)
        }

        NSLog("VV_TRACKED: Request timed out for %@", url.path)
        return nil
    }
