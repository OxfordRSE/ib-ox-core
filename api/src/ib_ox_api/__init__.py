from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("ib-ox-api")
except PackageNotFoundError as e:
    raise RuntimeError(
        "Package 'ib-ox-api' is not installed. "
        "Run 'pip install .' from the api/ directory."
    ) from e
