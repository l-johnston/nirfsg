"""Python binding to NI-RFSG"""
import os
import sys
import pathlib
from functools import wraps
from ctypes import (
    cdll,
    c_int32,
    c_uint16,
    c_uint32,
    c_char_p,
    POINTER,
    byref,
    create_string_buffer,
    c_double,
    c_int64,
)
from datetime import datetime

if sys.maxsize > 2 ** 32:
    dllpath = (
        pathlib.Path(os.getenv("PROGRAMFILES")) / "IVI Foundation/IVI/Bin/niRFSG_64.dll"
    )
else:
    dllpath = (
        pathlib.Path(os.getenv("PROGRAMFILES(X86)"))
        / "IVI Foundation/IVI/Bin/niRFSG.dll"
    )
nirfsgdll = cdll.LoadLibrary(str(dllpath))


def c_api(*args):
    """Decorator to retrieve the c-function from the dll

    Assigns the c-function to the 'call' attribute of the decorated Python function.

    Parameters
    ----------
    args : tuple containing
        function_name : str
        argtypes : tuple of ctypes
        restype : ctype, optional
    """

    def outer(py_function):
        function_name = args[0]
        argtypes = args[1]
        try:
            restype = args[2]
        except IndexError:
            restype = None
        c_function = getattr(nirfsgdll, function_name)
        if not isinstance(argtypes, (tuple, list)):
            argtypes = (argtypes,)
        c_function.argtypes = argtypes
        if restype is not None:
            c_function.restype = restype

        @wraps(py_function)
        def inner(*args, **kwargs):
            return py_function(*args, **kwargs)

        inner.call = c_function
        return inner

    return outer


ViStatus = c_int32
ViRsrc = c_char_p
ViBoolean = c_uint16
pViBoolean = POINTER(ViBoolean)
ViSession = c_uint32
ViInt32 = c_int32
pViInt32 = POINTER(ViInt32)
ViInt64 = c_int64
pViInt64 = POINTER(ViInt64)
ViAttr = c_uint32
pViAttr = POINTER(ViAttr)
ViReal64 = c_double
pViReal64 = POINTER(ViReal64)
ViString = c_char_p
ViConstString = c_char_p  # constant
IVI_MAX_MESSAGE_LEN = 255
IVI_MAX_MESSAGE_BUF_SIZE = IVI_MAX_MESSAGE_LEN + 1
NIRFSG_ATTR_INSTRUMENT_MODEL = 1050512  # ViString
NIRFSG_ATTR_FREQUENCY = 1250001  # ViReal64
NIRFSG_ATTR_POWER_LEVEL = 1250002  # ViReal64
NIRFSG_ATTR_OUTPUT_ENABLED = 1250004  # ViBoolean


class niRFSGError(Exception):
    """Exception raised upon error in NI-RFSG"""


@c_api(
    "niRFSG_GetError",
    (ViSession, POINTER(ViStatus), ViInt32, c_char_p),
    ViStatus,
)
def get_error(instrument_handle, error):
    """Get error info from error code

    Parameters
    ----------
    instrument_handle : ViSession
    error : int

    Returns
    -------
    err_msg : str
    """
    error = ViStatus(error)
    err_buf = create_string_buffer(IVI_MAX_MESSAGE_BUF_SIZE)
    err = get_error.call(instrument_handle, byref(error), IVI_MAX_MESSAGE_LEN, err_buf)
    if err != 0:
        raise niRFSGError(f"{err}")
    return err_buf.value.decode()


def check_error(func):
    """Decorator to check for error during c_api call"""

    @wraps(func)
    def inner(*args, **kwargs):
        # result is always a list of at least [error_code]
        result = func(*args, **kwargs)
        err = result.pop()
        if err:
            # assuming instrument_handle is arg[0]
            err_msg = get_error(args[0], err)
            raise niRFSGError(err_msg)
        if (n := len(result)) == 0:
            result = None
        elif n == 1:
            result = result[0]
        return result

    return inner


@c_api("niRFSG_init", (ViRsrc, ViBoolean, ViBoolean, POINTER(ViSession)), ViStatus)
def init(resource_name, query_id=True, reset_device=False):
    """Initialize a session

    Parameters
    ----------
    resource_name : str
        device to initialize, e.g. 'PXI1Slot1'
    query_id : bool
        whether to query the device's ID
    reset_device : bool
        whether to reset the device

    Returns
    -------
    instrument_handle : ViSession
    """
    resource_name = resource_name.encode()
    instrument_handle = ViSession(0)
    err = init.call(resource_name, query_id, reset_device, byref(instrument_handle))
    if err:
        err_msg = get_error(ViSession(0), err)
        raise niRFSGError(f"{err_msg}")
    return instrument_handle


@c_api(
    "niRFSG_InitWithOptions",
    (ViRsrc, ViBoolean, ViBoolean, c_char_p, POINTER(ViSession)),
    ViStatus,
)
def init_withoptions(resource_name, query_id=True, reset_device=False, options=""):
    """Initialize a session with options

    Parameters
    ----------
    resource_name : str
        device to initialize, e.g. 'PXI1Slot1'
    query_id : bool
        whether to query the device's ID
    reset_device : bool
        whether to reset the device
    options : str
        driver setup options such as 'Simulate=1,DriverSetup=Model:5654'

    Returns
    -------
    instrument_handle : ViSession
    """
    resource_name = resource_name.encode()
    instrument_handle = ViSession(0)
    options = options.encode()
    err = init_withoptions.call(
        resource_name, query_id, reset_device, options, byref(instrument_handle)
    )
    if err:
        err_msg = get_error(ViSession(0), err)
        raise niRFSGError(f"{err_msg}")
    return instrument_handle


@check_error
@c_api("niRFSG_close", (ViSession,), ViStatus)
def close(instrument_handle):
    """Close session

    Parameters
    ----------
    instrument_session : ViSession
    """
    err = close.call(instrument_handle)
    return [err]


@check_error
@c_api("niRFSG_ConfigureRF", (ViSession, ViReal64, ViReal64), ViStatus)
def configure_rf(instrument_handle, frequency, power):
    """Configure basic RF attributes

    Parameters
    ----------
    instrument_handle : ViSession
    frequency : float in hertz
    power : float in decibel_milliwatt
    """
    err = configure_rf.call(instrument_handle, frequency, power)
    return [err]


@check_error
@c_api("niRFSG_Initiate", (ViSession,), ViStatus)
def initiate(instrument_handle):
    """Initiate generation

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = initiate.call(instrument_handle)
    return [err]


@check_error
@c_api("niRFSG_Abort", (ViSession,), ViStatus)
def abort(instrument_handle):
    """Stop generation

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = abort.call(instrument_handle)
    return [err]


@check_error
@c_api(
    "niRFSG_GetExternalCalibrationLastDateAndTime",
    (ViSession, *map(POINTER, [ViInt32] * 6)),
    ViStatus,
)
def get_lastexternalcaldatetime(instrument_handle):
    """Get the date and time of the last external calibration

    Parameters
    ----------
    instrument_handle : ViSession

    Returns
    -------
    datetime.datetime
    """
    values = [ViInt32() for _ in range(6)]
    err = get_lastexternalcaldatetime.call(instrument_handle, *map(byref, values))
    values = [v.value for v in values]
    return [datetime(*values), err]


@check_error
@c_api(
    "niRFSG_GetAttributeViReal64",
    (ViSession, ViConstString, ViAttr, pViReal64),
    ViStatus,
)
def get_attribute_float(instrument_handle, channel, viattr):
    """Get float attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr

    Returns
    -------
    value : float
    """
    channel = ViConstString(channel.encode())
    value = ViReal64()
    err = get_attribute_float.call(instrument_handle, channel, viattr, byref(value))
    return [value.value, err]


@check_error
@c_api(
    "niRFSG_GetAttributeViString",
    (ViSession, c_char_p, ViAttr, ViInt32, c_char_p),
    ViStatus,
)
def get_attribute_string(instrument_handle, channel, viattr):
    """Get string attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr

    Returns
    -------
    value : float
    """
    channel = ViConstString(channel.encode())
    value = create_string_buffer(IVI_MAX_MESSAGE_BUF_SIZE)
    err = get_attribute_string.call(
        instrument_handle, channel, viattr, IVI_MAX_MESSAGE_BUF_SIZE, value
    )
    return [value.value.decode(), err]


@check_error
@c_api(
    "niRFSG_GetAttributeViBoolean", (ViSession, c_char_p, ViAttr, pViBoolean), ViStatus
)
def get_attribute_bool(instrument_handle, channel, viattr):
    """Get the boolean attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr

    Returns
    -------
    value : bool
    """
    channel = ViConstString(channel.encode())
    value = ViBoolean()
    err = get_attribute_bool.call(instrument_handle, channel, viattr, byref(value))
    return [value.value, err]


@check_error
@c_api("niRFSG_GetAttributeViInt32", (ViSession, c_char_p, ViAttr, pViInt32), ViStatus)
def get_attribute_int32(instrument_handle, channel, viattr):
    """Get the integer attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr

    Returns
    -------
    value : int
    """
    channel = ViConstString(channel.encode())
    value = ViInt32()
    err = get_attribute_int32.call(instrument_handle, channel, viattr, byref(value))
    return [value.value, err]


@check_error
@c_api("niRFSG_GetAttributeViInt64", (ViSession, c_char_p, ViAttr, pViInt64), ViStatus)
def get_attribute_int64(instrument_handle, channel, viattr):
    """Get the integer attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr

    Returns
    -------
    value : int
    """
    channel = ViConstString(channel.encode())
    value = ViInt64()
    err = get_attribute_int64.call(instrument_handle, channel, viattr, byref(value))
    return [value.value, err]


def get_instrument_model(instrument_handle):
    """Get instrument model

    Parameters
    ----------
    instrument_handle : ViSession

    Returns
    -------
    model : str
    """
    return get_attribute_string(instrument_handle, "", NIRFSG_ATTR_INSTRUMENT_MODEL)


@check_error
@c_api(
    "niRFSG_SetAttributeViReal64",
    (ViSession, ViConstString, ViAttr, ViReal64),
    ViStatus,
)
def set_attribute_float(instrument_handle, channel, viattr, value):
    """Set float attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr
    value : float
    """
    channel = ViConstString(channel.encode())
    err = set_attribute_float.call(instrument_handle, channel, viattr, value)
    return [err]


@check_error
@c_api(
    "niRFSG_SetAttributeViString",
    (ViSession, c_char_p, ViAttr, c_char_p),
    ViStatus,
)
def set_attribute_string(instrument_handle, channel, viattr, value):
    """Set string attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr
    value : str
    """
    channel = ViConstString(channel.encode())
    value = ViConstString(value.encode())
    err = set_attribute_string.call(instrument_handle, channel, viattr, value)
    return [err]


@check_error
@c_api(
    "niRFSG_SetAttributeViBoolean", (ViSession, c_char_p, ViAttr, ViBoolean), ViStatus
)
def set_attribute_bool(instrument_handle, channel, viattr, value):
    """Set the boolean attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr
    value : bool
    """
    channel = ViConstString(channel.encode())
    err = set_attribute_bool.call(instrument_handle, channel, viattr, value)
    return [err]


@check_error
@c_api("niRFSG_SetAttributeViInt32", (ViSession, c_char_p, ViAttr, ViInt32), ViStatus)
def set_attribute_int32(instrument_handle, channel, viattr, value):
    """Set the integer attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr
    value : int
    """
    channel = ViConstString(channel.encode())
    err = set_attribute_int32.call(instrument_handle, channel, viattr, value)
    return [err]


@check_error
@c_api("niRFSG_SetAttributeViInt64", (ViSession, c_char_p, ViAttr, ViInt64), ViStatus)
def set_attribute_int64(instrument_handle, channel, viattr, value):
    """Set the integer attribute for given channel

    Parameters
    ----------
    instrument_handle : ViSession
    channel : str
    viattr : ViAttr
    value : int
    """
    channel = ViConstString(channel.encode())
    err = set_attribute_int32.call(instrument_handle, channel, viattr, value)
    return [err]


GETLU = {
    ViReal64: get_attribute_float,
    ViString: get_attribute_string,
    ViBoolean: get_attribute_bool,
    ViInt32: get_attribute_int32,
    ViInt64: get_attribute_int64,
}
SETLU = {
    ViReal64: set_attribute_float,
    ViString: set_attribute_string,
    ViBoolean: set_attribute_bool,
    ViInt32: set_attribute_int32,
    ViInt64: set_attribute_int64,
}


@check_error
@c_api("niRFSG_GetChannelName", (ViSession, ViInt32, ViInt32, c_char_p))
def get_channelname(instrument_handle, index):
    """Get channel name for index

    Parameters
    ----------
    instrument_handle : ViSession
    index : int

    Returns
    -------
    name : str
    """
    name = create_string_buffer(IVI_MAX_MESSAGE_BUF_SIZE)
    err = get_channelname.call(instrument_handle, index, IVI_MAX_MESSAGE_LEN, name)
    return [name.value.decode(), err]


@check_error
@c_api("niRFSG_CheckGenerationStatus", (ViSession, POINTER(ViBoolean)), ViStatus)
def check_generationstatus(instrument_handle):
    """Check the generation status

    Parameters
    ----------
    instrument_handle : ViSession

    Returns
    -------
    isdone : bool
    """
    isdone = ViBoolean()
    err = check_generationstatus.call(instrument_handle, byref(isdone))
    return [bool(isdone.value), err]


@check_error
@c_api("niRFSG_revision_query", (ViSession, c_char_p, c_char_p), ViStatus)
def get_revisions(instrument_handle):
    """Get RFSG driver revision and device firmware revision

    Parameters
    ----------
    instrument_handle : ViSession

    Returns
    -------
    driver_revision : str
    firmware_revision : str
    """
    driver_revision = create_string_buffer(IVI_MAX_MESSAGE_BUF_SIZE)
    firmware_revision = create_string_buffer(IVI_MAX_MESSAGE_BUF_SIZE)
    err = get_revisions.call(instrument_handle, driver_revision, firmware_revision)
    driver_revision = driver_revision.value.decode()
    firmware_revision = firmware_revision.value.decode()
    return [driver_revision, firmware_revision, err]


@check_error
@c_api("niRFSG_Commit", (ViSession,), ViStatus)
def commit(instrument_handle):
    """Commit session

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = commit.call(instrument_handle)
    return [err]


@check_error
@c_api("niRFSG_WaitUntilSettled", (ViSession, ViInt32), ViStatus)
def waituntilsettled(instrument_handle, maxwait=10000):
    """Wait until settled

    Parameters
    ----------
    instrument_handle : ViSession
    maxwait : int in millisecond
    """
    err = waituntilsettled.call(instrument_handle, maxwait)
    return [err]


@check_error
@c_api("niRFSG_ConfigureOutputEnabled", (ViSession, ViBoolean), ViStatus)
def set_outputenabled(instrument_handle, value=False):
    """Set output enabled state

    Parameters
    ----------
    instrument_handle : ViSession
    value : bool
        If True, output is enabled, else output is disabled
    """
    err = set_outputenabled.call(instrument_handle, value)
    return [err]


@check_error
@c_api("niRFSG_reset", (ViSession,), ViStatus)
def reset(instrument_handle):
    """Reset all properties to their default values

    Also, move the NI-RFSG device to the Configuration state.

    Notes
    -----
    On PXIe-5654, this function doesn't actually work and even causes `close`
    to continue generating.

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = reset.call(instrument_handle)
    return [err]


@check_error
@c_api("niRFSG_reset", (ViSession,), ViStatus)
def resetdevice(instrument_handle):
    """Perform a hard reset on the device

    Notes
    -----
    On PXIe-5654, this function doesn't actually work and even causes `close`
    to continue generating.

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = reset.call(instrument_handle)
    return [err]


@check_error
@c_api(
    "niRFSG_CreateConfigurationList",
    (ViSession, ViConstString, ViInt32, pViAttr, ViBoolean),
    ViStatus,
)
def create_configurationlist(instrument_handle, name, attributes):
    """Create a new configuration list and set as active list

    Parameters
    ----------
    instrument_handle : ViSession
    name : str
    attributes : List[ViAttr]
    """
    name = ViConstString(name.encode())
    attrarraytype = ViAttr * len(attributes)
    attrarray = attrarraytype(*attributes)
    err = create_configurationlist.call(
        instrument_handle, name, len(attributes), attrarray, True
    )
    return [err]


@check_error
@c_api("niRFSG_CreateConfigurationListStep", (ViSession, ViBoolean), ViStatus)
def create_configurationlist_step(instrument_handle):
    """Create a new step and set as active step

    Parameters
    ----------
    instrument_handle : ViSession
    """
    err = create_configurationlist_step.call(instrument_handle, True)
    return [err]
