LEVEL_ENEMIES = [
    [
        ("trigonometric", "sin(x)"),
        ("weak_trigonometric", "tan(x)"),
        ("polynomial", "5e^x"),
        ("weak_exponential", "7e^(-2x)"),
    ],
    [
        ("weak_logarithmic", "4ln(x)"),
        ("exponential", "2e^(3x)"),
        ("trigonometric", "sec(x)"),
        ("trigonometric", "2tan(4x+2)"),
    ],
    [
        ("polynomial", "x^4 + 3x^3 + 2x^2 + 6x - 5"),
        ("trigonometric", "sin(6x+5)"),
        ("polynomial", "x^4 + 3x^3 + 5x^2 - 2x - x"),
        ("trigonometric", "2*x^2 + sin(x)"),
        ("trigonometric", "3*x^2 + cos(x)"),
        ("weak_trigonometric", "x^2 + tan(x)"),
    ],
    [
        ("hybrid", "e^(2x) + tan(x) + 3log(x)"),
        ("weak_exponential", "2^(2^(2x))"),
        ("weak_logarithmic", "ln(ln(ln(x)))"),
        ("boss", "sin(3x) + cos(2x)"),
    ],
]