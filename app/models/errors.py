

class GBCError(Exception):
    """
    所有GBC异常的基类
    """

class ConfigError(GBCError):
    """
    所有配置文件相关的Error
    """

class ExecutorError(GBCError):
    """
    执行器模块的Error
    """

class GuaranteeError(GBCError):
    """
    和保证相关的Error
    """

class IllegalOperationError(GBCError):
    """
    非法操作，操作意图层面就是错误的
    """

# ======== Illegal Operation ========
class IllegalFilePathError(IllegalOperationError):
    """
    非法操作，操作意图层面就是错误的
    """
    def __init__(self, target_file):
        self.target_file = target_file

    def __str__(self):
        return f"Operation intended to '{self.target_file}' is illegal"

# ======== Config ========

class ConfigNotFoundError(ConfigError):
    def __init__(self, target_file):
        self.target_file = target_file

    def __str__(self):
        return f"Config file '{self.target_file}' not found"

class ConfigParseError(ConfigError):
    def __init__(self, target_file, failure_info):
        self.target_file = target_file
        self.failure_info = failure_info

    def __str__(self):
        return f"Config file '{self.target_file}' failed to parse: \n{self.failure_info}"

# ======== Project ========

class ProjectNotFoundError(GBCError):
    def __init__(self, target_project):
        self.target_project = target_project

    def __str__(self):
        return f"Project '{self.target_project}' not found"

# ======== Meta ========

class MetaNotFoundError(GBCError):
    def __init__(self, original_file, target_file):
        self.original_file = original_file
        self.target_file = target_file

    def __str__(self):
        return f"Meta file for '{self.original_file}' not found: '{self.target_file}'"

# ======== Guarantee ========

class GuaranteeNotFoundError(GuaranteeError):
    def __init__(self, target_file, guarantee_id):
        self.target_file = target_file
        self.guarantee_id = guarantee_id

    def __str__(self):
        return f"Guarantee '{self.guarantee_id}' not found for '{self.target_file}'"

class GuaranteeTestFailedError(GuaranteeError):
    def __init__(self, target_file, guarantee_id, failure_info):
        self.target_file = target_file
        self.guarantee_id = guarantee_id
        self.failure_info = failure_info

    def __str__(self):
        return f"Guarantee '{self.guarantee_id}' failed for '{self.target_file}', failure info: \n {self.failure_info}"

# ======== Executor ========

