def fib(n: int) -> int:
    """Fibonacci example function"""
    if not n > 0:
        msg = f"{n} must be larger than 0!"
        raise RuntimeError(msg)
    a, b = 1, 1
    for _ in range(n - 1):
        a, b = b, a + b
    return a
