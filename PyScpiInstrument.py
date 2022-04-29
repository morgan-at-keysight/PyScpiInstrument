"""
Wrapper around OpenTap's GenericScpiInstrument for Python instruments.
"""

from tokenize import Single

from numpy import uint64
import clr
import os
import sys

from PythonTap import *

# TAP_PATH = "~/.tap"
# sys.path.append(TAP_PATH)
# sys.path.append(os.path.join(TAP_PATH, "Packages", "OpenTAP"))

clr.AddReference("OpenTap")
clr.AddReference("System")

from System.Diagnostics import *
from System.Collections.Generic import List
from System import Single, Double, UInt64, Int64, UInt32, Int32, String, Array, Boolean
from System.ComponentModel import BrowsableAttribute

import OpenTap
from OpenTap.Plugins.BasicSteps import GenericScpiInstrument


@Attribute(OpenTap.DisplayAttribute, "Python SCPI Instrument", "Generic SCPI Instrument for Python", "Python")
class PyScpiInstrument(Instrument):
    """
    Base class for Python SCPI instrument plugins.
    """

    def __init__(self):
        """
        Construct the PyScpiInstrument instance.
        :param name: name of the instrument.
        """
        super(PyScpiInstrument, self).__init__()  # Invoke the base class initializer

        self._io = GenericScpiInstrument()
        self.Name = "PySCPI"

        address = self.AddProperty("visa_address", "TCPIP0::127.0.0.1::hislip0::INSTR", String)
        address.AddAttribute(OpenTap.DisplayAttribute, "VISA Address", "VISA address of connection to instrument.",
                             Groups=["VISA"])
        address.AddAttribute(OpenTap.VisaAddressAttribute)

        timeout = self.AddProperty("io_timeout", 5000, Int32)
        timeout.AddAttribute(OpenTap.UnitAttribute, "s", PreScaling=1000, UseEngineeringPrefix=False)
        timeout.AddAttribute(OpenTap.DisplayAttribute, "IO Timeout",
                             "Timeout (s) of connection used by underlying VISA driver")

    def Open(self):
        self._io.VisaAddress = self.visa_address
        self._io.IoTimeout = self.io_timeout
        self._io.Open()
        self.Info("{} IO session opened.".format(self.Name))

    def Close(self):
        self.Info("Closing {} IO session.".format(self.Name))
        self._io.Close()

    def ScpiQuery(self, query: str, verbose: bool = True):
        """
        Send the SCPI query string and wait for a response.
        :param query: Query string
        :param verbose: Flag for enabling/suppressing log messages.
        :return: SCPI response string.
        """
        return self._io.ScpiQuery(query, not verbose)

    def ScpiCommand(self, command: str):
        """
        Send a SCPI command to the instrument.
        :param command: SCPI command string.
        :return: None
        """
        return self._io.ScpiCommand(command)

    def QueryBinaryValues(self, query: str, datatype: str):
        """
        Send a SCPI query to the instrument and read back resulting data 
        in binary block format
        :param query: SCPI query string.
        """

        if datatype == 'b':
            return self._io.ScpiQueryBlock(query)
        elif datatype == 'B':
            return self._io.ScpiQueryBlock(query)
        elif datatype == 'f':
            return self._io.ScpiQueryBlock[Single](query)
        elif datatype == 'd':
            return self._io.ScpiQueryBlock[Double](query)
        else:
            raise TypeError('Invalid data type selected.')

    def WriteBinaryValues(self, command: str, data):
        """
        Sends a SCPI command with a binary block payload.
        :param command: SCPI command string
        :param data: binary data to be sent in the SCPI command
        """

        maxSize = 1e9
        self._io.ScpiIEEEBlockCommand(command, data)

    def QueryErrors(self, verbose: bool = True, max_errors: int = 1000):
        """
        Return all errors on the instrument error stack. Clear the list in the same call.
        :param verbose: Flag for suppressing log messages. If false the errors will not be logged.
        :param max_errors: Max number of errors to retrieve. Useful if instrument generates errors faster than they can be read.
        :return: List of all errors on the instrument error stack.
        """
        scpi_errors = self._io.QueryErrors(not verbose, max_errors)
        # OpenTap.ScpiInstrument.QueryErrors returns a list of OpenTap.ScpiInstrument.ScpiErrors
        # ScpiErrors have an int error code and string message
        # Concatenate all the strings together to return something that can be consumed by TestStep.Error
        return ','.join(["{} - {}".format(err.Code, err.Message) for err in scpi_errors])

    def WaitForOperationComplete(self, timeout_ms: int = 5000):
        """
        Waits for all previously executed SCPI commands to complete.
        :param timeout_ms:
        :return: None
        """
        return self._io.WaitForOperationComplete(timeout_ms)

    def Reset(self):
        """
        Abort the currently running measurement and makes the default measurement active.
        Gets the mode to a consistent state with all of the default couplings set.
        :return: None
        """
        return self._io.Reset()
