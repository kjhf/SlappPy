import sys
from typing import Optional


def ask(question: str, loop_until_answered: bool = True):
    while True:
        answer = input(question).lower()
        if answer in ("y", "yes", "true"):
            return True
        elif answer in ("n", "no", "false"):
            return False
        elif not loop_until_answered:
            return None
        # else loop


def pause(exit_if_no: bool = False, message: Optional[str] = None):
    if not message:
        message = "Paused. Press enter to continue." if exit_if_no else "Paused. Continue? [y/n]"

    if not exit_if_no:
        _ = input(message)
    else:
        result = ask(message, loop_until_answered=True)
        if result is False:
            sys.exit(0)
