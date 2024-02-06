fn joplin_access_only_created(request, history) {
    // List of APIs that create a file or folder.
    let create_apis = vec!["/api/files/create_folder_v2", "/api/files/upload"];
    // Check access to /api/files scope.
    if request.path.starts_with("/api/files") {
        // Check access to existing files and folders.
        if !create_apis.contains(&request.path) {
            for entry in history {
                if create_apis.contains(&entry.api) {
                    // Accept if there is a history of creation.
                    println!("Accept");
                }
            }
            // Deny if no history of creation
            println!("Deny");
        } else {
            // Accept for APIs that create a file or folder.
            println!("Accept");
        }
    } else {
        // Deny API calls outside of /api/files scope.
        println!("Deny");
    }
}