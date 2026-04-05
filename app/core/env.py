import os

from app.config.executor import EnvAction


def get_clean_python_path():
    env = os.environ.copy()
    pp_list = env.get("PYTHONPATH", "").split(os.pathsep)
    pp_list = pp_list[1:]
    env["PYTHONPATH"] = os.pathsep.join(pp_list)

    return env


def apply_env_action(env: dict[str, str], op: EnvAction, sep: str = os.pathsep) -> dict[str, str]:
    """
    对传入的 env 字典执行单个 EnvAction 操作。
    注：为了安全，建议传入 env.copy() 以避免副作用。
    """

    key = op.key
    val = op.value or ""

    match op.action:
        case "set":
            env[key] = val

        case "remove":
            env.pop(key, None)

        case "append":
            current = env.get(key, "")
            # 如果当前有值，则用分隔符连接；否则直接设为 val
            env[key] = f"{current}{sep}{val}" if current else val

        case "prepend":
            current = env.get(key, "")
            # 如果当前有值，则用分隔符连接；否则直接设为 val
            env[key] = f"{val}{sep}{current}" if current else val

    return env

def apply_env_actions(env: dict[str, str], ops: None | list[EnvAction], sep: str = os.pathsep) -> dict[str, str]:
    if not ops:
        return env

    for op in ops:
        apply_env_action(env, op, sep)

    return env