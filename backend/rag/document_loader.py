from pathlib import Path #pathlib gives us a clean way to work with folders and files across operating systems.


def load_documents(knowledge_base_path):
    """
    Load documents from a specified directory.

    Args:
        knowledge_base_path (str): The path to the directory containing documents.
    """

    documents = [] # Initialize an empty list to store the loaded documents.

    knowledge_base = Path(knowledge_base_path)

    for file_path in knowledge_base.rglob("*.md"): # rglob is a method that recursively searches for files matching the given pattern (in this case, all markdown files) in the specified directory and its subdirectories.
        with open(file_path, "r", encoding="utf-8") as file: # Open the file in read mode with UTF-8 encoding to handle various characters correctly.
            content = file.read()
            
        documents.append({
            "content": content,
            "source": str(file_path.relative_to(knowledge_base))
        })

    return documents