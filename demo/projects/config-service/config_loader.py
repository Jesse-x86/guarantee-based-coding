"""Config loader: key-value reads that promise never to return None."""


class ConfigLoader:
    """Read config entries from an internal dict.

    Guarantee: get_config(key) always returns str, never None.
    Missing keys yield the empty string "" rather than None.
    """

    def __init__(self, defaults: dict[str, str] | None = None):
        self._config: dict[str, str] = dict(defaults or {})

    def get_config(self, key: str) -> str:
        """Return a config value.

        :param key: config key
        :return: value as str; "" when the key is missing
        """
        # Critical line: the "" default is what keeps "never None" true
        return self._config.get(key, "")
