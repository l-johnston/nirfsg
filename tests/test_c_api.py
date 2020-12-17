"""Test c_api"""
from nirfsg.c_api import init_withoptions, get_revisions, close

# pylint: disable=missing-function-docstring
def test_initwithoptions():
    vi = init_withoptions("PXI1Slot16", options="Simulate=1,DriverSetup=Model:5654")
    driver_rev, firmware_rev = get_revisions(vi)[:2]
    close(vi)
    assert driver_rev.startswith("Driver: NI-RFSG")
    assert firmware_rev.startswith("Not available")
