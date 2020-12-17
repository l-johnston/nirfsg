"""Python control of NI RF Signal Generators using NI-RFSG"""
from nirfsg.version import __version__
from nirfsg.pxie_5654 import PXIe_5654

__all__ = ["__version__", "PXIe_5654"]


def __dir__():
    return __all__
