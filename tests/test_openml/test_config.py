# License: BSD 3-Clause

import tempfile
import os
import unittest.mock

import openml.config
import openml.testing


class TestConfig(openml.testing.TestBase):
    @unittest.mock.patch("os.path.expanduser")
    @unittest.mock.patch("openml.config.openml_logger.warning")
    @unittest.mock.patch("openml.config._create_log_handlers")
    @unittest.skipIf(os.name == "nt", "https://github.com/openml/openml-python/issues/1033")
    def test_non_writable_home(self, log_handler_mock, warnings_mock, expanduser_mock):
        with tempfile.TemporaryDirectory(dir=self.workdir) as td:
            expanduser_mock.side_effect = (
                os.path.join(td, "openmldir"),
                os.path.join(td, "cachedir"),
            )
            os.chmod(td, 0o444)
            openml.config._setup()

        self.assertEqual(warnings_mock.call_count, 2)
        self.assertEqual(log_handler_mock.call_count, 1)
        self.assertFalse(log_handler_mock.call_args_list[0][1]["create_file_handler"])

    @unittest.mock.patch("os.path.expanduser")
    def test_XDG_directories_do_not_exist(self, expanduser_mock):
        with tempfile.TemporaryDirectory(dir=self.workdir) as td:

            def side_effect(path_):
                return os.path.join(td, str(path_).replace("~/", ""))

            expanduser_mock.side_effect = side_effect
            openml.config._setup()

    def test_get_config_as_dict(self):
        """ Checks if the current configuration is returned accurately as a dict. """
        config = openml.config.get_config_as_dict()
        _config = dict()
        _config["apikey"] = "610344db6388d9ba34f6db45a3cf71de"
        _config["server"] = "https://test.openml.org/api/v1/xml"
        _config["cachedir"] = self.workdir
        _config["avoid_duplicate_runs"] = False
        _config["connection_n_retries"] = 20
        _config["retry_policy"] = "robot"
        self.assertIsInstance(config, dict)
        self.assertEqual(len(config), 6)
        self.assertDictEqual(config, _config)

    def test_setup_with_config(self):
        """ Checks if the OpenML configuration can be updated using _setup(). """
        _config = dict()
        _config["apikey"] = "610344db6388d9ba34f6db45a3cf71de"
        _config["server"] = "https://www.openml.org/api/v1/xml"
        _config["cachedir"] = self.workdir
        _config["avoid_duplicate_runs"] = True
        _config["retry_policy"] = "human"
        _config["connection_n_retries"] = 100
        orig_config = openml.config.get_config_as_dict()
        openml.config._setup(_config)
        updated_config = openml.config.get_config_as_dict()
        openml.config._setup(orig_config)  # important to not affect other unit tests
        self.assertDictEqual(_config, updated_config)


class TestConfigurationForExamples(openml.testing.TestBase):
    def test_switch_to_example_configuration(self):
        """ Verifies the test configuration is loaded properly. """
        # Below is the default test key which would be used anyway, but just for clarity:
        openml.config.apikey = "610344db6388d9ba34f6db45a3cf71de"
        openml.config.server = self.production_server

        openml.config.start_using_configuration_for_example()

        self.assertEqual(openml.config.apikey, "c0c42819af31e706efe1f4b88c23c6c1")
        self.assertEqual(openml.config.server, self.test_server)

    def test_switch_from_example_configuration(self):
        """ Verifies the previous configuration is loaded after stopping. """
        # Below is the default test key which would be used anyway, but just for clarity:
        openml.config.apikey = "610344db6388d9ba34f6db45a3cf71de"
        openml.config.server = self.production_server

        openml.config.start_using_configuration_for_example()
        openml.config.stop_using_configuration_for_example()

        self.assertEqual(openml.config.apikey, "610344db6388d9ba34f6db45a3cf71de")
        self.assertEqual(openml.config.server, self.production_server)

    def test_example_configuration_stop_before_start(self):
        """ Verifies an error is raised is `stop_...` is called before `start_...`. """
        error_regex = ".*stop_use_example_configuration.*start_use_example_configuration.*first"
        self.assertRaisesRegex(
            RuntimeError, error_regex, openml.config.stop_using_configuration_for_example
        )

    def test_example_configuration_start_twice(self):
        """ Checks that the original config can be returned to if `start..` is called twice. """
        openml.config.apikey = "610344db6388d9ba34f6db45a3cf71de"
        openml.config.server = self.production_server

        openml.config.start_using_configuration_for_example()
        openml.config.start_using_configuration_for_example()
        openml.config.stop_using_configuration_for_example()

        self.assertEqual(openml.config.apikey, "610344db6388d9ba34f6db45a3cf71de")
        self.assertEqual(openml.config.server, self.production_server)
