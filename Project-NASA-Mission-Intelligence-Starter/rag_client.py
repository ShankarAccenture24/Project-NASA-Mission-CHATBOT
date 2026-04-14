try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

from typing import Dict, List, Optional
from pathlib import Path

def discover_chroma_backends() -> Dict[str, Dict[str, str]]:
    """Discover available ChromaDB backends in the project directory"""
    backends = {}
    current_dir = Path(".")

    # Look for ChromaDB directories
    chroma_dirs = []
    for dir_path in current_dir.rglob("*"):
        if dir_path.is_dir() and "chroma" in dir_path.name.lower():
            chroma_dirs.append(dir_path)

    # Loop through each discovered directory
    for chroma_dir in chroma_dirs:
        try:
            # Initialize database client with directory path and configuration settings
            client = chromadb.PersistentClient(path=str(chroma_dir))

            # Retrieve list of available collections from the database
            collections = client.list_collections()

            # Loop through each collection found
            for collection in collections:
                # Create unique identifier key combining directory and collection names
                key = f"{chroma_dir.name}_{collection.name}"

                # Build information dictionary containing:
                # Store directory path as string
                # Store collection name
                # Create user-friendly display name
                # Get document count with fallback for unsupported operations
                try:
                    doc_count = collection.count()
                except:
                    doc_count = "Unknown"

                backends[key] = {
                    "directory": str(chroma_dir),
                    "collection_name": collection.name,
                    "display_name": f"{chroma_dir.name} - {collection.name} ({doc_count} docs)"
                }

        except Exception as e:
            # Handle connection or access errors gracefully
            # Create fallback entry for inaccessible directories
            # Include error information in display name with truncation
            key = f"{chroma_dir.name}_error"
            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
            backends[key] = {
                "directory": str(chroma_dir),
                "collection_name": "error",
                "display_name": f"{chroma_dir.name} - Error: {error_msg}"
            }

    # Return complete backends dictionary with all discovered collections
    return backends

def initialize_rag_system(chroma_dir: str, collection_name: str):
    """Initialize the RAG system with specified backend"""

    if not CHROMADB_AVAILABLE:
        return None, False, "ChromaDB not available"

    try:
        # For batch evaluation, use in-memory client to avoid persistence issues
        if "batch" in collection_name.lower():
            client = chromadb.Client()
        else:
            # Create a chromadb persistent client
            client = chromadb.PersistentClient(path=chroma_dir)

        # Return the collection with the collection_name
        collection = client.get_collection(name=collection_name)

        return collection, True, "Successfully initialized RAG system"
    except Exception as e:
        return None, False, f"Failed to initialize RAG system: {str(e)}"

def retrieve_documents(collection, query: str, n_results: int = 3,
                      mission_filter: Optional[str] = None) -> Optional[Dict]:
    """Retrieve relevant documents from ChromaDB with optional filtering"""

    try:
        # Initialize filter variable to None (represents no filtering)
        where_clause = None

        # Check if filter parameter exists and is not set to "all" or equivalent
        # If filter conditions are met, create filter dictionary with appropriate field-value pairs
        if mission_filter and mission_filter.lower() != "all":
            where_clause = {"mission": mission_filter}

        # Execute database query with the following parameters:
        # Pass search query in the required format
        # Set maximum number of results to return
        # Apply conditional filter (None for no filtering, dictionary for specific filtering)
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where=where_clause
        )

        return results

    except Exception as e:
        print(f"Error retrieving documents: {e}")
        return None

def format_context(documents: List[str], metadatas: List[Dict]) -> str:
    """Format retrieved documents into context"""
    if not documents:
        return ""

    # Initialize list with header text for context section
    context_parts = ["=== Retrieved Context ===\n"]

    # Loop through paired documents and their metadata using enumeration
    for i, (doc, metadata) in enumerate(zip(documents, metadatas)):
        # Extract mission information from metadata with fallback value
        mission = metadata.get('mission', 'Unknown Mission')
        # Clean up mission name formatting (replace underscores, capitalize)
        mission = mission.replace('_', ' ').title()

        # Extract source information from metadata with fallback value
        source = metadata.get('source', 'Unknown Source')

        # Extract category information from metadata with fallback value
        category = metadata.get('document_category', 'Unknown Category')
        # Clean up category name formatting (replace underscores, capitalize)
        category = category.replace('_', ' ').title()

        # Create formatted source header with index number and extracted information
        source_header = f"[{i+1}] {mission} - {category} ({source})"
        context_parts.append(source_header)
        context_parts.append("-" * len(source_header))

        # Check document length and truncate if necessary
        max_length = 1000
        if len(doc) > max_length:
            truncated_doc = doc[:max_length] + "..."
            # Add truncated or full document content to context parts list
            context_parts.append(truncated_doc)
        else:
            context_parts.append(doc)

        context_parts.append("")  # Add blank line between documents

    # Join all context parts with newlines and return formatted string
    return "\n".join(context_parts)