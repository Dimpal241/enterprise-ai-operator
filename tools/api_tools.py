# tools/api_tools.py
from typing import Any, Dict, Optional

from tools.base import BaseTool, ToolResult


class APICallTool(BaseTool):
    name = "call_api"
    description = "Make an HTTP request to an internal or external REST API. Supports GET, POST, PUT, DELETE, and PATCH."

    def execute(
        self,
        url: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout: int = 30,
        **kwargs
    ) -> ToolResult:
        method = method.upper()
        try:
            import httpx

            with httpx.Client(timeout=timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    json=payload if method in ("POST", "PUT", "PATCH") and payload else None,
                    params=params,
                    headers=headers or {},
                )

                try:
                    body = response.json()
                except Exception:
                    body = response.text

                is_success = response.status_code < 400
                return ToolResult(
                    tool_name=self.name,
                    success=is_success,
                    output={
                        "status_code": response.status_code,
                        "body": body,
                        "headers": dict(response.headers),
                    },
                    error=None if is_success else f"HTTP {response.status_code}: {response.text[:200]}",
                )
        except ImportError:
            # Fallback to urllib.request if httpx is not yet installed
            try:
                import json
                import urllib.error
                import urllib.parse
                import urllib.request

                full_url = url
                if params:
                    full_url = f"{url}?{urllib.parse.urlencode(params)}"

                data_bytes = json.dumps(payload).encode("utf-8") if payload else None
                req_headers = headers or {}
                if payload:
                    req_headers["Content-Type"] = "application/json"

                req = urllib.request.Request(
                    full_url,
                    data=data_bytes,
                    headers=req_headers,
                    method=method,
                )

                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    resp_body = resp.read().decode("utf-8")
                    try:
                        parsed = json.loads(resp_body)
                    except Exception:
                        parsed = resp_body
                    return ToolResult(
                        tool_name=self.name,
                        success=True,
                        output={"status_code": resp.status, "body": parsed},
                    )
            except urllib.error.HTTPError as e:
                err_text = e.read().decode("utf-8")
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output={"status_code": e.code, "body": err_text},
                    error=f"HTTP {e.code}: {err_text[:200]}",
                )
            except Exception as e:
                return ToolResult(
                    tool_name=self.name,
                    success=False,
                    output={},
                    error=f"API call failed: {str(e)}",
                )
        except Exception as e:
            return ToolResult(
                tool_name=self.name,
                success=False,
                output={},
                error=f"API call failed: {str(e)}",
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
                        "url": {
                            "type": "string",
                            "description": "The full target API endpoint URL (e.g. 'http://localhost:8001/api/invoices')",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                            "default": "GET",
                            "description": "HTTP method to invoke",
                        },
                        "payload": {
                            "type": "object",
                            "description": "JSON payload body for POST/PUT requests",
                        },
                        "headers": {
                            "type": "object",
                            "description": "Custom HTTP request headers",
                        },
                        "params": {
                            "type": "object",
                            "description": "URL query parameters",
                        },
                    },
                    "required": ["url"],
                },
            },
        }
