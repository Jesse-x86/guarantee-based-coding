"""Server entry: starts from ConfigLoader's behavioral promises."""

from config_loader import ConfigLoader

loader = ConfigLoader({"port": "8080", "host": "0.0.0.0"})


def start_server() -> int:
    """Start the server from config and return the port.

    Trusts loader.get_config() never to be None —
    if get_config ever started returning None, int(None) would raise TypeError.
    """
    port_str = loader.get_config("port")
    # Downstream consumes it directly, trusting it is always str
    return int(port_str)


def get_timeout() -> int:
    """Read a timeout setting.

    Deliberately uses a likely-missing key ("timeout") to show missing-key
    behavior: the original impl returns "", and int("") would raise ValueError;
    without a default it returns None, and int(None) raises TypeError.
    """
    val = loader.get_config("timeout")
    return int(val) if val else 30  # "" → fall back to 30
