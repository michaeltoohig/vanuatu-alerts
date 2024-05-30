import os
from vanuatu_alerts.main import main


def str_to_bool(value):
    true_values = {"y", "yes", "t", "true", "on", "1"}
    false_values = {"n", "no", "f", "false", "off", "0"}

    if isinstance(value, bool):
        return value
    if value.lower() in true_values:
        return True
    elif value.lower() in false_values:
        return False
    else:
        raise ValueError(f"Invalid truth value {value}")


IMMEDIATE = str_to_bool(os.environ.get("IMMEDIATE", "False"))

main(immediate=IMMEDIATE)
