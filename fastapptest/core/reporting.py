# core/reporting.py

import json
import html
from pathlib import Path
from typing import Any, Dict


class Reporting:
    """
    Utility class for persisting API test results.
    Fully backward compatible with existing modules.
    """

    @staticmethod
    def save_json(results: Dict[str, Any], file_path: Path) -> None:
        """
        Save results as formatted JSON.
        """
        file_path.write_text(
            json.dumps(results, indent=4, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def save_html(results: Dict[str, Any], file_path: Path) -> None:
        """
        Save results as a simple, human-readable HTML report.
        """

        def escape(value: Any) -> str:
            """Safely escape content for HTML rendering."""
            try:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2, ensure_ascii=False)
                return html.escape(str(value))
            except Exception:
                return html.escape(repr(value))

        html_content = [
            "<html>",
            "<head>",
            "<meta charset='utf-8'/>",
            "<title>API Test Report</title>",
            "<style>",
            "body { font-family: Arial, sans-serif; }",
            "table { border-collapse: collapse; width: 100%; }",
            "th, td { border: 1px solid #ccc; padding: 8px; vertical-align: top; }",
            "th { background-color: #f2f2f2; }",
            ".success { color: green; font-weight: bold; }",
            ".error { color: red; font-weight: bold; }",
            "pre { white-space: pre-wrap; word-wrap: break-word; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>API Test Report</h1>",
            "<table>",
            "<tr>",
            "<th>Endpoint</th>",
            "<th>Method</th>",
            "<th>Status</th>",
            "<th>Request Body</th>",
            "<th>Response</th>",
            "</tr>",
        ]

        for endpoint, data in results.items():
            method = data.get("method", "N/A")
            status_code = data.get("status_code")
            response = data.get("response")
            body = data.get("body")

            status_class = "success" if isinstance(status_code, int) and status_code < 400 else "error"
            status_display = status_code if status_code is not None else "ERROR"

            html_content.extend([
                "<tr>",
                f"<td>{escape(endpoint)}</td>",
                f"<td>{escape(method)}</td>",
                f"<td class='{status_class}'>{escape(status_display)}</td>",
                f"<td><pre>{escape(body)}</pre></td>",
                f"<td><pre>{escape(response)}</pre></td>",
                "</tr>",
            ])

        html_content.extend([
            "</table>",
            "</body>",
            "</html>",
        ])

        file_path.write_text("\n".join(html_content), encoding="utf-8")
