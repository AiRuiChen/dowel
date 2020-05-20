import csv
import tempfile

import pytest

from dowel import CsvOutput, TabularInput
from dowel.csv_output import CsvOutputWarning


class TestCsvOutput:

    def setup_method(self):
        self.log_file = tempfile.NamedTemporaryFile()
        self.csv_output = CsvOutput(self.log_file.name)
        self.tabular = TabularInput()
        self.tabular.clear()

    def teardown_method(self):
        self.log_file.close()

    def test_record(self):
        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.tabular.record('bar', bar)
        self.csv_output.record(self.tabular)
        self.tabular.record('foo', foo * 2)
        self.tabular.record('bar', bar * 2)
        self.csv_output.record(self.tabular)
        self.csv_output.dump()

        correct = [
            {'foo': str(foo), 'bar': str(bar)},
            {'foo': str(foo * 2), 'bar': str(bar * 2)},
        ]  # yapf: disable
        self.assert_csv_matches(correct)

    # Test if adding keys expands header and adds empty cells in previous rows
    def test_record_inconsistent_add_keys_same_row_size(self):
        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.csv_output.record(self.tabular)
        self.tabular.clear()
        self.tabular.record('bar', bar)
        self.csv_output.record(self.tabular)

        self.csv_output.dump()

        correct = [
            {'foo': str(foo), 'bar': ''},
            {'foo': '', 'bar': str(bar)},
        ]  # yapf: disable
        self.assert_csv_matches(correct)

    # Test if adding keys expands header and adds empty cells in previous rows
    def test_record_inconsistent_add_keys_diff_row_size(self):
        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.csv_output.record(self.tabular)
        self.tabular.clear()
        self.tabular.record('bar', bar)
        self.tabular.record('new1', 1)
        self.csv_output.record(self.tabular)
        self.tabular.clear()
        self.tabular.record('bar', bar)
        self.tabular.record('new1', 1)
        self.tabular.record('new2', 2)
        self.csv_output.record(self.tabular)
        self.tabular.clear()

        self.csv_output.dump()

        correct = [
            {'foo': str(foo), 'bar': '', 'new1': '', 'new2': ''},
            {'foo': '', 'bar': str(bar), 'new1': '1', 'new2': ''},
            {'foo': '', 'bar': str(bar), 'new1': '1', 'new2': '2'}
        ]  # yapf: disable
        self.assert_csv_matches(correct)

    # Test if removing keys leaves empty cells in future rows
    def test_record_inconsistent_remove_keys(self):
        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.tabular.record('bar', bar)
        self.tabular.record('to_remove', foo)
        self.csv_output.record(self.tabular)
        self.tabular.clear()
        self.tabular.record('bar', bar)
        self.tabular.record('foo', foo * 2)

        # this should not produce a warning, because we only warn once
        self.csv_output.record(self.tabular)

        self.csv_output.dump()

        correct = [
            {'foo': str(foo), 'bar': str(bar), 'to_remove': str(foo)},
            {'foo': str(foo * 2), 'bar': str(bar), 'to_remove': ''},
        ]  # yapf: disable
        self.assert_csv_matches(correct)


    def test_empty_record(self):
        self.csv_output.record(self.tabular)
        assert not self.csv_output._writer

        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.tabular.record('bar', bar)
        self.csv_output.record(self.tabular)
        assert not self.csv_output._warned_once

    def test_unacceptable_type(self):
        with pytest.raises(ValueError):
            self.csv_output.record('foo')

    def test_disable_warnings(self):
        foo = 1
        bar = 10
        self.tabular.record('foo', foo)
        self.csv_output.record(self.tabular)
        self.tabular.record('foo', foo * 2)
        self.tabular.record('bar', bar * 2)

        self.csv_output.disable_warnings()

        # this should not produce a warning, because we disabled warnings
        self.csv_output.record(self.tabular)

    def assert_csv_matches(self, correct):
        """Check the first row of a csv file and compare it to known values."""
        with open(self.log_file.name, 'r') as file:
            reader = csv.DictReader(file)

            for correct_row in correct:
                row = next(reader)
                assert row == correct_row
