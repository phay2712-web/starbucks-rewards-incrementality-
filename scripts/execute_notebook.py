"""Execute the case-study notebook in place without requiring Jupyter.

The notebook only contains Python and text outputs, so a small in-process
runner keeps the repository reproducible in constrained CI environments where
starting a ZeroMQ-backed Jupyter kernel is not permitted.
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import os
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK = ROOT / "notebooks" / "01_experiment_design.ipynb"


def execute_cell(source: str, namespace: dict[str, object]) -> tuple[str, str, object | None]:
    """Execute a cell and return captured stdout, stderr and its final value."""

    module = ast.parse(source, filename=str(NOTEBOOK))
    final_expression = None
    if module.body and isinstance(module.body[-1], ast.Expr):
        final_expression = ast.Expression(module.body.pop().value)

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        if module.body:
            exec(compile(module, str(NOTEBOOK), "exec"), namespace)
        value = (
            eval(compile(final_expression, str(NOTEBOOK), "eval"), namespace)
            if final_expression is not None
            else None
        )
    return stdout.getvalue(), stderr.getvalue(), value


def main() -> None:
    notebook = json.loads(NOTEBOOK.read_text(encoding="utf-8"))
    namespace: dict[str, object] = {"__name__": "__main__"}
    execution_count = 0
    original_cwd = Path.cwd()

    try:
        os.chdir(NOTEBOOK.parent)
        for cell in notebook["cells"]:
            if cell.get("cell_type") != "code":
                continue

            execution_count += 1
            cell["execution_count"] = execution_count
            cell["outputs"] = []
            source = "".join(cell.get("source", []))

            try:
                stdout, stderr, value = execute_cell(source, namespace)
            except Exception as exc:
                cell["outputs"].append(
                    {
                        "output_type": "error",
                        "ename": type(exc).__name__,
                        "evalue": str(exc),
                        "traceback": traceback.format_exc().splitlines(),
                    }
                )
                raise

            if stdout:
                cell["outputs"].append(
                    {"name": "stdout", "output_type": "stream", "text": stdout.splitlines(True)}
                )
            if stderr:
                cell["outputs"].append(
                    {"name": "stderr", "output_type": "stream", "text": stderr.splitlines(True)}
                )
            if value is not None:
                cell["outputs"].append(
                    {
                        "data": {"text/plain": repr(value).splitlines(True)},
                        "execution_count": execution_count,
                        "metadata": {},
                        "output_type": "execute_result",
                    }
                )
    finally:
        os.chdir(original_cwd)

    NOTEBOOK.write_text(json.dumps(notebook, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(NOTEBOOK)


if __name__ == "__main__":
    main()
