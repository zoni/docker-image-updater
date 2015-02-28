import attr
import logging
import subprocess
import sys
from docker.errors import APIError


@attr.s
class ContainerSet(object):
    """
    The definition of a set of Docker images which should be watched
    for updates with a set of actions to be executed when a newer version
    of the image is pulled.

    :param name:
        A unique name for this watcher.
    :param images:
        A list of Docker images to watch for updates.
    """
    name = attr.ib()
    images = attr.ib(default=attr.Factory(list))
    commands = attr.ib(default=attr.Factory(list))


class Updater(object):
    """
    The docker image updater.
    """

    def __init__(self, client, containerset):
        """
        :param client:
            The Docker client to use (a docker.Client instance)
        :param containerset:
            A list of ContainerSet instances.
        """
        self.client = client
        self.containerset = {x.name: x for x in containerset}
        self.logger = logging.getLogger(self.__class__.__name__)
        self._updated = []  # Tracks updated images
        self.error_count = 0

    def _pull_docker_image(self, image):
        """
        Pull the given docker image, printing data to stdout to
        keep the user informed of progress.
        :param image:
            The name of the image to pull down.
        """
        self.logger.info("Pulling image {}".format(image))
        attached_to_tty = sys.stdout.isatty()

        for _ in self.client.pull(image, stream=True):
            if not attached_to_tty:
                continue
            sys.stdout.write('.')
            sys.stdout.flush()

        if attached_to_tty:
            sys.stdout.write("\n")

    def _update_image(self, image):
        """
        Update the given docker image.

        :param image:
            The image to update, in the form of `ubuntu` or `ubuntu:latest`.
        :returns:
            True if the image is updated, False if it is already the latest version.
        """
        try:
            self.logger.debug("Inspecting image {}".format(image))
            image_id = self.client.inspect_image(image)['Id']
            self.logger.debug("Image id: {}".format(image_id))
        except APIError as e:
            if e.response.status_code == 404:
                self.logger.warning(
                    "404 response from docker API, assuming image does not "
                    "exist locally"
                )
                image_id = None
            else:
                raise

        self._pull_docker_image(image)
        self.logger.debug("New image id: {}".format(image_id))
        if image_id != self.client.inspect_image(image)['Id']:
            self.logger.debug("Image IDs differ before and after pull, image was updated")
            self._updated.append(image)
            return True

        self.logger.debug("Image IDs identical before and after pull")
        return False

    def _update(self, watcher):
        """
        Update the containers configured by the supplied watcher and
        execute post-update actions as needed.

        :param watcher:
            An ContainerSet instance.
        """
        updated = False
        for image in watcher.images:
            if image in self._updated:
                updated = True
                continue
            try:
                self.logger.info("Updating image {}".format(image))
                updated_ = self._update_image(image)
            except Exception:
                self.logger.exception("Exception occurred during update of {}".format(image))
                self.error_count += 1
                continue
            if updated_:
                self.logger.info("Image {} updated to latest version".format(image))
                updated = True
            else:
                self.logger.info("Image {} already at latest version".format(image))

        if not updated:
            self.logger.debug("No images in this set updated")
            return

        self.logger.debug("One or more images in this set updated")
        for command in watcher.commands:
            try:
                self._run_command(command)
            except Exception:
                self.logger.exception("Exception occurred during command execution")
                self.error_count += 1
                continue

    def _run_command(self, command):
        """
        Run given command in a shell.
        """
        self.logger.info("Running command: {}".format(command))
        p = subprocess.Popen(command, shell=True)
        returncode = p.wait()
        if returncode == 0:
            self.logger.info("Command exited successfully")
        else:
            self.logger.error("Command exited with non-zero exit code {}".format(returncode))
            self.error_count += 1

    def do_updates(self):
        """
        Update the watched images.
        """
        for watcher in self.containerset.values():
            self.logger.info("Checking images in set {}".format(watcher.name))
            self._update(watcher)
