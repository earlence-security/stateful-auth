fn joplin_access_only_created(request, history) {
    // List of APIs that create a file or folder.
    let create_apis = vec!["/api/files/create_folder_v2", "/api/files/upload"];
    // Check access to existing files and folders.
    if request.path.starts_with("/api/files") && !create_apis.contains(&request.path) {
        for entry in history {
            if create_apis.contains(&entry.api) {
                // Accept if there is a history of creation
                return "Accept"
            }
        }
        // Deny if no history of creation
        return "Deny"
    } else {
        // Accept for the rest of APIs
        return "Accept"
    }
}