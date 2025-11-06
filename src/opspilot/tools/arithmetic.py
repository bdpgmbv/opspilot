import ast
import operator

from pydantic import BaseModel, ConfigDict, Field

from opspilot.tools.base import ToolError, tool

DESCRIPTION = (
    "Evaluate an arithmetic expression and return the result. "
    "Supports + - * / ** and parentheses. Numbers only, no variables. "
    'Example: calculator(expression="(2400 * 18.5) / 100")'
)


class CalculatorInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expression: str = Field(
        min_length=1,
        max_length=200,
        description="Arithmetic expression, e.g. '(2400 * 18.5) / 100'",
    )


_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
}


def _walk(node):
    """Allow numbers and math. Reject everything else."""
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _walk(node.left), _walk(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 100:
            raise ToolError("exponent too large, keep it under 100")
        if isinstance(node.op, ast.Div) and right == 0:
            raise ToolError("division by zero")
        return _OPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -_walk(node.operand)

    raise ToolError(f"only plain arithmetic is allowed, got: {type(node).__name__}")


@tool("calculator", DESCRIPTION, CalculatorInput)
def calculator(expression: str) -> str:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as e:
        raise ToolError(f"could not parse {expression!r}: {e.msg}") from e
    return str(_walk(tree.body))
