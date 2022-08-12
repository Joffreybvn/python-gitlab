"""
GitLab API:
https://docs.gitlab.com/ee/api/job_artifacts.html
"""
import warnings
from typing import Any, Callable, Iterator, Optional, TYPE_CHECKING, Union

import requests

from gitlab import cli
from gitlab import exceptions as exc
from gitlab import utils
from gitlab.base import RESTManager, RESTObject

__all__ = [
    "ProjectArtifact",
    "ProjectArtifactManager",
    "ProjectJobArtifact",
    "ProjectJobArtifactManager",
]


class ProjectArtifact(RESTObject):
    """Dummy object to manage custom actions on artifacts"""

    _id_attr = "ref_name"


class ProjectArtifactManager(RESTManager):
    _obj_cls = ProjectArtifact
    _path = "/projects/{project_id}/jobs/artifacts"
    _from_parent_attrs = {"project_id": "id"}

    @cli.register_custom_action(
        "Project", ("ref_name", "job"), ("job_token",), custom_action="artifacts"
    )
    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[bytes]:
        utils.warn(
            message=(
                "The project.artifacts() method is deprecated and will be removed in a "
                "future version. Use project.artifacts.download() instead.\n"
            ),
            category=DeprecationWarning,
        )
        data = self.download(
            *args,
            **kwargs,
        )
        if TYPE_CHECKING:
            assert data is not None
            assert isinstance(data, bytes)
        return data

    @exc.on_http_error(exc.GitlabDeleteError)
    def delete(self, **kwargs: Any) -> None:
        """Delete the project's artifacts on the server.

        Args:
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabDeleteError: If the server cannot perform the request
        """
        path = self._compute_path("/projects/{project_id}/artifacts")

        if TYPE_CHECKING:
            assert path is not None
        self.gitlab.http_delete(path, **kwargs)

    @cli.register_custom_action(
        "ProjectArtifactManager", ("ref_name", "job"), ("job_token",)
    )
    @exc.on_http_error(exc.GitlabGetError)
    def download(
        self,
        ref_name: str,
        job: str,
        streamed: bool = False,
        action: Optional[Callable[[bytes], None]] = None,
        chunk_size: int = 1024,
        *,
        iterator: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[bytes, Iterator[Any]]]:
        """Get the job artifacts archive from a specific tag or branch.

        Args:
            ref_name: Branch or tag name in repository. HEAD or SHA references
            are not supported.
            job: The name of the job.
            job_token: Job token for multi-project pipeline triggers.
            streamed: If True the data will be processed by chunks of
                `chunk_size` and each chunk is passed to `action` for
                treatment
            iterator: If True directly return the underlying response
                iterator
            action: Callable responsible of dealing with chunk of
                data
            chunk_size: Size of each chunk
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabGetError: If the artifacts could not be retrieved

        Returns:
            The artifacts if `streamed` is False, None otherwise.
        """
        path = f"{self.path}/{ref_name}/download"
        result = self.gitlab.http_get(
            path, job=job, streamed=streamed, raw=True, **kwargs
        )
        if TYPE_CHECKING:
            assert isinstance(result, requests.Response)
        return utils.response_content(
            result, streamed, action, chunk_size, iterator=iterator
        )

    @cli.register_custom_action(
        "ProjectArtifactManager", ("ref_name", "artifact_path", "job")
    )
    @exc.on_http_error(exc.GitlabGetError)
    def raw(
        self,
        ref_name: str,
        artifact_path: str,
        job: str,
        streamed: bool = False,
        action: Optional[Callable[[bytes], None]] = None,
        chunk_size: int = 1024,
        *,
        iterator: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[bytes, Iterator[Any]]]:
        """Download a single artifact file from a specific tag or branch from
        within the job's artifacts archive.

        Args:
            ref_name: Branch or tag name in repository. HEAD or SHA references
                are not supported.
            artifact_path: Path to a file inside the artifacts archive.
            job: The name of the job.
            streamed: If True the data will be processed by chunks of
                `chunk_size` and each chunk is passed to `action` for
                treatment
            iterator: If True directly return the underlying response
                iterator
            action: Callable responsible of dealing with chunk of
                data
            chunk_size: Size of each chunk
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabGetError: If the artifacts could not be retrieved

        Returns:
            The artifact if `streamed` is False, None otherwise.
        """
        path = f"{self.path}/{ref_name}/raw/{artifact_path}"
        result = self.gitlab.http_get(
            path, streamed=streamed, raw=True, job=job, **kwargs
        )
        if TYPE_CHECKING:
            assert isinstance(result, requests.Response)
        return utils.response_content(
            result, streamed, action, chunk_size, iterator=iterator
        )


class ProjectJobArtifact(RESTObject):
    """Dummy object to manage custom actions on artifacts"""

    _id_attr = "artifact_path"


class ProjectJobArtifactManager(RESTManager):
    _path = "/projects/{project_id}/jobs/{job_id}/artifacts"
    _from_parent_attrs = {"project_id": "project_id", "job_id": "id"}

    @cli.register_custom_action("ProjectJob", custom_action="artifacts")
    def __call__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Optional[Union[bytes, Iterator[Any]]]:
        warnings.warn(
            "The job.artifacts() method is deprecated and will be "
            "removed in a future version. Use job.artifacts.download() instead.\n",
            DeprecationWarning,
        )
        return self.download(
            *args,
            **kwargs,
        )

    @cli.register_custom_action("ProjectJobArtifactManager")
    @exc.on_http_error(exc.GitlabGetError)
    def download(
        self,
        streamed: bool = False,
        action: Optional[Callable[..., Any]] = None,
        chunk_size: int = 1024,
        iterator: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[bytes, Iterator[Any]]]:
        """Get the job artifacts.

        Args:
            streamed: If True the data will be processed by chunks of
                `chunk_size` and each chunk is passed to `action` for
                treatment
            action: Callable responsible of dealing with chunk of
                data
            chunk_size: Size of each chunk
            iterator: If True directly return the underlying response
                iterator
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabGetError: If the artifacts could not be retrieved

        Returns:
            The artifacts if `streamed` is False, None otherwise.
        """
        if TYPE_CHECKING:
            assert self.path is not None
        result = self.gitlab.http_get(self.path, streamed=streamed, raw=True, **kwargs)

        if TYPE_CHECKING:
            assert isinstance(result, requests.Response)
        return utils.response_content(
            result, streamed, action, chunk_size, iterator=iterator
        )

    @cli.register_custom_action("ProjectJobArtifactManager", ("artifact_path",))
    @cli.register_custom_action("ProjectJob")
    @exc.on_http_error(exc.GitlabGetError)
    def raw(
        self,
        path: str,
        streamed: bool = False,
        action: Optional[Callable[..., Any]] = None,
        chunk_size: int = 1024,
        iterator: bool = False,
        **kwargs: Any,
    ) -> Optional[Union[bytes, Iterator[Any]]]:
        """Get a single artifact file from within the job's artifacts archive.

        Args:
            path: Path of the artifact
            streamed: If True the data will be processed by chunks of
                `chunk_size` and each chunk is passed to `action` for
                treatment
            action: Callable responsible of dealing with chunk of
                data
            chunk_size: Size of each chunk
            iterator: If True directly return the underlying response
                iterator
            **kwargs: Extra options to send to the server (e.g. sudo)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabGetError: If the artifacts could not be retrieved

        Returns:
            The artifacts if `streamed` is False, None otherwise.
        """
        path = f"{self.path}/{path}"
        result = self.gitlab.http_get(path, streamed=streamed, raw=True, **kwargs)
        if TYPE_CHECKING:
            assert isinstance(result, requests.Response)
        return utils.response_content(
            result, streamed, action, chunk_size, iterator=iterator
        )
