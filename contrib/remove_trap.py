## Remove Traps Turbo Trainer
## This scripts resolves the Remove Traps mini-game automatically.
##
## Copyright Caporale Simone - 2024
##
## This version of the script is inspired from the UOAlive Discord Thread of Thomasthorun (Thanks).
## I copied some ideas like the clicloc search for the gump and the gump size calculation.
## I call it "Turbo Trainer" because it tries to match the actual path with known solutions to speed up the resolution.
##
## My benchmarks:
##  Trap 3x3:  average 27 seconds on 356 tries
##  Trap 4x4:  average 33 seconds om 100 tries
##  Trap 5x5:  average 35 seconds om 245 tries
## (https://github.com/caporalesimone)

# Script by ThomasThorun(https://github.com/ThomasThorun). The Turbo Solver was SimonSoft (https://github.com/caporalesimone/) idea.

# Translated to TazUO Iron Python/GUI by Daennabis. Most of the code remains the same with minor changes for python.

import re
import time

import API

pause = 0.10


class Dir:
    Invalid = 0
    Up = 1
    Right = 2
    Down = 3
    Left = 4


class MoveResult:
    Disarmed = 0
    WrongTry = 1
    ValidTry = 2
    SomethingWentWrong = 3


# Solutions
known_solutions_3x3 = [
    [Dir.Down, Dir.Right, Dir.Right, Dir.Down],
    [Dir.Down, Dir.Right, Dir.Down, Dir.Right],
    [Dir.Down, Dir.Down, Dir.Right, Dir.Right],
    [Dir.Down, Dir.Down, Dir.Right, Dir.Up, Dir.Up, Dir.Right, Dir.Down, Dir.Down],
    [Dir.Right, Dir.Right, Dir.Down, Dir.Down],
    [Dir.Right, Dir.Down, Dir.Left, Dir.Down, Dir.Right, Dir.Right],
    [Dir.Right, Dir.Down, Dir.Right, Dir.Down],
    [Dir.Right, Dir.Down, Dir.Down, Dir.Right],
]

known_solutions_4x4 = [
    [Dir.Down, Dir.Right, Dir.Down, Dir.Right, Dir.Right, Dir.Down],
    [Dir.Down, Dir.Right, Dir.Right, Dir.Up, Dir.Right, Dir.Down, Dir.Down, Dir.Down],
    [Dir.Down, Dir.Right, Dir.Right, Dir.Right, Dir.Down, Dir.Down],
    [
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Up,
        Dir.Up,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [Dir.Down, Dir.Down, Dir.Right, Dir.Up, Dir.Right, Dir.Right, Dir.Down, Dir.Down],
    [Dir.Down, Dir.Down, Dir.Down, Dir.Right, Dir.Right, Dir.Right],
    [Dir.Right, Dir.Down, Dir.Right, Dir.Right, Dir.Down, Dir.Down],
    [
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Right,
    ],
    [
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Right,
    ],
    [Dir.Right, Dir.Right, Dir.Down, Dir.Right, Dir.Down, Dir.Down],
    [Dir.Right, Dir.Right, Dir.Right, Dir.Down, Dir.Down, Dir.Down],
    [
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Left,
        Dir.Left,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Down,
    ],
]

known_solutions_5x5 = [
    [
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Right,
    ],
    [
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Up,
        Dir.Left,
        Dir.Left,
        Dir.Up,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Right,
    ],
    [
        Dir.Down,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Up,
        Dir.Up,
        Dir.Up,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [
        Dir.Down,
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Down,
    ],
    [
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Up,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Up,
        Dir.Up,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
    ],
    [
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
    ],
    [
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Down,
        Dir.Down,
    ],
    [
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Down,
        Dir.Left,
        Dir.Left,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
    ],
    [
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Down,
        Dir.Left,
        Dir.Left,
        Dir.Left,
        Dir.Left,
        Dir.Down,
        Dir.Down,
        Dir.Right,
        Dir.Right,
        Dir.Right,
        Dir.Right,
    ],
]


def dir_to_str(direction):
    if direction == Dir.Up:
        return "^"
    if direction == Dir.Right:
        return ">"
    if direction == Dir.Down:
        return "v"
    if direction == Dir.Left:
        return "<"
    else:
        return "Unknown"


def dir_list_to_str(directions):
    return "".join([dir_to_str(d) for d in directions])


def open_trap(serial):
    while True:
        API.UseSkill("Remove Trap")
        if API.WaitForTarget("Neutral", 1):
            break
        API.Pause(10)
    API.Target(serial)  # pyright:ignore

    return wait_for_remove_trap_gump()


def wait_for_remove_trap_gump():
    trap_open_time = time.time()
    while True:
        current_time = time.time()
        gump_id = API.HasGump()  # Grab the first gump
        if API.GumpContains("Trap", gump_id):  # verify this is trap gump
            return gump_id
        if current_time - trap_open_time > 5:  # Timer to break loop
            API.SysMsg("Gump not found.", 33)
            return 0
        API.Pause(pause)


def calculate_trap_size(gump_id):
    raw = API.GetGump(gump_id).PacketGumpText
    diamond_count = len(re.findall(r"9720", raw))  # Gray Diamond ID

    if diamond_count <= 7:
        return 3
    elif diamond_count < 23:
        return 4
    else:
        return 5


# CORE GAME LOGIC + MOVE EXECUTION
def play_game(gump_id, size, trap_serial):
    path = []
    failedDirections = []

    attempt = (
        MoveResult.ValidTry
    )  # First try is always valid/This shows the status of the current attempt
    TryDirection = Dir.Invalid
    for _ in range(0, 50):
        solutionFitness, foundSolution = calculate_path_fitness(size, path)
        if solutionFitness > 0:
            # Continue with the missing steps of the solution
            for i in range(len(path), len(foundSolution)):
                TryDirection = foundSolution[i]
                attempt = move_to(gump_id, TryDirection)

                # Check if the step is valid. Expected result should be always valid.
                if (
                    attempt == MoveResult.WrongTry
                    or attempt == MoveResult.SomethingWentWrong
                ):
                    API.SysMsg("The found solution is not valid!!", 33)
                    break  # The found solution isn't valid.

        else:
            if attempt == MoveResult.WrongTry:
                for step in path:
                    check = move_to(gump_id, step)
                    if check == (MoveResult.WrongTry or MoveResult.SomethingWentWrong):
                        return False  # Something went wrong
            TryDirection = next_direction(size, path, failedDirections)

            attempt = move_to(gump_id, TryDirection)

        if attempt == MoveResult.Disarmed:
            path.append(TryDirection)
            # if STORE_UNKNOWN_SOLUTIONS_ON_FILE == True: store_solution(size, path)
            return True
        if attempt == MoveResult.WrongTry:
            failedDirections.append(TryDirection)
            if open_trap(trap_serial) != gump_id:
                return False
            continue
        if attempt == MoveResult.ValidTry:
            path.append(TryDirection)
            failedDirections.clear()
            continue
        if attempt == MoveResult.SomethingWentWrong:
            return False
    API.SysMsg("Failed: Too many tries.", 33)
    return True


def move_to(gump_id, direction):
    API.ClearJournal()
    API.ReplyGump(direction, gump_id)
    for _ in range(50):
        if API.InJournal("successfully disarm"):
            return 0  # Disarmed
        if API.InJournal("fail to disarm the trap"):
            return 1  # Wrong Try
        if bool(API.HasGump(gump_id)):
            return 2  # Valid Try
        API.Pause(0.25)
    wait_for_remove_trap_gump()

    API.CloseGump(gump_id)
    return 3  # Something went wrong


def next_direction(size, prev, failed):
    row, col = 0, 0
    for step in prev:
        if step == Dir.Up:
            row -= 1
        elif step == Dir.Down:
            row += 1
        elif step == Dir.Left:
            col -= 1
        elif step == Dir.Right:
            col += 1

        if row < 0 or row >= size or col < 0 or col >= size:
            API.SysMsg("NextDirection failed: out of bounds", 33)
            return Dir.Invalid

    last = prev[-1] if prev else Dir.Invalid
    options = []
    if col < size - 1 and last != Dir.Left:
        options.append(Dir.Right)
    if row < size - 1 and last != Dir.Up:
        options.append(Dir.Down)
    if col > 0 and last != Dir.Right:
        options.append(Dir.Left)
    if row > 0 and last != Dir.Down:
        options.append(Dir.Up)

    options = [d for d in options if d not in failed]
    if not options:
        return Dir.Invalid
    if len(options) == 2:
        if Dir.Up in options and Dir.Down in options:
            return Dir.Down
        if Dir.Left in options and Dir.Right in options:
            return Dir.Right

    return calculate_best_next(size, prev, options)


# FITNESS MATCHING AND DIRECT SOLUTION
def calculate_path_fitness(size, path):
    pathSolution = []
    available_solutions = []
    if size == 3:
        available_solutions = known_solutions_3x3
    elif size == 4:
        available_solutions = known_solutions_4x4
    elif size == 5:
        available_solutions = known_solutions_5x5

    cntMatch = 0
    strPath = dir_list_to_str(path)

    for solution in available_solutions:
        strSolution = dir_list_to_str(solution)
        if strSolution.startswith(strPath):
            cntMatch += 1
            pathSolution = solution

    if cntMatch == 0:
        return 0, []
    if cntMatch > 1:
        return 0, []

    fitness = len(path) / len(pathSolution) * 100
    return fitness, pathSolution


def calculate_best_next(size, current_path, options):
    if len(current_path) < 2:
        return options[0]

    if size == 3:
        known = known_solutions_3x3
    elif size == 4:
        known = known_solutions_4x4
    elif size == 5:
        known = known_solutions_5x5
    else:
        return Dir.Invalid

    path_str = dir_list_to_str(current_path)

    for solution in known:
        if dir_list_to_str(solution).startswith(path_str):
            if len(solution) > len(current_path):
                next_dir = solution[len(current_path)]
                if next_dir in options:
                    return next_dir
            break

    return options[0]


def run():
    trap_serial = API.RequestTarget(10)
    API.SysMsg("Select the trap to disarm.")

    while True:
        gump_id = open_trap(trap_serial)
        if not gump_id:
            continue

        size = calculate_trap_size(gump_id)
        play_game(gump_id, size, trap_serial)


run()
