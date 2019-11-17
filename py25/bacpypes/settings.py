#!/usr/bin/python

"""
Settings
"""

import os


class Settings(dict):
    """
    Settings
    """

    def __getattr__(self, name):
        if name not in self:
            raise AttributeError("No such setting: " + name)
        return self[name]

    def __setattr__(self, name, value):
        if name not in self:
            raise AttributeError("No such setting: " + name)
        self[name] = value


# globals
settings = Settings(
    debug=set(),
    color=False,
    debug_file="",
    max_bytes=1048576,
    backup_count=5,
    route_aware=False,
)


def os_settings():
    """
    Update the settings from known OS environment variables.
    """
    for setting_name, env_name in (
        ("debug", "BACPYPES_DEBUG"),
        ("color", "BACPYPES_COLOR"),
        ("debug_file", "BACPYPES_DEBUG_FILE"),
        ("max_bytes", "BACPYPES_MAX_BYTES"),
        ("backup_count", "BACPYPES_BACKUP_COUNT"),
        ("route_aware", "BACPYPES_ROUTE_AWARE"),
    ):
        env_value = os.getenv(env_name, None)
        if env_value is not None:
            cur_value = settings[setting_name]

            if isinstance(cur_value, bool):
                env_value = env_value.lower()
                if env_value in ("set", "true"):
                    env_value = True
                elif env_value in ("reset", "false"):
                    env_value = False
                else:
                    raise ValueError("setting: " + setting_name)
            elif isinstance(cur_value, int):
                try:
                    env_value = int(env_value)
                except:
                    raise ValueError("setting: " + setting_name)
            elif isinstance(cur_value, str):
                pass
            elif isinstance(cur_value, list):
                env_value = env_value.split()
            elif isinstance(cur_value, set):
                env_value = set(env_value.split())
            else:
                raise TypeError("setting type: " + setting_name)
            settings[setting_name] = env_value


def dict_settings(**kwargs):
    """
    Update the settings from key/value content.  Lists are morphed into sets
    if necessary, giving a setting any value is acceptable if there isn't one
    already set, otherwise protect against setting type changes.
    """
    for setting_name, kw_value in kwargs.items():
        cur_value = settings.get(setting_name, None)

        if cur_value is None:
            pass
        elif isinstance(cur_value, set):
            if isinstance(kw_value, list):
                kw_value = set(kw_value)
            elif not isinstance(kw_value, set):
                raise TypeError(setting_name)
        elif not isinstance(kw_value, type(cur_value)):
            raise TypeError("setting type: " + setting_name)
        settings[setting_name] = kw_value
