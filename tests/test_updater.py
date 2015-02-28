import itertools
import mock
import pytest
from copy import deepcopy
from docker.errors import APIError
from diu.updater import Updater, ContainerSet


CONTAINERSET = [
    ContainerSet(
        name="ubuntu",
        images=['ubuntu:latest', 'ubuntu:14.04'],
        commands=['foo', 'bar'],
    )
]


class TestUpdater(object):
    @pytest.fixture
    def default_image(self):
        return {
            'Id': 'c3c3d842b8f7b00268f391ee65d57ffddb955cd8c7f5b330710b14bc9781d8f2',
        }

    @pytest.fixture(autouse=True)
    def updater(self, default_image):
        c = mock.MagicMock()
        c.inspect_image.return_value = default_image

        self.client = c
        self.updater = Updater(client=self.client, containerset=CONTAINERSET)
        return self.updater

    def test_init_sets_paramaters_on_self(self, updater):
        assert updater.client == self.client

        assert list(updater.containerset.keys()) == [w.name for w in CONTAINERSET]
        assert list(updater.containerset.values()) == CONTAINERSET

    def test_update_image_detects_whether_image_was_updated(self, updater, default_image):
        updated = updater._update_image('ubuntu:latest')
        assert not updated
        assert updater._updated == []

        before = default_image
        after = deepcopy(before)
        after['Id'] = 'a-new-id'
        self.client.inspect_image.side_effect = [before, after]

        updated = updater._update_image('ubuntu:latest')
        assert updated
        assert updater._updated == ['ubuntu:latest']

    def test_update_image_will_pull_if_image_not_found(self, updater, default_image):
        r = mock.MagicMock()
        r.status_code = 404
        e = APIError(
            "404 Client Error: Not Found",
            response=r,
            explanation="No such image: ubuntu:newtag"
        )
        self.client.inspect_image.side_effect = [e, default_image]
        updated = updater._update_image('ubuntu:newtag')
        assert updated
        assert updater._updated == ['ubuntu:newtag']

    def test_do_updates_calls_update_with_each_containerset(self, updater):
        with mock.patch.object(Updater, '_update') as m:
            updater.do_updates()

        expected_calls = [mock.call(w) for w in CONTAINERSET]
        assert m.call_args_list == expected_calls

    @mock.patch('diu.updater.Updater._run_command')
    def test_update_will_call_update_image_for_configured_images(self, run_command_mock, updater):
        with mock.patch.object(Updater, '_update_image') as m:
            updater.do_updates()

        expected_images = list(itertools.chain.from_iterable([x.images for x in CONTAINERSET]))
        expected_calls = [mock.call(i) for i in expected_images]
        assert expected_calls == m.call_args_list

    @mock.patch('diu.updater.Updater._run_command')
    def test_update_will_not_run_commands_if_no_images_updated(self, run_command_mock, updater):
        m = mock.MagicMock()
        m.return_value = False
        with mock.patch.object(Updater, '_update_image', new=m):
            updater.do_updates()
        assert not run_command_mock.called

    @mock.patch('diu.updater.Updater._run_command')
    def test_update_will_run_commands_if_images_updated(self, run_command_mock, updater):
        m = mock.MagicMock()
        m.return_value = True
        with mock.patch.object(Updater, '_update_image', new=m):
            updater.do_updates()
        assert run_command_mock.called

        expected_commands = list(itertools.chain.from_iterable([w.commands for w in CONTAINERSET]))
        expected_calls = [mock.call(x) for x in expected_commands]
        assert expected_calls == run_command_mock.call_args_list

    def test_update_continues_if_update_image_throws_exception(self, updater):
        m = mock.MagicMock()
        m.side_effect = Exception("Boom!")
        with mock.patch.object(Updater, '_update_image', new=m):
            updater.do_updates()

    def test_update_continues_if_run_command_throws_exception(self, updater):
        run_command_mock = mock.MagicMock()
        run_command_mock.side_effect = Exception("Boom!")
        update_image_mock = mock.MagicMock()
        update_image_mock.return_value = True
        with mock.patch.object(Updater, '_update_image', new=update_image_mock), \
             mock.patch.object(Updater, '_run_command', new=run_command_mock):
                updater.do_updates()

    @mock.patch('diu.updater.Updater._run_command')
    def test_update_is_aware_of_images_updated_by_other_containerset(self, run_command_mock, updater):
        assert "ubuntu:latest" in CONTAINERSET[0].images
        updater._updated = ["ubuntu:latest"]

        updater._update(CONTAINERSET[0])
        assert run_command_mock.called

    def test_error_count_is_incremented_if_updating_image_fails(self, updater):
        assert updater.error_count == 0
        m = mock.MagicMock()
        m.side_effect = Exception("Boom!")
        with mock.patch.object(Updater, '_update_image', new=m):
            updater.do_updates()
        assert updater.error_count == 2

    def test_error_count_is_incremented_if_running_command_fails(self, updater):
        run_command_mock = mock.MagicMock()
        run_command_mock.side_effect = Exception("Boom!")
        update_image_mock = mock.MagicMock()
        update_image_mock.return_value = True

        assert updater.error_count == 0
        with mock.patch.object(Updater, '_update_image', new=update_image_mock), \
             mock.patch.object(Updater, '_run_command', new=run_command_mock):
            updater.do_updates()
        assert updater.error_count == 2

    def test_error_count_is_incremented_if_command_returns_non_zero_exit(self, updater):
        update_image_mock = mock.MagicMock()
        update_image_mock.return_value = True
        popen_return = mock.MagicMock()
        popen_return.wait.return_value = 1
        popen_mock = mock.MagicMock()
        popen_mock.return_value = popen_return
        assert updater.error_count == 0

        with mock.patch.object(Updater, '_update_image', new=update_image_mock), \
             mock.patch('diu.updater.subprocess.Popen', new=popen_mock) as m:
            updater.do_updates()

        assert m.called
        assert updater.error_count == 2
