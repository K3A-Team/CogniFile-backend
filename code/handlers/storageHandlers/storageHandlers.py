from Core.Shared.Database import Database

def get_shared_content_handler(searchQuery: str, userID: str):
    """
    Retrieves the shared content (files and folders) that match the search query.
    Shared content includes:
    - Files and folders where the user is the owner and there is at least one readId or writeId.
    - Files and folders where the user is included in the readId or writeId.
    """
    try:

        refs = Database.setupRefs(["files", "folders"])
        files_ref = refs["files"]
        folders_ref = refs["folders"]

        owned_shared_files_r = [doc.to_dict() for doc in files_ref.where("ownerId", "==", userID).where("readId", "!=", []).stream()]
        owned_shared_files_w = [
            doc.to_dict() for doc in files_ref.where("ownerId", "==", userID).where("writeId", "!=", []).stream()
            if doc.id not in {item['id'] for item in owned_shared_files_r}
        ]
        shared_files_r = [doc.to_dict() for doc in files_ref.where("readId", "array_contains", userID).stream()]
        shared_files_w = [
            doc.to_dict() for doc in files_ref.where("writeId", "array_contains", userID).stream()
            if doc.id not in {item['id'] for item in shared_files_r}
        ]
        
        owned_shared_folders_r = [doc.to_dict() for doc in folders_ref.where("ownerId", "==", userID).where("readId", "!=", []).stream()]
        owned_shared_folders_w = [
            doc.to_dict() for doc in folders_ref.where("ownerId", "==", userID).where("writeId", "!=", []).stream()
            if doc.id not in {item['id'] for item in owned_shared_folders_r}
        ]
        shared_folders_r = [doc.to_dict() for doc in folders_ref.where("readId", "array_contains", userID).stream()]
        shared_folders_w = [
            doc.to_dict() for doc in folders_ref.where("writeId", "array_contains", userID).stream()
            if doc.id not in {item['id'] for item in shared_folders_r}
        ]

        all_shared_files = owned_shared_files_r + owned_shared_files_w + shared_files_r + shared_files_w
        all_shared_folders = owned_shared_folders_r + owned_shared_folders_w + shared_folders_r + shared_folders_w

        if searchQuery:

            all_user_ids = set()
            for item in all_shared_files + all_shared_folders:
                all_user_ids.update(item.get('readId', []))
                all_user_ids.update(item.get('writeId', []))
                all_user_ids.add(item.get('ownerId', ''))

            user_names_map = Database.get_user_names_map(list(all_user_ids))

            searchQuery = searchQuery.lower()

            all_shared_files = [
                item for item in all_shared_files
                if (
                    searchQuery in item.get('name', '').lower() or
                    any(searchQuery in tag.lower() for tag in item.get('tags', [])) or
                    Database.matches_search_term(item, searchQuery, user_names_map, userID)
                )
            ]

            all_shared_folders = [
                item for item in all_shared_folders
                if (
                    searchQuery in item.get('name', '').lower() or
                    Database.matches_search_term(item, searchQuery, user_names_map, userID)
                )
            ]

        return {
            "files": all_shared_files,
            "folders": all_shared_folders
        }

    except Exception as e:
        raise Exception(str(e))
