# F:\Kernschmied\backend\tools\calculator\implementation.py

from __future__ import annotations

import ast
from collections.abc import Callable
from typing import Final, TypeAlias

from app.contracts.tool import BaseTool


Number: TypeAlias = int | float
BinaryOperation: TypeAlias = Callable[[Number, Number], Number]
UnaryOperation: TypeAlias = Callable[[Number], Number]


MAX_EXPRESSION_LENGTH: Final[int] = 1_000
MAX_AST_DEPTH: Final[int] = 50
MAX_ABSOLUTE_RESULT: Final[float] = 1e100


def _add(
    left: Number,
    right: Number,
) -> Number:
    return left + right


def _subtract(
    left: Number,
    right: Number,
) -> Number:
    return left - right


def _multiply(
    left: Number,
    right: Number,
) -> Number:
    return left * right


def _divide(
    left: Number,
    right: Number,
) -> Number:
    if right == 0:
        raise ValueError(
            "Division durch null ist nicht erlaubt.",
        )

    return left / right


def _negate(
    value: Number,
) -> Number:
    return -value


BINARY_OPERATIONS: Final[
    dict[type[ast.operator], BinaryOperation]
] = {
    ast.Add: _add,
    ast.Sub: _subtract,
    ast.Mult: _multiply,
    ast.Div: _divide,
}


UNARY_OPERATIONS: Final[
    dict[type[ast.unaryop], UnaryOperation]
] = {
    ast.USub: _negate,
}


def evaluate(
    node: ast.AST,
    *,
    depth: int = 0,
) -> Number:
    """
    Wertet ausschließlich freigegebene mathematische AST-Knoten aus.

    Erlaubt sind:

    - ganze Zahlen,
    - Fließkommazahlen,
    - Addition,
    - Subtraktion,
    - Multiplikation,
    - Division,
    - negatives Vorzeichen.
    """

    if depth > MAX_AST_DEPTH:
        raise ValueError(
            "Der mathematische Ausdruck ist zu tief verschachtelt.",
        )

    if isinstance(
        node,
        ast.Constant,
    ):
        value = node.value

        # bool ist eine Unterklasse von int und muss deshalb vorher
        # ausdrücklich ausgeschlossen werden.
        if isinstance(
            value,
            bool,
        ):
            raise ValueError(
                "Boolesche Werte sind nicht erlaubt.",
            )

        if isinstance(
            value,
            int | float,
        ):
            return value

        raise ValueError(
            "Nur Zahlen sind als Konstanten erlaubt.",
        )

    if isinstance(
        node,
        ast.BinOp,
    ):
        operation = BINARY_OPERATIONS.get(
            type(node.op),
        )

        if operation is None:
            raise ValueError(
                f"Der Operator "
                f"'{type(node.op).__name__}' "
                "ist nicht erlaubt.",
            )

        left = evaluate(
            node.left,
            depth=depth + 1,
        )

        right = evaluate(
            node.right,
            depth=depth + 1,
        )

        result = operation(
            left,
            right,
        )

        _validate_result(
            result,
        )

        return result

    if isinstance(
        node,
        ast.UnaryOp,
    ):
        operation = UNARY_OPERATIONS.get(
            type(node.op),
        )

        if operation is None:
            raise ValueError(
                f"Der unäre Operator "
                f"'{type(node.op).__name__}' "
                "ist nicht erlaubt.",
            )

        operand = evaluate(
            node.operand,
            depth=depth + 1,
        )

        result = operation(
            operand,
        )

        _validate_result(
            result,
        )

        return result

    raise ValueError(
        f"Der Ausdruckstyp "
        f"'{type(node).__name__}' "
        "ist nicht erlaubt.",
    )


def parse_and_evaluate(
    expression: str,
) -> Number:
    """
    Validiert, parst und berechnet einen Ausdruck.
    """

    normalized_expression = expression.strip()

    if not normalized_expression:
        raise ValueError(
            "Der mathematische Ausdruck darf nicht leer sein.",
        )

    if len(
        normalized_expression,
    ) > MAX_EXPRESSION_LENGTH:
        raise ValueError(
            "Der mathematische Ausdruck ist zu lang.",
        )

    try:
        parsed = ast.parse(
            normalized_expression,
            mode="eval",
        )

    except SyntaxError as exc:
        raise ValueError(
            "Der mathematische Ausdruck ist syntaktisch ungültig.",
        ) from exc

  
    result = evaluate(
        parsed.body,
    )

    _validate_result(
        result,
    )

    return result


def _validate_result(
    value: Number,
) -> None:
    """
    Verhindert nicht endliche oder unverhältnismäßig große Ergebnisse.
    """

    numeric_value = float(
        value,
    )

    if numeric_value != numeric_value:
        raise ValueError(
            "Das Ergebnis ist keine gültige Zahl.",
        )

    if numeric_value in {
        float("inf"),
        float("-inf"),
    }:
        raise ValueError(
            "Das Ergebnis ist nicht endlich.",
        )

    if abs(
        numeric_value,
    ) > MAX_ABSOLUTE_RESULT:
        raise ValueError(
            "Das Ergebnis überschreitet den erlaubten Wertebereich.",
        )


class CalculatorTool(BaseTool):
    """
    Sicherer Rechner für einfache mathematische Ausdrücke.
    """

    name: str = "calculator"

    description: str = (
        "Berechnet einfache mathematische Ausdrücke "
        "mit Addition, Subtraktion, Multiplikation und Division."
    )

    parameters: dict[str, object] = {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "title": "Mathematischer Ausdruck",
                "description": (
                    "Ein einfacher mathematischer Ausdruck, "
                    "zum Beispiel '(1250 * 0.19) + 81'."
                ),
                "minLength": 1,
                "maxLength": MAX_EXPRESSION_LENGTH,
            },
        },
        "required": [
            "expression",
        ],
        "additionalProperties": False,
    }

    # Diese Methode muss dieselbe Signatur wie BaseTool.execute besitzen.
    # Der bisherige **kwargs-Vertrag ist nicht mit BaseTool kompatibel.