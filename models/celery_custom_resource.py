# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = celery_custom_resource_from_dict(json.loads(json_string))

from dataclasses import dataclass
from typing import Any, Optional, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_none(x: Any) -> Any:
    assert x is None
    return x


def from_union(fs, x):
    for f in fs:
        try:
            return f(x)
        except:
            pass
    assert False


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_dict(x: Any) -> dict:
    assert isinstance(x, dict)
    return x


@dataclass
class ResourceRequirements:
    requests: Optional[dict] = None
    limits: Optional[dict] = None

    @staticmethod
    def from_dict(obj: Any) -> 'ResourceRequirements':
        assert isinstance(obj, dict)
        requests = from_union([from_dict, from_none], obj.get("requests"))
        limits = from_union([from_dict, from_none], obj.get("limits"))
        return ResourceRequirements(requests, limits)

    def to_dict(self) -> dict:
        result: dict = {}
        result["requests"] = from_union([from_dict, from_none], self.requests)
        result["limits"] = from_union([from_dict, from_none], self.limits)
        return result


@dataclass
class FlowerSpecificSpec:
    service: Optional[dict] = None
    args: Optional[List[str]] = None
    node_selector: Optional[dict] = None
    env: Optional[List[dict]] = None
    resources: Optional[ResourceRequirements] = None

    @staticmethod
    def from_dict(obj: Any) -> 'FlowerSpecificSpec':
        assert isinstance(obj, dict)
        service = from_union([from_dict, from_none], obj.get("service"))
        args = from_union([lambda x: from_list(from_str, x), from_none], obj.get("args"))
        node_selector = from_union([from_dict, from_none], obj.get("nodeSelector"))
        env = from_union([lambda x: from_list(from_dict, x), from_none], obj.get("env"))
        resources = from_union([ResourceRequirements.from_dict, from_none], obj.get("resources"))
        return FlowerSpecificSpec(service, args, node_selector, env, resources)

    def to_dict(self) -> dict:
        result: dict = {}
        result["service"] = from_union([from_dict, from_none], self.service)
        result["args"] = from_union([lambda x: from_list(from_str, x), from_none], self.args)
        result["nodeSelector"] = from_union([from_dict, from_none], self.node_selector)
        result["env"] = from_union([lambda x: from_list(from_dict, x), from_none], self.env)
        result["resources"] = from_union([lambda x: to_class(ResourceRequirements, x), from_none], self.resources)
        return result


@dataclass
class WorkerSpecificSpec:
    args: Optional[List[str]] = None
    node_selector: Optional[dict] = None
    env: Optional[List[dict]] = None
    resources: Optional[ResourceRequirements] = None

    @staticmethod
    def from_dict(obj: Any) -> 'WorkerSpecificSpec':
        assert isinstance(obj, dict)
        args = from_union([lambda x: from_list(from_str, x), from_none], obj.get("args"))
        node_selector = from_union([from_dict, from_none], obj.get("nodeSelector"))
        env = from_union([lambda x: from_list(from_dict, x), from_none], obj.get("env"))
        resources = from_union([ResourceRequirements.from_dict, from_none], obj.get("resources"))
        return WorkerSpecificSpec(args, node_selector, env, resources)

    def to_dict(self) -> dict:
        result: dict = {}
        result["args"] = from_union([lambda x: from_list(from_str, x), from_none], self.args)
        result["nodeSelector"] = from_union([from_dict, from_none], self.node_selector)
        result["env"] = from_union([lambda x: from_list(from_dict, x), from_none], self.env)
        result["resources"] = from_union([lambda x: to_class(ResourceRequirements, x), from_none], self.resources)
        return result


@dataclass
class CeleryCustomResource:
    app_name: str
    celery_app: str
    celery_version: str
    image: str
    worker_spec: WorkerSpecificSpec
    flower_spec: FlowerSpecificSpec
    image_pull_policy: Optional[str] = None
    image_pull_secrets: Optional[List[dict]] = None
    worker_replicas: Optional[int] = None
    flower_replicas: Optional[int] = None
    init_containers: Optional[List[Any]] = None
    volume_mounts: Optional[List[Any]] = None
    volumes: Optional[List[Any]] = None
    liveness_probe: Optional[dict] = None
    readiness_probe: Optional[dict] = None

    @staticmethod
    def from_dict(obj: Any) -> 'CeleryCustomResource':
        assert isinstance(obj, dict)
        app_name = from_str(obj.get("appName"))
        celery_app = from_str(obj.get("celeryApp"))
        celery_version = from_str(obj.get("celeryVersion"))
        image = from_str(obj.get("image"))
        image_pull_policy = from_union([from_str, from_none], obj.get("imagePullPolicy"))
        image_pull_secrets = from_union(
            [lambda x: from_list(from_dict, x), from_none], obj.get("imagePullSecrets"))
        worker_replicas = from_union([from_int, from_none], obj.get("workerReplicas"))
        flower_replicas = from_union([from_int, from_none], obj.get("flowerReplicas"))
        worker_spec = from_union([WorkerSpecificSpec.from_dict, from_none], obj.get("workerSpec"))
        flower_spec = from_union([FlowerSpecificSpec.from_dict, from_none], obj.get("flowerSpec"))
        init_containers = from_union(
            [lambda x: from_list(lambda x: x, x), from_none], obj.get("initContainers"))
        volume_mounts = from_union(
            [lambda x: from_list(lambda x: x, x), from_none], obj.get("volumeMounts"))
        volumes = from_union([lambda x: from_list(lambda x: x, x), from_none], obj.get("volumes"))
        liveness_probe = from_union([from_dict, from_none], obj.get("livenessProbe"))
        readiness_probe = from_union([from_dict, from_none], obj.get("readinessProbe"))
        return CeleryCustomResource(
            app_name, celery_app, celery_version,
            image, worker_spec, flower_spec, image_pull_policy,
            image_pull_secrets, worker_replicas, flower_replicas,
            init_containers, volume_mounts, volumes, liveness_probe, readiness_probe
        )

    def to_dict(self) -> dict:
        result: dict = {}
        result["appName"] = from_str(self.app_name)
        result["celeryApp"] = from_str(self.celery_app)
        result["celeryVersion"] = from_str(self.celery_version)
        result["image"] = from_str(self.image)
        result["imagePullPolicy"] = from_union([from_str, from_none], self.image_pull_policy)
        result["imagePullSecrets"] = from_union([lambda x: from_list(from_dict), from_none], self.image_pull_secrets)
        result["workerReplicas"] = from_union([from_int, from_none], self.worker_replicas)
        result["flowerReplicas"] = from_union([from_int, from_none], self.flower_replicas)
        result["workerSpec"] = from_union([lambda x: to_class(WorkerSpecificSpec, x), from_none], self.worker_spec)
        result["flowerSpec"] = from_union([lambda x: to_class(FlowerSpecificSpec, x), from_none], self.flower_spec)
        result["initContainers"] = from_union([lambda x: from_list(lambda x: x, x), from_none], self.init_containers)
        result["volumeMounts"] = from_union([lambda x: from_list(lambda x: x, x), from_none], self.volume_mounts)
        result["volumes"] = from_union([lambda x: from_list(lambda x: x, x), from_none], self.volumes)
        result["livenessProbe"] = from_union([from_dict, from_none], self.liveness_probe)
        result["readinessProbe"] = from_union([from_dict, from_none], self.readiness_probe)
        return result


def celery_custom_resource_from_dict(s: Any) -> CeleryCustomResource:
    return CeleryCustomResource.from_dict(s)


def celery_custom_resource_to_dict(x: CeleryCustomResource) -> Any:
    return to_class(CeleryCustomResource, x)
