# memory/company_kb.py
"""Company Knowledge Base & Policy Memory via ChromaDB.

Provides semantic search over corporate SOPs, spending thresholds,
vendor catalogs, and operational permissions.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from tools.base import BaseTool, ToolResult

KB_DIR = "./corporate_memory"
COLLECTION_NAME = "company_knowledge"


def get_chroma_client() -> chromadb.PersistentClient:
    """Return persistent ChromaDB client pointing to KB directory."""
    Path(KB_DIR).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=KB_DIR)


def index_company_documents(docs_dir: str = "memory/knowledge_base") -> int:
    """Index all company SOPs, markdown policies, and JSON reference catalogs into ChromaDB."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    base_path = Path(docs_dir)
    if not base_path.exists():
        print(f"Knowledge base directory '{docs_dir}' does not exist.")
        return 0

    documents: List[str] = []
    ids: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    # 1. Index Markdown SOPs
    for doc_path in base_path.rglob("*.md"):
        try:
            content = doc_path.read_text(encoding="utf-8")
            doc_id = f"sop_{doc_path.stem}"
            documents.append(content)
            ids.append(doc_id)
            metadatas.append({"source": str(doc_path), "type": "sop", "title": doc_path.stem})
        except Exception as e:
            print(f"Failed to read {doc_path}: {e}")

    # 2. Index JSON catalogs & permissions
    for json_path in base_path.rglob("*.json"):
        try:
            content = json_path.read_text(encoding="utf-8")
            doc_id = f"json_{json_path.stem}"
            documents.append(content)
            ids.append(doc_id)
            metadatas.append({"source": str(json_path), "type": "reference", "title": json_path.stem})
        except Exception as e:
            print(f"Failed to read {json_path}: {e}")

    if documents:
        collection.upsert(
            documents=documents,
            ids=ids,
            metadatas=metadatas,
        )

    count = len(documents)
    print(f"Successfully indexed {count} company documents into ChromaDB collection '{COLLECTION_NAME}'.")
    return count


def query_company_policy(question: str, n_results: int = 3) -> str:
    """Query company policies for relevant operational guidance."""
    client = get_chroma_client()
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    count = collection.count()
    if count == 0:
        index_company_documents()

    n = min(n_results, max(1, collection.count()))
    results = collection.query(query_texts=[question], n_results=n)
    docs = results.get("documents", [[]])[0]
    return "\n\n---\n\n".join(docs) if docs else "No relevant company policy found."


class PolicyQueryTool(BaseTool):
    """Tool allowing AI Operator to look up company SOPs, limits, and rules."""

    name = "query_company_policy"
    description = (
        "Look up company SOPs, spending approval thresholds, vendor policies, "
        "and operational permissions before executing actions."
    )

    def execute(self, question: str, **kwargs) -> ToolResult:
        try:
            context = query_company_policy(question)
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=context,
            )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Policy query failed: {str(e)}",
            )

    def schema(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "question": {
                            "type": "string",
                            "description": "Question about company policy, approval thresholds, or vendor rules (e.g. 'What is the approval threshold for invoices?')",
                        }
                    },
                    "required": ["question"],
                },
            },
        }
