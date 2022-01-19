"""PXIe-5654 20 GHz analog signal generator"""
import nirfsg.c_api as c_api
from nirfsg.common import (
    SignalGenerator,
    Subsystem,
    ConfigurationList,
    StartTrigger,
    ConfigurationListTrigger,
    Events,
    ExternalCalibration,
)
from nirfsg.attributemonger import get_attributes


class PXIe_5654(SignalGenerator):
    """PXIe-5654 20 GHz analog signal generator

    Parameters
    ----------
    resource_name : str
        IVI logical name such as 'PXI1Slot1'
    reset_device : bool
        whether to restore attributes to factory default values
    options : str
        driver optional setup such as 'Simulate=1,DriverSetup=Model:<model number>'

    Returns
    -------
    PXIe_5654
    """

    def __init__(self, resource_name, reset_device=False, driver_options=""):
        super().__init__(resource_name, reset_device, driver_options)
        self._attrs = get_attributes(self._vi, subsystem="model")
        self._attrs.update(get_attributes(self._vi, subsystem="channel"))
        self._channel = ""
        self.modulation = AnalogModulation(self)
        self.clock = RefClock(self)
        self.configurationlist = ConfigurationList(self)
        self.triggers = Triggers(self)
        self.events = Events(self)
        self.external_cal = ExternalCalibration(self)

    def configure_rf(self, frequency, power):
        """Configure RF frequency and power

        Parameters
        ----------
        frequency : float in hertz
        power : float in dBm
        """
        c_api.configure_rf(self._vi, frequency, power)


class AnalogModulation(Subsystem, kind="analog_modulation"):
    """Analog modulation subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)

    def __dir__(self):
        attrs = super().__dir__()
        mode = self.mode
        mode_enum = type(mode)
        attrs_copy = attrs.copy()
        if mode == getattr(mode_enum, "none"):
            for attr in attrs_copy:
                if (
                    attr.startswith("am")
                    or attr.startswith("fm")
                    or attr.startswith("pm")
                ):
                    attrs.remove(attr)
        elif mode == getattr(mode_enum, "am"):
            for attr in attrs_copy:
                if attr.startswith("fm") or attr.startswith("pm"):
                    attrs.remove(attr)
        elif mode == getattr(mode_enum, "fm"):
            for attr in attrs_copy:
                if attr.startswith("am") or attr.startswith("pm"):
                    attrs.remove(attr)
        elif mode == getattr(mode_enum, "pm"):
            for attr in attrs_copy:
                if attr.startswith("am") or attr.startswith("fm"):
                    attrs.remove(attr)
        return attrs


class RefClock(Subsystem, kind="clock"):
    """Reference clock subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)


class Triggers(Subsystem, kind="triggers"):
    """Triggers subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self.start_trigger = StartTrigger5654(self)
        self.configurationlist_trigger = ConfigurationListTrigger(self)


class StartTrigger5654(StartTrigger, kind="start_trigger"):
    """Start trigger for PXIe-5654"""

    def __dir__(self):
        attrs = super().__dir__()
        if "software" in attrs:
            attrs.remove("software")
        return attrs
