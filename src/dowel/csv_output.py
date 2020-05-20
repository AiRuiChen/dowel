"""A `dowel.logger.LogOutput` for CSV files."""
import csv
import warnings
import os
import tempfile

from dowel import TabularInput
from dowel.simple_outputs import FileOutput
from dowel.utils import colorize


class CsvOutput(FileOutput):
    """CSV file output for logger.

    :param file_name: The file this output should log to.
    """

    def __init__(self, file_name):
        super().__init__(file_name)
        self._file_name = file_name
        self._writer = None
        self._fieldnames = None
        self._warned_once = set()
        self._disable_warnings = False

    @property
    def types_accepted(self):
        """Accept TabularInput objects only."""
        return (TabularInput, )

    def record(self, data, prefix=''):
        """Log tabular data to CSV."""
        if isinstance(data, TabularInput):
            to_csv = data.as_primitive_dict

            if not to_csv.keys() and not self._writer:
                return

            if not self._writer:
                self._fieldnames = set(to_csv.keys())
                self._writer = csv.DictWriter(
                    self._log_file,
                    fieldnames=self._fieldnames,
                    extrasaction='ignore')
                self._writer.writeheader()

            # add new keys to _fieldnames set
            old_header_size = len(self._fieldnames)
            for key in to_csv.keys():
                self._fieldnames.add(key)

            # if new keys are added, rewrite the csv file
            if len(self._fieldnames) > old_header_size:
                self._writer = csv.DictWriter(
                    self._log_file,
                    fieldnames=sorted(list(self._fieldnames)),
                    extrasaction='ignore')

                self._log_file.seek(0)
                self._writer.writeheader()

                with open(self._file_name, 'r') as old_file:
                    reader = csv.DictReader(old_file)
                    for row in reader:
                        self._writer.writerow(row)

            self._writer.writerow(to_csv)

            for k in to_csv.keys():
                data.mark(k)
        else:
            raise ValueError('Unacceptable type.')

    def _warn(self, msg):
        """Warns the user using warnings.warn.

        The stacklevel parameter needs to be 3 to ensure the call to logger.log
        is the one printed.
        """
        if not self._disable_warnings and msg not in self._warned_once:
            warnings.warn(
                colorize(msg, 'yellow'), CsvOutputWarning, stacklevel=3)
        self._warned_once.add(msg)
        return msg

    def disable_warnings(self):
        """Disable logger warnings for testing."""
        self._disable_warnings = True


class CsvOutputWarning(UserWarning):
    """Warning class for CsvOutput."""

    pass
