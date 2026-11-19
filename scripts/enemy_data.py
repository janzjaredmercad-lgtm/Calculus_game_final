LEVEL_ENEMIES = [
    [
        ("polynomial", "x^2 + 2*x"),
        ("polynomial", "x^3 - x"),
        ("polynomial", "x^4 + 3*x^2 - 5"),
    ],
    [
        ("exponential", "e^x"),
        ("trigonometric", "sin(2x+5)"),
        ("exponential", "x*e^x"),
        ("trigonometric", "2x^2 + cos(x)"),
    ],
    [
        ("hybrid", "e^(2x) + tan(x) + 3log(x)"),
        ("boss_exponential", "2^(2^(2x))"),
        ("boss_logarithmic", "log(log(log(x)))"),
        ("boss_trigonometric", "sin(3x) + cos(2x)"),
    ],
]