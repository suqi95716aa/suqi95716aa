
class Code:
    SUCCESS_REQUEST_CODE = 200  # 成功

    ERROR_PARAMS = 400  # 传入错误的参数
    ERROR_FORBIDDEN = 403   # 禁止访问
    ERROR_PARAMS_NOT_FOUND = 404    # 参数未找到
    ERROR_WRONG_TYPE_CONCAT = 405   # 将不同类型放入拼接
    ERROR_LOGIN_EXPIRED = 406   # 登录超时
    ERROR_ACCESS_ERROR = 407   # 登录失败

    ERROR_DB_EXISTS = 420   # 数据库对象已存在
    ERROR_DB_NOT_EXISTS = 421   # 数据库对象不存在
    ERROR_KB_EXISTS = 422   # 案件库对象已存在
    ERROR_KB_NOT_EXISTS = 423   # 案件库对象不存在
    ERROR_FILE_EXISTS = 424   # 文件对象存在
    ERROR_FILE_NOT_EXISTS = 425   # 文件对象不存在

    ERROR_PHONE_NOT_EXISTS = 447     # 手机号不存在
    ERROR_USER_NOT_EXISTS = 448     # 用户不存在
    ERROR_PHONE_EXISTS = 449     # 手机号已存在
    ERROR_USER_EXISTS = 450     # 用户已存在
    ERROR_USER_DATA_LENGTH = 451    # 用户数据长度超出限制
    ERROR_CODE_INVALID = 452    # 验证码无效
    ERROR_CODE_NOT_FOUND = 453  # 验证码未找到
    ERROR_CODE_COOLING = 454  # 验证码服务正在冷却中，请稍后再试

    ERROR_INTERNAL_SERVICE = 500    # 服务器内部错误


class Message:
    # System
    MESSAGE_INVALID_PARAMS = "Invalid parameters"
    MESSAGE_FORMAT_ERROR = "Format error"
    MESSAGE_DATA_LONG_ERROR = "Data long error"
    MESSAGE_PARAM_MISSING = "Params error"
    MESSAGE_SERVER_ERROR = "Server error"
    MESSAGE_DUPLICATE_ERROR = "Duplicate key error"
    MESSAGE_WRONG_TYPE_CONCAT_ERROR = "trying to merge on float or int and object columns for key"

    MESSAGE_OP_SUCCESS = "Operation success"
    MESSAGE_OP_FAIL = "Operation fail"

    # User
    MESSAGE_REGISTER_SUCCESS = "Register success"
    MESSAGE_REGISTER_ERROR = "Register fail, try again later"

    MESSAGE_USER_EXISTS = "User already exists"
    MESSAGE_USERNAME_EXISTS = "Username already exists"
    MESSAGE_PHONE_EXISTS = "Phone already exists"
    MESSAGE_BASE_EXISTS = "Base already exists"
    MESSAGE_FILE_EXISTS = "File exists"
    MESSAGE_USER_NOT_EXISTS = "User not exists"
    MESSAGE_USERNAME_NOT_EXISTS = "Username not exists"
    MESSAGE_PHONE_NOT_EXISTS = "Phone not exists"
    MESSAGE_BASE_NOT_EXISTS = "Base not exists"
    MESSAGE_CONFIG_NOT_FOUND_EXISTS = "Config not found exists"
    MESSAGE_FILE_NOT_FOUND_EXISTS = "File not exists"
    MESSAGE_SHEET_NOT_FOUND_EXISTS = "Sheetname not exists"
    MESSAGE_KNOWLEDGE_NOT_FOUND_EXISTS = "Knowledge not exists"
    MESSAGE_SCREEN_FOUND_EXISTS = "Screen exists"
    MESSAGE_SCREEN_NOT_FOUND_EXISTS = "Screen not exists"

    # Auth
    MESSAGE_CODE_VALID = "Valid code"
    MESSAGE_CODE_COOLING = "Cooling code"
    MESSAGE_CODE_NOT_FOUND_ERROR = "Code not found"
    MESSAGE_CODE_INVALID_ERROR = "Code invalid"

    MESSAGE_TOKEN_EXPIRED_ERROR = "Token expired"
    MESSAGE_TOKEN_INVALID_ERROR = "Token invalid"



