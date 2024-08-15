from services.fileHierarchyService import optimize_hierarchy,get_folder_hierarchy,update_folder_structure
from Core.Shared.Database import Database
from Models.Entities.Folder import Folder
import uuid
from Core.Shared.Database import db

async def file_hierarchy_handler(folder_id, userId):
    folder = await Database.read("folders", folder_id)
    if folder is None:
        raise Exception("Folder not found")
    if folder["ownerId"] != userId:
        raise Exception("You are not the owner of this folder")
    
    ai_structure = optimize_hierarchy(folder_id=folder_id)
    initial_structure = get_folder_hierarchy(folder_id, displayFileId=True)

    
    # Delete all already existing user transactions
    userTransactions = db.collection('transactions').where('concernedUser', '==', userId)

    userTransactions = userTransactions.stream()
    userTransactions = [doc.to_dict() for doc in userTransactions]

    for transaction in userTransactions:
        await Database.delete("transactions", transaction["id"])
    
    transactionId = str(uuid.uuid4())
    transObj =  {
        "id": transactionId,
        "ai_structure": ai_structure,
        "initial_structure": initial_structure,
        "concernedUser": userId,
        "folderId": folder_id
    }

    transaction = await Database.store("transactions", transactionId,transObj)




    
    return transObj


async def confirm_hierarchy_suggestions(transactionId , userId):
    transactionRecord = await Database.read("transactions",transactionId)

    if transactionRecord is None:
        raise Exception("Transaction not found or expired")
    if transactionRecord["concernedUser"] != userId:
        raise Exception("You are not the owner of this transaction")
    ai_structure = transactionRecord["ai_structure"]
    initial_structure = transactionRecord["initial_structure"]
    folderId = transactionRecord["folderId"]
    rootFolder = Folder.loadWithId(folderId)

    #transaction = db.transaction()
    update_folder_structure( rootFolder,ai_structure=ai_structure, initial_structure=initial_structure)

    await Database.delete("transactions",transactionId)

    hierarchy = get_folder_hierarchy(folderId)



    return hierarchy