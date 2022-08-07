import json
import os
from typing import Any, Dict, List, Union

Config = Union[List[Any], Dict[str, Any]]

def get_config(name: str = "bot", with_default: bool = True) -> Config:
    """
    Returns the config for the given name.
    """

    if with_default:
        default = get_default_config(name)
    else:
        default = dict()
    filepath = f"config/{name}.json"
    os.makedirs("config", exist_ok=True)

    if not os.path.exists(filepath) or os.stat(filepath).st_size == 0:
        # If the config file does not exist or is empty
        config = dict()
    else:
        with open(filepath, "r", encoding="utf-8") as config_file:
            config = json.load(config_file)

    return default | config

def get_default_config(name: str = "bot") -> Config:
    """
    Returns the default config for the given name.
    """

    filepath = f"defaults/{name}.json"
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return dict()

def expand_config_file(name: str = "bot") -> None:
    """
    Adds the missing default configurations to the config file.
    """

    with open(f"config/{name}.json", "w") as config_file:
        json.dump(get_config(name), config_file, indent=4)
