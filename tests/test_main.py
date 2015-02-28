import mock
import pytest
import yaml
from diu.main import Application
from diu.updater import ContainerSet, Updater


class TestApplication(object):
    @pytest.fixture
    def app(self, tmpdir, config=None):
        f = tmpdir.join("config.yml")
        if config is None:
            config = {
                'config': {
                    'docker': {
                        'version': '1.16',
                        'base_url': 'unix://var/run/docker.sock',
                    }
                },
                'watch': {
                    'ubuntu': {
                        'images': ['ubuntu:latest', 'ubuntu:14.04'],
                        'commands': ['foo', 'bar'],
                    },
                }
            }
        yaml.dump(config, f.open('w'))
        return Application(args=["--file", str(f)])

    def test_config_is_loaded_from_config_file(self, app):
        assert app.config == {
            'docker': {
                'version': '1.16',
                'base_url': 'unix://var/run/docker.sock',
            }
        }

    def test_containerset_is_loaded_from_config_file(self, app):
        assert len(app.containerset) == 1
        assert isinstance(app.containerset[0], ContainerSet)
        assert app.containerset[0].name == "ubuntu"

    def test_updater_instance_is_initialized_during_init(self, app):
        assert isinstance(app.updater, Updater)

    def test_run_calls_updater_do_updates(self, tmpdir):
        with mock.patch('diu.main.Updater') as m:
            app = self.app(tmpdir=tmpdir)
        app.updater.error_count = 0
        app.run()
        app.updater.do_updates.assert_called_once_with()

    def test_docker_client_initialized_with_params_from_config(self, tmpdir):
        with mock.patch('diu.main.DockerClient') as m:
            app = self.app(tmpdir=tmpdir)
        m.assert_called_once_with(
            version='1.16',
            base_url='unix://var/run/docker.sock'
        )
