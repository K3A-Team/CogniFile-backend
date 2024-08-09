from services.fileHierarchyService import optimize_hierarchy

async def file_hierarchy_handler(folder_id):
    result = optimize_hierarchy(folder_id)
    return result