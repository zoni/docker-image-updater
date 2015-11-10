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
        return Application(args=[str(f)])

    @pytest.fixture
    def multiconfig_app(self, tmpdir):
        f1 = tmpdir.join("config1.yml")
        f2 = tmpdir.join("config2.yml")

        config1 = {
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
        config2 = {
            'config': {
                'docker': {
                    'version': '1.17',
                    'base_url': 'unix://var/run/docker.sock',
                }
            },
            'watch': {
                'ubuntu': {
                    'images': ['ubuntu:latest', 'ubuntu:15.04'],
                    'commands': ['baz'],
                },
                'debian': {
                    'images': ['debian:squeeze'],
                    'commands': ['foo']
                }
            }
        }

        yaml.dump(config1, f1.open('w'))
        yaml.dump(config2, f2.open('w'))

        return Application(args=[str(f1), str(f2)])


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

    def test_config_loading_with_multiple_configs(self, multiconfig_app):
        app = multiconfig_app
        assert len(app.containerset) == 2
        assert isinstance(app.containerset[0], ContainerSet)
        assert isinstance(app.containerset[1], ContainerSet)

        if app.containerset[0].name == "debian":
            debian = app.containerset[0]
            ubuntu = app.containerset[1]
        else:
            debian = app.containerset[1]
            ubuntu = app.containerset[0]

        assert debian.name == "debian"
        assert debian.images == ['debian:squeeze']
        assert debian.commands == ['foo']
        assert ubuntu.name == "ubuntu"
        assert sorted(ubuntu.images) == sorted(['ubuntu:14.04', 'ubuntu:latest', 'ubuntu:15.04'])
        assert sorted(ubuntu.commands) == sorted(['baz', 'foo', 'bar'])

    def test_shady_configs(self, tmpdir):
        self.app(tmpdir=tmpdir, config={})
        self.app(tmpdir=tmpdir, config={'watch': {}})
        self.app(tmpdir=tmpdir, config={'watch': {"myapp": {}}})
        with pytest.raises(SystemExit):
            self.app(tmpdir=tmpdir, config={'config': []})
        with pytest.raises(SystemExit):
            self.app(tmpdir=tmpdir, config={'config': "foo"})
        with pytest.raises(SystemExit):
            self.app(tmpdir=tmpdir, config={'watch': []})
        with pytest.raises(SystemExit):
            self.app(tmpdir=tmpdir, config={'watch': "myapp"})
        with pytest.raises(SystemExit):
            self.app(tmpdir=tmpdir, config={'watch': {"myapp": []}})
