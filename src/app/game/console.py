"""Console screen helpers for the text game."""

import os


def clear_console():
    command = "cls" if os.name == "nt" else "clear"
    os.system(command)


def wait_for_continue(prompt="Press Enter to continue..."):
    input(prompt)

