import sympy as sp


x = sp.symbols("x")

# These are the only function calls the player can type.
FUNCTIONS = {
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "log": sp.log,
    "sqrt": sp.sqrt,
}

DERIVATIVE_FORMULAS = (
    "d/dx x^n = n*x^(n-1)",
    "d/dx c = 0",
    "d/dx e^x = e^x",
    "d/dx sin(x) = cos(x)",
    "d/dx cos(x) = -sin(x)",
    "d/dx tan(x) = 1/cos(x)^2",
    "d/dx log(x) = 1/x",
    "Product rule: (u*v)' = u*v' +  u'*v",
    "Use * for multiplication; 2x is also accepted.",
    "Example answer: 2*x",
)

ALLOWED_INPUTS = set("acegilnopqrstx0123456789+-*/^().")


class InvalidExpression(ValueError):
    """The expression uses a symbol or operation the game does not support."""


def _tokenize(text):
    """Break the input into numbers, names, and math symbols."""
    tokens = []
    position = 0

    while position < len(text):
        character = text[position]

        if character.isspace():
            position += 1
        elif character.isdigit() or character == ".":
            start = position
            while position < len(text) and (text[position].isdigit() or text[position] == "."):
                position += 1
            number = text[start:position]
            if number == "." or number.count(".") > 1:
                raise InvalidExpression("Check the number in the expression.")
            tokens.append(number)
        elif character.isalpha():
            name = None
            for allowed_name in ("sin", "cos", "tan", "log", "sqrt", "pi", "x", "e"):
                if text.startswith(allowed_name, position):
                    name = allowed_name
                    break

            if name is None:
                start = position
                while position < len(text) and text[position].isalpha():
                    position += 1
                tokens.append(text[start:position])
            else:
                tokens.append(name)
                position += len(name)
        elif character in "+-*/^()":
            tokens.append(character)
            position += 1
        else:
            raise InvalidExpression("Use supported math symbols and functions.")

    return tokens


class ExpressionParser:
    """Read math tokens and turn them into a SymPy expression."""

    def __init__(self, text):
        self.tokens = _tokenize(text)
        self.position = 0

    def _peek(self):
        if self.position == len(self.tokens):
            return None
        return self.tokens[self.position]

    def _take(self):
        token = self._peek()
        if token is None:
            raise InvalidExpression("The expression ended too early.")
        self.position += 1
        return token

    def parse(self):
        result = self._parse_expression()
        if self._peek() is not None:
            raise InvalidExpression("Check the expression and use supported math.")
        return result

    def _parse_expression(self):
        """Read additions and subtractions."""
        result = self._parse_term()
        while self._peek() in ("+", "-"):
            operator = self._take()
            right = self._parse_term()
            if operator == "+":
                result += right
            else:
                result -= right
        return result

    def _parse_term(self):
        """Read multiplication and division, including shorthand like 2x."""
        result = self._parse_factor()
        while True:
            token = self._peek()
            if token in ("*", "/"):
                operator = self._take()
                right = self._parse_factor()
            elif self._starts_factor(token):
                operator = "*"
                right = self._parse_factor()
            else:
                break

            if operator == "/":
                result /= right
            else:
                result *= right
        return result

    def _starts_factor(self, token):
        if token is None:
            return False
        return (
            token == "("
            or token in ("x", "e", "pi")
            or token in FUNCTIONS
            or token[0].isdigit()
            or token[0] == "."
        )

    def _parse_factor(self):
        """Read a leading plus or minus, then a power."""
        if self._peek() == "+":
            self._take()
            return self._parse_factor()
        if self._peek() == "-":
            self._take()
            return -self._parse_factor()
        return self._parse_power()

    def _parse_power(self):
        """Read a value and, optionally, its exponent."""
        base = self._parse_primary()
        if self._peek() == "^":
            self._take()
            exponent = self._parse_factor()
            if exponent.free_symbols and base != sp.E:
                raise InvalidExpression("Variable powers are only supported with base e.")
            if not exponent.free_symbols and abs(float(exponent)) > 8:
                raise InvalidExpression("Use a constant power from -8 to 8.")
            return base ** exponent
        return base

    def _parse_primary(self):
        """Read a number, variable, function, or parenthesized expression."""
        token = self._take()

        if token[0].isdigit() or token[0] == ".":
            return sp.Rational(token)
        if token == "x":
            return x
        if token == "e":
            return sp.E
        if token == "pi":
            return sp.pi
        if token == "(":
            result = self._parse_expression()
            if self._take() != ")":
                raise InvalidExpression("Add a closing parenthesis.")
            return result
        if token in FUNCTIONS:
            if self._peek() != "(":
                raise InvalidExpression("Put the function input in parentheses.")
            self._take()
            argument = self._parse_expression()
            if self._take() != ")":
                raise InvalidExpression("Add a closing parenthesis.")
            return FUNCTIONS[token](argument)

        raise InvalidExpression("Use x, e, pi, or a supported function.")


def parse_expression(expression):
    """Convert a short math expression into a SymPy expression."""
    if isinstance(expression, sp.Basic):
        return expression
    return ExpressionParser(str(expression)).parse()


def differentiate(function):
    """Return the derivative of a function with respect to x."""
    return sp.diff(parse_expression(function), x)


def check_derivative(answer, function):
    """Check whether an answer is mathematically equal to the derivative."""
    try:
        difference = differentiate(function) - parse_expression(answer)
        return sp.simplify(difference) == 0
    except (TypeError, ValueError, OverflowError, RecursionError):
        return False


def format_expression(expression):
    """Make SymPy expressions easier to read above enemies."""
    text = str(expression).replace("**", "^")
    return text.replace("exp(x)", "e^x")