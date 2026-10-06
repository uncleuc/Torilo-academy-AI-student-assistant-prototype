import re # imports Python's regular expression library.


def extract_metadata(text, source):
    """
    Extract document metadata from the Document Information section.
    """

    metadata = {
        "source": source
    }

    fields = {
        "document_id": "document_id",
        "document_type": "document_type",
        "source_type": "source_type",
        "organization": "organization",
        "source": "original_source",
        "last_verified": "last_verified",
        "status": "status"
    }

    for field_name, metadata_key in fields.items():

        pattern = rf"- {field_name.replace('_', ' ')}:\s*(.+)"

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE
        )

        if match:
            metadata[metadata_key] = match.group(1).strip()

    return metadata