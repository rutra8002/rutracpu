from pathlib import Path

from rutracpu.compiler.ast import AssignStatement
from rutracpu.compiler.ast import Expression
from rutracpu.compiler.ast import ForStatement
from rutracpu.compiler.ast import GpuClearStatement
from rutracpu.compiler.ast import GpuPlotStatement
from rutracpu.compiler.ast import GpuPresentStatement
from rutracpu.compiler.ast import GpuSetStatement
from rutracpu.compiler.ast import LiteralExpr
from rutracpu.compiler.ast import OffsetExpr
from rutracpu.compiler.ast import PrintStatement
from rutracpu.compiler.ast import Statement
from rutracpu.compiler.ast import VariableExpr
from rutracpu.compiler.ast import VariableType
from rutracpu.compiler.parser import parse_program


GPU_CMD_SET_X = 0xF0
GPU_CMD_SET_Y = 0xF1
GPU_CMD_PLOT = 0xF2
GPU_CMD_CLEAR = 0xF3
GPU_CMD_PRESENT = 0xF4


def encode_string_literal(text: str) -> str:
    return text.encode("unicode_escape").decode("ascii").replace('"', '\\"')


class Compiler:
    def __init__(self, source_name: str) -> None:
        self.source_name = source_name
        self.variables: dict[str, int] = {}
        self.variable_types: dict[str, VariableType] = {}
        self.instructions: list[str] = []
        self.next_address = 0
        self.active_loop_vars: list[str] = []

    def allocate_variable(self, name: str, line_no: int, variable_type: VariableType) -> int:
        if name in self.variables:
            return self.variables[name]

        if self.next_address > 255:
            raise ValueError(f"Line {line_no}: out of RAM variables. Maximum is 256.")

        address = self.next_address
        self.variables[name] = address
        self.variable_types[name] = variable_type
        self.next_address += 1
        return address

    def require_variable(self, name: str, line_no: int) -> int:
        if name not in self.variables:
            raise ValueError(f"Line {line_no}: variable '{name}' is not declared.")
        return self.variables[name]

    def require_variable_type(self, name: str, line_no: int) -> VariableType:
        self.require_variable(name, line_no)
        return self.variable_types[name]

    def infer_declaration_type(self, stmt: AssignStatement) -> VariableType:
        if stmt.variable_type is not None:
            return stmt.variable_type

        if isinstance(stmt.expr, LiteralExpr):
            return "int"

        return "int"

    def emit(self, mnemonic: str, operand: int | None = None) -> int:
        if operand is None:
            self.instructions.append(mnemonic)
        else:
            self.instructions.append(f"{mnemonic} {operand}")
        return len(self.instructions) - 1

    def patch_operand(self, index: int, operand: int) -> None:
        mnemonic = self.instructions[index].split()[0]
        self.instructions[index] = f"{mnemonic} {operand}"

    def compile_expression_load(self, expr: Expression, line_no: int) -> None:
        if isinstance(expr, LiteralExpr):
            self.emit("LOAD_IMMEDIATE", expr.value)
            return

        if isinstance(expr, VariableExpr):
            self.emit("LOAD", self.require_variable(expr.name, line_no))
            return

        if isinstance(expr, OffsetExpr):
            address = self.require_variable(expr.name, line_no)
            self.emit("LOAD", address)
            if expr.operator == "+":
                self.emit("ADD_IMMEDIATE", expr.amount)
            else:
                self.emit("SUBTRACT_IMMEDIATE", expr.amount)
            return

        raise ValueError(f"Line {line_no}: unsupported expression.")

    def compile_assignment(self, stmt: AssignStatement) -> None:
        if stmt.name in self.active_loop_vars:
            raise ValueError(f"Line {stmt.line_no}: cannot assign to active loop variable '{stmt.name}'.")

        if stmt.declare:
            variable_type = self.infer_declaration_type(stmt)
            address = self.allocate_variable(stmt.name, stmt.line_no, variable_type)
        else:
            address = self.require_variable(stmt.name, stmt.line_no)

        self.compile_expression_load(stmt.expr, stmt.line_no)
        self.emit("STORE", address)

    def compile_print(self, stmt: PrintStatement) -> None:
        if stmt.text is not None:
            for ch in stmt.text:
                self.emit("LOAD_IMMEDIATE", ord(ch))
                self.emit("OUTPUT_CHAR")
            return

        if stmt.expr is None:
            raise ValueError(f"Line {stmt.line_no}: print requires an expression or string.")

        self.compile_expression_load(stmt.expr, stmt.line_no)
        if isinstance(stmt.expr, VariableExpr) and self.require_variable_type(stmt.expr.name, stmt.line_no) == "char":
            self.emit("OUTPUT_CHAR")
        else:
            self.emit("OUTPUT_INT")

    def compile_for(self, stmt: ForStatement) -> None:
        if stmt.name in self.active_loop_vars:
            raise ValueError(f"Line {stmt.line_no}: loop variable '{stmt.name}' is already active.")

        address = self.allocate_variable(stmt.name, stmt.line_no, "int")
        self.emit("LOAD_IMMEDIATE", stmt.start)
        self.emit("STORE", address)

        loop_start = len(self.instructions)
        self.active_loop_vars.append(stmt.name)
        for child in stmt.body:
            self.compile_statement(child)
        self.active_loop_vars.pop()

        self.emit("LOAD", address)
        self.emit("SUBTRACT_IMMEDIATE", stmt.end)
        skip_increment = self.emit("JUMP_IF_ZERO", 0)
        self.emit("LOAD", address)
        self.emit("ADD_IMMEDIATE", 1)
        self.emit("STORE", address)
        self.emit("JUMP", loop_start)
        loop_end = len(self.instructions)

        self.patch_operand(skip_increment, loop_end)

    def emit_gpu_command(self, command_byte: int) -> None:
        self.emit("LOAD_IMMEDIATE", command_byte)
        self.emit("OUTPUT_CHAR")

    def emit_expr_as_char(self, expr: Expression, line_no: int) -> None:
        self.compile_expression_load(expr, line_no)
        self.emit("OUTPUT_CHAR")

    def compile_gpu_set(self, stmt: GpuSetStatement) -> None:
        if isinstance(stmt.x_expr, LiteralExpr) and stmt.x_expr.value > 15:
            raise ValueError(f"Line {stmt.line_no}: gpu_set x out of range: {stmt.x_expr.value}. Valid range is 0..15.")
        if isinstance(stmt.y_expr, LiteralExpr) and stmt.y_expr.value > 15:
            raise ValueError(f"Line {stmt.line_no}: gpu_set y out of range: {stmt.y_expr.value}. Valid range is 0..15.")

        self.emit_gpu_command(GPU_CMD_SET_X)
        self.emit_expr_as_char(stmt.x_expr, stmt.line_no)
        self.emit_gpu_command(GPU_CMD_SET_Y)
        self.emit_expr_as_char(stmt.y_expr, stmt.line_no)

    def compile_gpu_plot(self, stmt: GpuPlotStatement) -> None:
        self.emit_gpu_command(GPU_CMD_PLOT)
        self.emit_expr_as_char(stmt.value_expr, stmt.line_no)

    def compile_statement(self, stmt: Statement) -> None:
        if isinstance(stmt, AssignStatement):
            self.compile_assignment(stmt)
            return

        if isinstance(stmt, PrintStatement):
            self.compile_print(stmt)
            return

        if isinstance(stmt, GpuClearStatement):
            self.emit_gpu_command(GPU_CMD_CLEAR)
            return

        if isinstance(stmt, GpuPresentStatement):
            self.emit_gpu_command(GPU_CMD_PRESENT)
            return

        if isinstance(stmt, GpuSetStatement):
            self.compile_gpu_set(stmt)
            return

        if isinstance(stmt, GpuPlotStatement):
            self.compile_gpu_plot(stmt)
            return

        self.compile_for(stmt)

    def compile_program(self, program: list[Statement]) -> str:
        for stmt in program:
            self.compile_statement(stmt)

        lines = [f"; Generated from {self.source_name}"]
        if self.variables:
            layout = ", ".join(
                f"{name}:{self.variable_types[name]}={address}" for name, address in self.variables.items()
            )
            lines.append(f"; RAM layout: {layout}")
        lines.extend(self.instructions)
        lines.append("HALT")
        return "\n".join(lines) + "\n"


def compile_to_rasm(source_path: Path, output_path: Path | None = None) -> Path:
    if not source_path.exists():
        raise FileNotFoundError(f"Source file not found: {source_path}")

    if output_path is None:
        output_path = source_path.with_suffix(".rasm")

    program = parse_program(source_path.read_text(encoding="utf-8-sig"))
    compiler = Compiler(source_name=source_path.name)
    output_path.write_text(compiler.compile_program(program), encoding="ascii")
    return output_path
