"""Output formatting for agentix CLI."""

import json
import sys
from typing import Any, Dict, List, Optional, Sequence, Union

from tabulate import tabulate

from .exceptions import AgentixError


class OutputFormatter:
    """Renders data as JSON or table."""

    def __init__(self, fmt: str = "json"):
        self.fmt = fmt

    def output(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        columns: Optional[Sequence[str]] = None,
    ) -> None:
        """Print data to stdout."""
        if self.fmt == "json":
            print(json.dumps(data, indent=2, default=str))
        else:
            self._print_table(data, columns)

    def error(self, exc: AgentixError) -> None:
        """Print error to stderr (table mode) or stdout (JSON mode)."""
        if self.fmt == "json":
            print(json.dumps(exc.to_dict(), indent=2, default=str))
        else:
            print(f"Error: {exc}", file=sys.stderr)
            if exc.details:
                for k, v in exc.details.items():
                    print(f"  {k}: {v}", file=sys.stderr)

    def success(self, message: str, data: Optional[Dict[str, Any]] = None) -> None:
        """Print a success message."""
        if self.fmt == "json":
            result: Dict[str, Any] = {"success": True, "message": message}
            if data:
                result["data"] = data
            print(json.dumps(result, indent=2, default=str))
        else:
            print(message)

    def _print_table(
        self,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        columns: Optional[Sequence[str]] = None,
    ) -> None:
        if isinstance(data, dict):
            # Single item: key-value pairs
            rows = [[k, v] for k, v in data.items()]
            print(tabulate(rows, headers=["Field", "Value"], tablefmt="simple"))
        elif isinstance(data, list) and data:
            headers = list(columns) if columns else list(data[0].keys())
            rows = [[item.get(h, "") for h in headers] for item in data]
            print(tabulate(rows, headers=headers, tablefmt="simple"))
        else:
            print("No results.")
