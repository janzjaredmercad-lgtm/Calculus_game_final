import sympy as sp

ALLOWED_INPUTS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "e", "l", "n", "|", "(", ")", "/", "+", "-", "*"]


class Calculate_Derivative:
    def differentiate(function):
        x = sp.symbols('x')
        return sp.diff(function, x)

    def check_derivative(self, function, answer):
        correct_answer = self.differentiate(function)
        if sp.simplify(correct_answer - answer) == 0:
            return correct_answer

    