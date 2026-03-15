from __future__ import annotations

from dataclasses import dataclass


VariableType = str


@dataclass(frozen=True)
class LiteralExpr:
    value: int


@dataclass(frozen=True)
class VariableExpr:
    name: str


@dataclass(frozen=True)
class OffsetExpr:
    name: str
    operator: str
    amount: int


Expression = LiteralExpr | VariableExpr | OffsetExpr


@dataclass(frozen=True)
class AssignStatement:
    name: str
    expr: Expression
    declare: bool
    variable_type: VariableType | None
    line_no: int


@dataclass(frozen=True)
class PrintStatement:
    expr: Expression | None
    text: str | None
    line_no: int


@dataclass(frozen=True)
class ForStatement:
    name: str
    start: int
    end: int
    body: list[Statement]
    line_no: int


Statement = AssignStatement | PrintStatement | ForStatement
