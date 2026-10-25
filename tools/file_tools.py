# tools/file_tools.py
from pathlib import Path
from typing import Any, Dict, Optional

from tools.base import BaseTool, ToolResult


class ReadPDFTool(BaseTool):
    name = "read_pdf"
    description = "Extract text and structured data from a PDF file. Use for invoices, reports, or any PDF document."

    def execute(self, filepath: str, **kwargs) -> ToolResult:
        path = Path(filepath)
        if not path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"File not found: '{filepath}'",
            )

        try:
            import pdfplumber

            with pdfplumber.open(str(path)) as pdf:
                extracted_pages = []
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    extracted_pages.append(f"--- Page {i + 1} ---\n{text}")

                full_text = "\n\n".join(extracted_pages).strip()

            return ToolResult(
                tool_name=self.name,
                success=True,
                output=full_text,
            )
        except ImportError:
            # Fallback if pdfplumber is not yet installed: attempt basic text read or pymupdf
            try:
                import fitz  # pymupdf (pre-installed)
                doc = fitz.open(str(path))
                text = "\n\n".join(
                    f"--- Page {i + 1} ---\n{page.get_text()}"
                    for i, page in enumerate(doc)
                )
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=text.strip(),
                )
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output="",
                    error=f"Failed to read PDF with pdfplumber/pymupdf: {str(e)}",
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output="",
                error=f"Error reading PDF file '{filepath}': {str(e)}",
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
                        "filepath": {
                            "type": "string",
                            "description": "Path to the PDF file to read (e.g. 'mock_enterprise/data/invoice_acme_corp.pdf')",
                        }
                    },
                    "required": ["filepath"],
                },
            },
        }


class ReadCSVTool(BaseTool):
    name = "read_csv"
    description = "Read a CSV or Excel file and return structured table records."

    def execute(self, filepath: str, **kwargs) -> ToolResult:
        path = Path(filepath)
        if not path.exists():
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=[],
                error=f"File not found: '{filepath}'",
            )

        try:
            import pandas as pd

            if path.suffix.lower() in [".xls", ".xlsx"]:
                df = pd.read_excel(str(path))
            else:
                df = pd.read_csv(str(path))

            records = df.to_dict(orient="records")
            return ToolResult(
                tool_name=self.name,
                success=True,
                output=records,
            )
        except ImportError:
            # Fallback to standard library csv module
            try:
                import csv
                with open(str(path), mode="r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    records = list(reader)
                return ToolResult(
                    tool_name=self.name,
                    success=True,
                    output=records,
                )
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output=[],
                    error=f"Failed to read CSV file: {str(e)}",
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output=[],
                error=f"Error reading tabular file '{filepath}': {str(e)}",
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
                        "filepath": {
                            "type": "string",
                            "description": "Path to the CSV or Excel file to read",
                        }
                    },
                    "required": ["filepath"],
                },
            },
        }
