from Core.Shared.Database import Database , db



def get_folder_hierarchy(folder_id):
    folder_ref = db.collection('folders').document(folder_id)
    folder_doc = folder_ref.get()
    
    if not folder_doc.exists:
        return None
    
    folder_data = folder_doc.to_dict()
    hierarchy = {
        'type': 'folder',
        'id': folder_id,
        'name': folder_data.get('name', ''),
        'children': [],
        'files': []
    }
    
    # Get files
    if 'files' in folder_data:
        file_refs = [db.collection('files').document(file_id) for file_id in folder_data['files']]
        file_docs = db.get_all(file_refs)
        for file_doc in file_docs:
            if file_doc.exists:
                file_data = file_doc.to_dict()
                hierarchy['files'].append({
                    'type': 'file',
                    'id': file_doc.id,
                    'name': file_data.get('name', '')
                })
    
    # Recursively get subfolders
    if 'subFolders' in folder_data:
        for subfolder_id in folder_data['subFolders']:
            subfolder = get_folder_hierarchy( subfolder_id)
            if subfolder:
                hierarchy['children'].append(subfolder)
    
    return hierarchy