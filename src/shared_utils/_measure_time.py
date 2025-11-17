import time
from dataclasses import dataclass
from functools import wraps
from typing import Callable, TypeVar, Any

T = TypeVar("T")


def measure_time(
    func: Callable[..., T] | None = None,
    *,
    logger: Callable[[str], None] = print,
    message_fmt: str = "{func_name} exécutée en {duration}",
) -> Callable[..., T] | Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that measures the execution time of a function and prints a human-readable duration.

    The elapsed time is measured using time.perf_counter() and printed to stdout in the form:
        "<function_name> exécutée en <formatted_duration>"
    Optionally, you can pass a custom logger (e.g., logging.info) and message format string.

    Can be used with or without parentheses:
        @measure_time
        def my_function(): ...

        @measure_time(logger=custom_logger)
        def my_function(): ...

    Formatting rules for <formatted_duration>:
    - If elapsed >= 60 seconds:
        - Show minutes and seconds as integers (e.g. "2min 12s").
    - If 10s <= elapsed < 60s:
        - Show only integer seconds, e.g. "12s"
    - If elapsed < 10s:
        - Show seconds with 3 decimal places, e.g. "0.123s"

    Parameters
    ----------
    func : callable, optional
        The function to wrap and time. If None, returns a decorator.
    logger : callable, optional
        A function to output the timing message (default is print; e.g., logging.info).
    message_fmt : str, optional
        A format string for the timing message, with placeholders {func_name} and {duration}
        (default is "{func_name} exécutée en {duration}").

    Returns
    -------
    callable
        The decorated function that returns the original function's return value unchanged.

    Side effects
    --------
    - Prints a timing message to the provided logger.
    - Preserves the wrapped function's metadata (uses functools.wraps).

    Notes
    -----
    - Timing is done with time.perf_counter() for high resolution.
    - Exceptions raised by the wrapped function are propagated unchanged.
    """

    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            start = time.perf_counter()
            result = f(*args, **kwargs)
            elapsed = time.perf_counter() - start
            # format elapsed with rules:
            # - if elapsed >= 60s: show minutes and seconds (minutes integer)
            # - if 10s <= elapsed < 60s: show integer seconds (e.g. '12s')
            # - if elapsed < 10s: show seconds with 3 decimals (e.g. '0.123s')
            if elapsed >= 60:
                minutes = int(elapsed // 60)
                seconds = elapsed - minutes * 60
                sec_str = f"{int(seconds)}s"
                formatted = f"{minutes}min {sec_str}"
            elif elapsed >= 10:
                # show only integer seconds
                formatted = f"{int(elapsed)}s"
            else:
                # show up to 3 decimals for sub-10s durations
                formatted = f"{elapsed:.3f}s"
            logger(message_fmt.format(func_name=f.__name__, duration=formatted))
            return result

        return wrapper

    # Support for both @measure_time and @measure_time() syntax
    if func is None:
        return decorator
    else:
        return decorator(func)


if __name__ == "__main__":

    @dataclass
    class Produit:
        nom: str
        prix: float
        quantite: int = 1

        @measure_time
        def calcul_total(self):
            return self.prix * self.quantite

    p = Produit("Chaise", 49.99, 4)
    total = p.calcul_total()
    print(f"Total pour {p.quantite} {p.nom}(s) : {total:.2f} €")
