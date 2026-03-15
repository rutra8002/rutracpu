from rutracpu.compiler.ast import AssignStatement
from rutracpu.compiler.ast import ForStatement
from rutracpu.compiler.ast import LiteralExpr
from rutracpu.compiler.ast import OffsetExpr
from rutracpu.compiler.ast import PrintStatement
from rutracpu.compiler.ast import Statement
from rutracpu.compiler.ast import VariableExpr


ALLOWED_VARIABLE_TYPES = {"int", "char"}


def strip_comment(raw_line: str) -> str:
    in_string = False
    escaped = False
    result = []

    for ch in raw_line:
        if escaped:
            result.append(ch)
            escaped = False
            continue

        if ch == "\\":
            result.append(ch)
            escaped = True
            continue

        if ch == '"':
            in_string = not in_string
            result.append(ch)
            continue

        if ch == "#" and not in_string:
            break

        result.append(ch)

    return "".join(result)


def validate_identifier(name: str, line_no: int) -> str:
    if not name:
        raise ValueError(f"Line {line_no}: missing identifier.")

    if not (name[0].isalpha() or name[0] == "_"):
        raise ValueError(f"Line {line_no}: invalid identifier '{name}'.")

    for ch in name[1:]:
        if not (ch.isalnum() or ch == "_"):
            raise ValueError(f"Line {line_no}: invalid identifier '{name}'.")

    return name


def parse_u8(raw_value: str, line_no: int, label: str) -> int:
    try:
        value = int(raw_value, 0)
    except ValueError as exc:
        raise ValueError(f"Line {line_no}: invalid {label} '{raw_value}'.") from exc

    if value < 0 or value > 255:
        raise ValueError(f"Line {line_no}: {label} out of range: {value}. Valid range is 0..255.")

    return value


def parse_expression(raw_expr: str, line_no: int):
    text = raw_expr.strip()
    if not text:
        raise ValueError(f"Line {line_no}: missing expression.")

    try:
        return LiteralExpr(parse_u8(text, line_no, "integer"))
    except ValueError:
        pass

    if text.startswith('"'):
        literal = parse_string_literal(text, line_no)
        if len(literal) != 1:
            raise ValueError(f"Line {line_no}: variables can only store one byte, so string literals must be one character long.")
        return LiteralExpr(ord(literal))

    for operator in ("+", "-"):
        if operator in text:
            left, right = text.split(operator, 1)
            name = validate_identifier(left.strip(), line_no)
            amount = parse_u8(right.strip(), line_no, "integer")
            return OffsetExpr(name, operator, amount)

    return VariableExpr(validate_identifier(text, line_no))


def parse_string_literal(raw_value: str, line_no: int) -> str:
    if len(raw_value) < 2 or raw_value[0] != '"' or raw_value[-1] != '"':
        raise ValueError(f"Line {line_no}: expected a quoted string literal.")

    try:
        decoded = bytes(raw_value[1:-1], "ascii").decode("unicode_escape")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Line {line_no}: invalid string escape sequence.") from exc

    try:
        decoded.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"Line {line_no}: strings must be ASCII.") from exc

    return decoded


def parse_assignment(raw_line: str, line_no: int, declare: bool) -> AssignStatement:
    left, right = raw_line.split("=", 1)
    name = validate_identifier(left.strip(), line_no)
    expr = parse_expression(right.strip(), line_no)
    return AssignStatement(name=name, expr=expr, declare=declare, variable_type=None, line_no=line_no)


def parse_declaration(raw_line: str, line_no: int) -> AssignStatement:
    if "=" not in raw_line:
        raise ValueError(f"Line {line_no}: variable declaration requires '='.")

    left, right = raw_line.split("=", 1)
    left_parts = left.strip().split()
    if len(left_parts) == 1:
        variable_type = None
        name = validate_identifier(left_parts[0], line_no)
    elif len(left_parts) == 2:
        variable_type = left_parts[0].lower()
        if variable_type not in ALLOWED_VARIABLE_TYPES:
            allowed = ", ".join(sorted(ALLOWED_VARIABLE_TYPES))
            raise ValueError(f"Line {line_no}: unknown variable type '{left_parts[0]}'. Allowed: {allowed}.")
        name = validate_identifier(left_parts[1], line_no)
    else:
        raise ValueError(f"Line {line_no}: invalid variable declaration syntax.")

    expr = parse_expression(right.strip(), line_no)
    return AssignStatement(name=name, expr=expr, declare=True, variable_type=variable_type, line_no=line_no)


def parse_print(raw_line: str, line_no: int) -> PrintStatement:
    payload = raw_line[6:].strip()
    if not payload:
        raise ValueError(f"Line {line_no}: print requires a value or string.")

    if payload.startswith('"'):
        return PrintStatement(expr=None, text=parse_string_literal(payload, line_no), line_no=line_no)

    return PrintStatement(expr=parse_expression(payload, line_no), text=None, line_no=line_no)


def parse_for_header(raw_line: str, line_no: int) -> tuple[str, int, int]:
    if not raw_line.endswith("{"):
        raise ValueError(f"Line {line_no}: for loop must end with '{{'.")

    header = raw_line[:-1].strip()
    if not header.lower().startswith("for "):
        raise ValueError(f"Line {line_no}: invalid for loop syntax.")

    body = header[4:].strip()
    name_part, separator, remainder = body.partition(" from ")
    if not separator:
        raise ValueError(f"Line {line_no}: for loop must use 'from'.")

    start_raw, separator, end_raw = remainder.partition(" to ")
    if not separator:
        raise ValueError(f"Line {line_no}: for loop must use 'to'.")

    loop_name = validate_identifier(name_part.strip(), line_no)

    start = parse_u8(start_raw.strip(), line_no, "loop start")
    end = parse_u8(end_raw.strip(), line_no, "loop end")
    if start > end:
        raise ValueError(f"Line {line_no}: descending loops are not supported ({start} to {end}).")

    return loop_name, start, end


def parse_statement(raw_line: str, line_no: int) -> Statement:
    if raw_line.lower().startswith("let "):
        return parse_declaration(raw_line[4:].strip(), line_no)

    if raw_line.lower().startswith("print "):
        return parse_print(raw_line, line_no)

    if "=" in raw_line:
        return parse_assignment(raw_line, line_no, declare=False)

    raise ValueError(f"Line {line_no}: unsupported statement '{raw_line}'.")


def parse_block(lines: list[str], start_index: int, inside_loop: bool) -> tuple[list[Statement], int]:
    statements: list[Statement] = []
    index = start_index

    while index < len(lines):
        line_no = index + 1
        clean_line = strip_comment(lines[index]).strip()
        index += 1

        if not clean_line:
            continue

        if clean_line == "}":
            if not inside_loop:
                raise ValueError(f"Line {line_no}: unexpected closing brace.")
            return statements, index

        if clean_line.lower().startswith("for "):
            loop_name, start, end = parse_for_header(clean_line, line_no)
            body, index = parse_block(lines, index, inside_loop=True)
            statements.append(ForStatement(name=loop_name, start=start, end=end, body=body, line_no=line_no))
            continue

        statements.append(parse_statement(clean_line, line_no))

    if inside_loop:
        raise ValueError("Missing closing brace for for loop.")

    return statements, index


def parse_program(source: str) -> list[Statement]:
    statements, _ = parse_block(source.splitlines(), 0, inside_loop=False)
    return statements
