from services.fileHierarchyService import get_folder_hierarchy

async def file_hierarchy_handler(folder_id):
    result = get_folder_hierarchy(folder_id)
    return result