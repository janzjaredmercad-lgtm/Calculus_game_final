A 2D platform game where you solve derivatives to defeat function enemies.
It uses Pygame for the game and SymPy to check answers.

Controls:

- Left / Right arrows: move
- Space / Up: jump
- Type a derivative answer, then press Enter: fire the derivative gun
- Backspace: erase one character
- Delete: clear the answer
- q: open or close the formula guide

Rules:
- Use `^` for powers. Both `2*x` and `2x` work, Ex: enter `2x`
- Use () to group the expression for the power, Ex: 2^3x -> 2^(3x)
- Use of * is only required if left or right of it are both letters, Ex: xe^(2x) -> x*e^(2x)
- Put powers last if a function is made up of letters, Ex: sec(x)^2