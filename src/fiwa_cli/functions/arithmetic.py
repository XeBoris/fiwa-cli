"""Mathematical expression evaluation utility for FiWa.

This module provides functions to evaluate mathematical expressions entered by users
when specifying prices and amounts in the application.

Functions:
    eval_math: Evaluate mathematical expressions or convert strings to floats
"""

try:
    import numexpr
except ImportError:
    numexpr = None


def eval_math(cost_string: str = None, init_char: str = "=") -> float:
    """Evaluate mathematical expressions or convert string numbers to float.
    
    This is a wrapper function for numexpr that handles typical use cases in FiWa
    when evaluating price strings and mathematical expressions. The function supports:
    
        - **None or empty strings**: Returns 0.0
        - **Expression starting with "="**: Evaluates the substring after "=" using numexpr
          Example: "=100+50*2" evaluates to 200.0
        - **Numeric strings**: Converts to float with comma-to-dot replacement
          Example: "123,45" converts to 123.45
    
    This enables users to:
        - Enter simple numbers: "100" → 100.0
        - Enter European-formatted numbers: "123,45" → 123.45
        - Enter mathematical expressions: "=20*5 + 10" → 110.0
        - Enter complex calculations: "=sqrt(100) + 5" → 15.0
    
    Args:
        cost_string (str, optional): A string representing a number or mathematical expression.
            If None or empty, returns 0.0.
            If starts with "=", the rest is evaluated as a math expression.
            Otherwise treated as a numeric string with optional comma decimal separator.
            Defaults to None.
        init_char (str, optional): The character that introduces a mathematical expression.
            Defaults to "=" (currently not used in implementation but provided for API flexibility).
    
    Returns:
        float: The evaluated result or converted number.
            Returns 0.0 if input is None or empty string.
            Returns the evaluated expression result if input starts with "=".
            Returns the converted float if input is a numeric string.
    
    Raises:
        SyntaxError: If the mathematical expression is invalid and numexpr fails.
        ValueError: If the string cannot be converted to float.
    
    Examples:
        >>> eval_math(None)
        0.0
        
        >>> eval_math("")
        0.0
        
        >>> eval_math("100")
        100.0
        
        >>> eval_math("123,45")
        123.45
        
        >>> eval_math("=50+25")
        75.0
        
        >>> eval_math("=100*2+50")
        250.0
        
        >>> eval_math("=sqrt(16)")
        4.0
        
        >>> eval_math("=10.5 * 2")
        21.0
    
    Notes:
        - For mathematical expressions, numexpr is used for safe evaluation
        - Supports standard arithmetic operators: +, -, *, /, **
        - Supports math functions: sqrt, sin, cos, tan, exp, log, etc.
        - Comma (,) is automatically replaced with period (.) for decimal separator
        - If numexpr is not installed, mathematical expressions will raise an ImportError
    
    See Also:
        - numexpr documentation: https://github.com/pydata/numexpr
        - Common math functions available in numexpr
    """
    # Handle None or empty string
    if cost_string is None or len(cost_string) == 0:
        return 0.0
    
    # Handle mathematical expressions starting with "="
    if cost_string[0] == init_char:
        if numexpr is None:
            raise ImportError(
                "numexpr is required for mathematical expression evaluation. "
                "Please install it with: pip install numexpr"
            )
        try:
            # Evaluate the expression after the "=" character
            result = numexpr.evaluate(cost_string[1:].replace(",", "."))
            # Extract scalar value from numpy result
            return float(result.item() if hasattr(result, 'item') else result)
        except (SyntaxError, TypeError, ValueError) as e:
            raise SyntaxError(
                f"Invalid mathematical expression: {cost_string[1:]}\n"
                f"Error details: {str(e)}\n"
                f"Examples of valid expressions: =100+50, =sqrt(100), =20*5+10"
            ) from e
    else:
        # Convert string number to float (handle comma as decimal separator)
        try:
            cost_string = cost_string.replace(",", ".")
            return float(cost_string)
        except ValueError as e:
            raise ValueError(
                f"Cannot convert '{cost_string}' to float. "
                f"Expected a number like '100' or '123.45' or '123,45'"
            ) from e

