"""NI-RFSG attributemonger"""
from functools import wraps
from pathlib import Path
from enum import Enum
from datetime import timedelta
import copy
from nirfsg import c_api


class Attribute:
    """Attribute"""

    def __init__(
        self,
        c_api_name,
        attr_id,
        c_type,
        subsystem,
        name,
        supported_models,
        defined_values,
    ):
        self.c_api_name = c_api_name
        self.id = attr_id
        self.c_type = c_type
        self.subsystem = subsystem
        self.name = name
        self.supported_models = supported_models
        self.defined_values = defined_values
        self._vi = None
        self._channel = None
        self._get = c_api.GETLU[c_type]
        self._set = c_api.SETLU[c_type]

    @property
    def value(self):
        """Value of the attribute"""
        value = self._get(self._vi, self._channel, self.id)
        if self.defined_values is not None:
            value = self.defined_values(value)
        elif self.c_type == c_api.ViBoolean:
            value = bool(value)
        elif self.c_api_name == "NIRFSG_ATTR_EXTERNAL_CALIBRATION_RECOMMENDED_INTERVAL":
            value = timedelta(days=value / 12 * 365)
        elif self.c_api_name == "NIRFSG_ATTR_AUTOMATIC_THERMAL_CORRECTION":
            value = bool(value)
        return value

    @value.setter
    def value(self, new_value):
        if self.defined_values is not None:
            new_value = getattr(self.defined_values, new_value, new_value)
            if hasattr(new_value, "value"):
                new_value = new_value.value
        self._set(self._vi, self._channel, self.id, new_value)

    def __eq__(self, other):
        return self.id == other.id


class SupportedModels(list):
    """list of supported models for a given attribute

    Parameters
    ----------
    models : list of str
        model names such as PXIe-5654

    When the list contains 'all', a test for `in` returns True.
    """

    def __contains__(self, value):
        if super().__contains__("all"):
            return True
        for model in self:
            if model in value:
                return True
        return False


def singleton(cls):
    """Decorator to create a singleton class"""

    @wraps(cls)
    def wrapped(*args, **kwargs):
        if wrapped.inst is None:
            wrapped.inst = cls(*args, **kwargs)
        return wrapped.inst

    wrapped.inst = None
    return wrapped


@singleton
class AttributeMonger:
    """Get attributes for given model

    Parameters
    ----------
    instrument_handle : ViSession

    Returns
    -------
    attributes : dict
    """

    def __init__(self):
        self._attributes = {}
        self._readtable()

    def _readtable(self):
        with open(Path(__file__).parent / "attribute_table.csv") as file:
            for line in file.readlines():
                tokens = line.strip().split(",")
                if not tokens[0].startswith("NIRFSG") or tokens[3] == "":
                    continue
                c_api_name = tokens[0]
                attr_id = int(tokens[1])
                c_type = getattr(c_api, tokens[2])
                name = tokens[3]
                subsystem = tokens[4]
                i = 6
                cnt = int(tokens[i - 1])
                supmods = SupportedModels(tokens[i : i + cnt])
                i = i + cnt + 1
                cnt = int(tokens[i - 1]) if tokens[i - 1] != "" else 0
                defvals = []
                if cnt > 0:
                    for cn, v in zip(
                        tokens[i : i + 2 * cnt + 1 : 2],
                        tokens[i + 1 : i + 1 + 2 * cnt : 2],
                    ):
                        n = (
                            cn.split("_VAL_")[-1]
                            .replace("_", " ")
                            .replace(" STR", "")
                            .lower()
                        )
                        v = int(v) if v.isdecimal() else v
                        defvals.append([n, v])
                defvals = Enum(name, defvals) if len(defvals) > 0 else None
                self._attributes[name] = Attribute(
                    c_api_name, attr_id, c_type, subsystem, name, supmods, defvals
                )

    def __call__(self, instrument_handle, subsystem, channel=""):
        model = c_api.get_attribute_string(
            instrument_handle, "", c_api.NIRFSG_ATTR_INSTRUMENT_MODEL
        )
        attrs = {}
        for name, attr in self._attributes.items():
            if model in attr.supported_models and subsystem == attr.subsystem:
                attr._vi = instrument_handle
                attr._channel = channel
                attrs[name] = attr
        return copy.deepcopy(attrs)


get_attributes = AttributeMonger()
