import re # imports Python's regular expression library.
# We're using it for controlled text cleanup.

def clean_text(text):
    """
    Clean document text while preserving useful information
    for retrieval.
    """
    # Remove the optional FILE: line
    text = re.sub(r"^FILE:.*$\n", "", text, flags=re.MULTILINE)

    # Normalize windows line endings
    text = text.replace("\r\n", "\n")

    #  Replace tabs with spaces
    text = text.replace("\t", " ")

    # Remove trailing whitespace from each line
    text = "\n".join(
        line.rstrip()
        for line in text.splitlines("\n")
        )

    # Replace 3 or more consecutive blank lines
    # with a maximum of 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Remove leading and trailing whitespace from the entire text
    text = text.strip()

    return text
