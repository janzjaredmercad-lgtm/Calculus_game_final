import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

x = sp.symbols("x")

FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "cot": sp.cot,
    "sec": sp.sec,
    "csc": sp.csc,
    "log": sp.log,
    "sqrt": sp.sqrt,
    "e": sp.E,
    "pi": sp.pi,
    "x": x,
    "ln": sp.log
}

DERIVATIVE_FORMULAS = (
    "d/dx x^n = n*x^(n-1)",
    "d/dx c = 0",
    "d/dx e^x = e^x",
    "d/dx a^x = a^x*ln(a)",
    "d/dx a^u = u'(a^(u) ln(a))", 
    "d/dx sin(x) = cos(x)",
    "d/dx cos(x) = -sin(x)",
    "d/dx tan(x) = sec(x)^2",
    "d/dx cot(x) = -csc(x)^2",
    "d/dx sec(x) = sec(x)tan(x)",
    "d/dx csc(x) = -csc(x)cot(x)",
    "d/dx log(x) = 1/x",
    "Product rule: (u*v)' = u*v' + u'*v",
)

ALLOWED_INPUTS = set("acegilnopqrstx0123456789+-*/^(). ")


class InvalidExpression(ValueError):
    pass

def parse_expression(text):
    if isinstance(text, sp.Basic):
        return text

    text = str(text).strip()

    for char in text:
        if char not in ALLOWED_INPUTS:
            raise InvalidExpression("Use supported math symbols and functions.")

    rules = standard_transformations + (
        implicit_multiplication_application,
        convert_xor,
    )

    try:
        expr = parse_expr(text, local_dict=FUNCTIONS, transformations=rules)
    except Exception:
        raise InvalidExpression("Check your expression and try again.")
    for symbol in expr.free_symbols:
        if symbol != x:
            raise InvalidExpression("Only use x as your variable.")

    return expr


def differentiate(function):
    expr = parse_expression(function)
    return sp.diff(expr, x)


def check_derivative(answer, function):
    try:
        correct_ans = differentiate(function)
        user_ans = parse_expression(answer)
        
        diff = sp.simplify(correct_ans - user_ans)
        return diff == 0
    except Exception:
        return False


def format_expression(expression):
    text = str(expression)
    text = text.replace("**", "^")
    text = text.replace("exp(x)", "e^x")
    for i in range(2, 10):
        text = text.replace(f"exp({i}*x)", f"e^({i}*x)")
    text = text.replace("tan(x)^2 + 1", "sec(x)^2")
    text = text.replace("-cot(x)^2 - 1", "-csc(x)^2")
    text = text.replace("log", "ln")
    return text

def format_expression_entity(expression):
    text = str(expression)
    text = text.replace("**", "^")
    text = text.replace("exp(x)", "e^x")
    for i in range(2, 10):
        text = text.replace(f"exp({i}*x)", f"e^({i}*x)")
    text = text.replace("tan(x)^2 + 1", "sec(x)^2")
    text = text.replace("-cot(x)^2 - 1", "-csc(x)^2")
    return text