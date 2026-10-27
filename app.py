
import os
import random
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "local-development-key"
)


# ---------- N-QUEENS SOLVER ----------

def solve_queens(n):
    board = [-1] * n

    def solve(r):
        if r == n:
            return True

        for c in range(n):
            if all(
                board[i] != c and
                abs(board[i] - c) != abs(r - i)
                for i in range(r)
            ):
                board[r] = c

                if solve(r + 1):
                    return True

                board[r] = -1

        return False

    return board if solve(0) else None


# ---------- CHECK MANUAL N-QUEENS ----------

def check_queens(queens, n):
    if len(queens) != n:
        return False

    rows = [r for r, c in queens]
    cols = [c for r, c in queens]

    if len(set(rows)) != n or len(set(cols)) != n:
        return False

    for i in range(n):
        for j in range(i + 1, n):
            r1, c1 = queens[i]
            r2, c2 = queens[j]

            if abs(r1 - r2) == abs(c1 - c2):
                return False

    return True


# ---------- SUDOKU SOLVER ----------

def solve_sudoku(b):
    for r in range(9):
        for c in range(9):
            if b[r][c] == 0:
                for n in range(1, 10):
                    if (
                        n not in b[r] and
                        all(b[i][c] != n for i in range(9)) and
                        all(
                            b[i][j] != n
                            for i in range(r // 3 * 3, r // 3 * 3 + 3)
                            for j in range(c // 3 * 3, c // 3 * 3 + 3)
                        )
                    ):
                        b[r][c] = n

                        if solve_sudoku(b):
                            return True

                        b[r][c] = 0

                return False

    return True


# ---------- RANDOM SUDOKU GENERATOR ----------

def new_sudoku():
    base = [
        [(r * 3 + r // 3 + c) % 9 for c in range(9)]
        for r in range(9)
    ]

    rows = [
        g * 3 + r
        for g in random.sample(range(3), 3)
        for r in random.sample(range(3), 3)
    ]

    cols = [
        g * 3 + c
        for g in random.sample(range(3), 3)
        for c in random.sample(range(3), 3)
    ]

    nums = random.sample(range(1, 10), 9)

    solution = [
        [nums[base[rows[r]][cols[c]]]
         for c in range(9)]
        for r in range(9)
    ]

    puzzle = [row[:] for row in solution]

    for cell in random.sample(range(81), 45):
        puzzle[cell // 9][cell % 9] = 0

    return puzzle, solution


# ---------- MATH CHALLENGE ----------

def make_question():
    a = random.randint(2, 12)
    b = random.randint(2, 12)
    op = random.choice(["+", "-", "*"])

    if op == "+":
        answer = a + b
    elif op == "-":
        answer = a - b
    else:
        answer = a * b

    return f"{a} {op} {b} = ?", answer


# ---------- HOME PAGE ----------

@app.route("/")
def home():
    return render_template("index.html")


# ---------- N-QUEENS PAGE ----------

@app.route("/queens", methods=["GET", "POST"])
def queens():
    n = 4
    result = None
    message = ""
    hint_question = None
    manual_queens = []
    manual_message = ""

    # Restore a pending manual board after submission
    if request.method == "GET":
        saved = session.pop("manual_queens", [])
        manual_queens = [
            tuple(cell) for cell in saved
        ]

    if request.method == "POST":
        try:
            n = int(request.form.get("n", 4))
        except (ValueError, TypeError):
            n = 4

        if not 1 <= n <= 14:
            n = 4
            message = "Choose a board size between 1 and 14."

        action = request.form.get("action")

        if action == "solve" and not message:
            result = solve_queens(n)
            message = (
                "Solution found!" if result is not None
                else "No solution exists for this board size."
            )

        elif action == "hint" and not message:
            q, a = make_question()
            session["q_answer"] = a
            session["q_n"] = n
            session["q_question"] = q
            hint_question = q

        elif action == "check_hint":
            hint_question = session.get("q_question")
            answer = request.form.get("math_answer", "")

            if (
                answer.lstrip("-").isdigit()
                and int(answer) == session.get("q_answer")
                and n == session.get("q_n")
            ):
                result = solve_queens(n)

                if result is not None:
                    message = (
                        f"Hint: Try placing the first queen "
                        f"in row 1, column {result[0] + 1}."
                    )
                else:
                    message = "No solution exists for this size."
            else:
                message = (
                    "Incorrect answer or changed board size. "
                    "Try again."
                )

            session.pop("q_answer", None)
            session.pop("q_question", None)
            session.pop("q_n", None)
            hint_question = None

        elif action == "check_manual" and not message:
            selected = request.form.getlist("queen")

            try:
                manual_queens = [
                    tuple(map(int, cell.split(",")))
                    for cell in selected
                ]
            except (ValueError, TypeError):
                manual_queens = []

            valid_coordinates = all(
                len(cell) == 2
                and 0 <= cell[0] < n
                and 0 <= cell[1] < n
                for cell in manual_queens
            )

            if not valid_coordinates:
                manual_queens = []
                manual_message = "Invalid board selection. Try again."
            elif check_queens(manual_queens, n):
                manual_message = (
                    "Correct! All queens are safely placed."
                )
            else:
                manual_message = (
                    "Not correct yet. Check the number of queens, "
                    "rows, columns and diagonals."
                )

        elif action == "reset_manual":
            manual_queens = []
            manual_message = ""

        # Preserve selected queens across page reloads
        session["manual_queens"] = [
            list(cell) for cell in manual_queens
        ]

    if not hint_question:
        hint_question = session.get("q_question")

    return render_template(
        "queens.html",
        n=n,
        result=result,
        message=message,
        hint_question=hint_question,
        manual_queens=manual_queens,
        manual_message=manual_message
    )


# ---------- SUDOKU PAGE ----------

@app.route("/sudoku", methods=["GET", "POST"])
def sudoku():
    if "puzzle" not in session:
        p, s = new_sudoku()
        session["puzzle"] = p
        session["solution"] = s
        session["current"] = p

    puzzle = session["puzzle"]
    solution = session["solution"]
    board = session.get("current", puzzle)
    message = ""
    solved_board = None
    hint_question = session.get("s_question")

    if request.method == "POST":
        action = request.form.get("action")

        if action == "new":
            p, s = new_sudoku()
            session["puzzle"] = p
            session["solution"] = s
            session["current"] = p
            session.pop("s_question", None)
            session.pop("s_answer", None)
            return redirect(url_for("sudoku"))

        # Read the user's current 9x9 grid.
        board = []
        valid = True

        for r in range(9):
            row = []

            for c in range(9):
                value = request.form.get(f"cell_{r}_{c}", "")

                if value == "":
                    row.append(0)
                elif value.isdigit() and 1 <= int(value) <= 9:
                    row.append(int(value))
                else:
                    row.append(0)
                    valid = False

            board.append(row)

        # Keep original clues unchanged.
        for r in range(9):
            for c in range(9):
                if puzzle[r][c] != 0:
                    board[r][c] = puzzle[r][c]

        session["current"] = board

        if not valid:
            message = "Enter only numbers from 1 to 9."

        elif action == "solve":
            copy_board = [row[:] for row in board]

            if solve_sudoku(copy_board):
                solved_board = copy_board
                message = "Solution found!"
            else:
                message = "This board has no valid solution."

        elif action == "check":
            if any(0 in row for row in board):
                message = "Fill in the empty cells first."
            elif board == solution:
                message = "Excellent! You solved the Sudoku!"
            else:
                message = "Some numbers are incorrect. Try again."

        elif action == "hint":
            q, a = make_question()
            session["s_question"] = q
            session["s_answer"] = a
            hint_question = q

        elif action == "check_hint":
            answer = request.form.get("math_answer", "")

            if (
                answer.lstrip("-").isdigit()
                and int(answer) == session.get("s_answer")
            ):
                found = False

                for r in range(9):
                    for c in range(9):
                        if board[r][c] == 0:
                            message = (
                                f"Hint: Row {r + 1}, column {c + 1} "
                                f"should contain {solution[r][c]}."
                            )
                            found = True
                            break

                    if found:
                        break

                if not found:
                    message = "The Sudoku is already complete!"
            else:
                message = "Incorrect maths answer. Try again."

            session.pop("s_question", None)
            session.pop("s_answer", None)
            hint_question = None

    return render_template(
        "sudoku.html",
        puzzle=puzzle,
        board=board,
        message=message,
        hint_question=hint_question,
        solved_board=solved_board
    )


if __name__ == "__main__":
    app.run(debug=True)
