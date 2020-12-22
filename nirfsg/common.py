"""Common definitions"""
from abc import ABC, abstractmethod
import nirfsg.c_api as c_api
from nirfsg.attributemonger import get_attributes


class niBase(ABC):
    """Base metaclass for NI device

    Parameters
    ----------
    instrument_handle : ViSession
    """

    @abstractmethod
    def __init__(self, instrument_handle):
        self._vi = instrument_handle
        self._attrs = {}

    @staticmethod
    def _ispublic(key):
        return not key.startswith("_")

    def __dir__(self):
        inst_attr = list(filter(self._ispublic, self.__dict__))
        cls_attr = list(filter(self._ispublic, dir(self.__class__)))
        ni_attr = list(filter(self._ispublic, self._attrs))
        return inst_attr + cls_attr + ni_attr

    def __getattr__(self, item):
        if item in self._attrs:
            attr = self._attrs[item]
            return attr.value
        return self.__dict__.get(item, None)

    def __setattr__(self, item, value):
        try:
            attrs = super().__getattribute__("_attrs")
        except AttributeError:
            super().__setattr__(item, value)
        else:
            if item in attrs:
                attr = attrs[item]
                attr.value = value
            else:
                super().__setattr__(item, value)

    @abstractmethod
    def __repr__(self):
        return "<niBase>"


class Subsystem(niBase):
    """Subsystem

    Parameters
    ----------
    owner : niBase
    """

    _kind = "subsystem"

    def __init__(self, owner):
        super().__init__(owner._vi)
        self._owner = owner

    def __init_subclass__(cls, kind):
        cls._kind = kind

    def __repr__(self):
        return f"<{self._owner} Subsystem:{self._kind}>"


class SignalGenerator(niBase):
    """Base class for signal generators

    Parameters
    ----------
    resource_name : str
        IVI logical name such as 'PXI1Slot1'
    reset_device : bool
    options : str
        driver optional setup such as 'Simulate=1,DriverSetup=Model:<model number>'

    Returns
    -------
    SignalGenerator
    """

    def __init__(self, resource_name, reset_device=False, driver_options=""):
        if driver_options == "":
            vi = c_api.init(resource_name, reset_device=reset_device)
        else:
            vi = c_api.init_withoptions(
                resource_name, reset_device=reset_device, options=driver_options
            )
        super().__init__(vi)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        c_api.close(self._vi)

    def __repr__(self):
        modelstr = c_api.get_instrument_model(self._vi)
        return f"<{modelstr}>"

    @abstractmethod
    def configure_rf(self, frequency, power):
        """Configure RF frequency and power

        Parameters
        ----------
        frequency : float in hertz
        power : float in dBm
        """

    def initiate(self):
        """Initiates signal generation"""
        c_api.initiate(self._vi)

    def check_status(self):
        """Check for completion of generation or errors during generation

        Returns
        -------
        done : bool
        """
        return c_api.check_generationstatus(self._vi)

    def abort(self):
        """Stop signal generation"""
        c_api.abort(self._vi)

    def close(self):
        """Stop signal generation and close driver session"""
        c_api.close(self._vi)

    def wait_until_settled(self):
        """Wait unit output is settled to new frequency/power setting"""
        c_api.waituntilsettled(self._vi)


class ConfigurationList(Subsystem, kind="configuration_list"):
    """Configuration list subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)
        self.lists = []

    def create(self, name, attributes):
        """Create a new configuration list

        Parameters
        ----------
        name : str
        attributes : List[str]
            {'rf_frequency', 'rf_power'}
        """
        viattrs = []
        for attr in attributes:
            viattrs.append(self._owner._attrs[attr].id)
        c_api.create_configurationlist(self._vi, name, viattrs)
        self.lists.append(name)

    def add_step(self):
        """Add a new step to the active configuration list"""
        c_api.create_configurationlist_step(self._vi)


class StartTrigger(Subsystem, kind="start_trigger"):
    """Start trigger subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)

    def __dir__(self):
        attrs = super().__dir__()
        trigtype = self.type
        trigtype_enum = type(trigtype)
        if trigtype == getattr(trigtype_enum, "none"):
            if "edge" in attrs:
                attrs.remove("edge")
            if "source" in attrs:
                attrs.remove("source")
        elif trigtype == getattr(trigtype_enum, "digital edge"):
            if "software" in attrs:
                attrs.remove("software")
        elif trigtype == getattr(trigtype_enum, "software"):
            if "digital edge" in attrs:
                attrs.remove("edge")
                attrs.remove("source")
        return attrs


class ConfigurationListTrigger(Subsystem, kind="configurationlist_trigger"):
    """Configuration List trigger subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)


class Events(Subsystem, kind="events"):
    """Events subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)


class ExternalCalibration(Subsystem, kind="external_cal"):
    """External calibration subsystem

    Parameters
    ----------
    owner : niBase
    """

    def __init__(self, owner):
        super().__init__(owner)
        self._attrs = get_attributes(self._vi, subsystem=self._kind)

    @property
    def date(self):
        """Last external calibration date

        Returns
        -------
        date : datetime
        """
        return c_api.get_lastexternalcaldatetime(self._vi)
