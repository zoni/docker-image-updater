from diu.main import Application as RealApplication


class Application(RealApplication):
    def _load_config(self, *files):
        self.config = {}
        self.given_config_files = files


class TestApplication(object):
    def test_deprecated_file_argument_takes_precedence(self):
        app = Application(["--file", "test.yaml"])
        assert app.given_config_files == ("test.yaml",)

    def test_no_file_arg_uses_etc_docker_image_updater_yml(self):
        app = Application([])
        assert app.given_config_files == ("/etc/docker-image-updater.yml",)
