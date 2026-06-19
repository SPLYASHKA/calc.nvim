from enum import Enum


# class ErrorCode(Enum):
#     STACK_UNDERFLOW = "stack_underflow"
#     INVALID_OPERATION = "invalid_operation"
#     DIVISION_BY_ZERO = "division_by_zero"

class CalculatorError(Exception):
    pass

class StackError(CalculatorError):
    pass

class StackUnderflowError(StackError):
    pass

class StackOperandError(StackError):
    pass

class SympyError(CalculatorError):
    pass
