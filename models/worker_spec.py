from dataclasses import dataclass
from typing import Any, List, TypeVar, Type, cast, Callable


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


@dataclass
class Constraints:
    cpu: str
    memory: str

    @staticmethod
    def from_dict(obj: Any) -> 'Constraints':
        assert isinstance(obj, dict)
        cpu = from_str(obj.get("cpu"))
        memory = from_str(obj.get("memory"))
        return Constraints(cpu, memory)

    def to_dict(self) -> dict:
        result: dict = {}
        result["cpu"] = from_str(self.cpu)
        result["memory"] = from_str(self.memory)
        return result


@dataclass
class Resources:
    requests: Constraints
    limits: Constraints

    @staticmethod
    def from_dict(obj: Any) -> 'Resources':
        assert isinstance(obj, dict)
        requests = Constraints.from_dict(obj.get("requests"))
        limits = Constraints.from_dict(obj.get("limits"))
        return Resources(requests, limits)

    def to_dict(self) -> dict:
        result: dict = {}
        result["requests"] = to_class(Constraints, self.requests)
        result["limits"] = to_class(Constraints, self.limits)
        return result


@dataclass
class WorkerSpec:
    args: List[str]
    command: List[str]
    image: str
    name: str
    resources: Resources

    @staticmethod
    def from_dict(obj: Any) -> 'WorkerSpec':
        assert isinstance(obj, dict)
        args = from_list(from_str, obj.get("args"))
        command = from_list(from_str, obj.get("command"))
        image = from_str(obj.get("image"))
        name = from_str(obj.get("name"))
        resources = Resources.from_dict(obj.get("resources"))
        return WorkerSpec(args, command, image, name, resources)

    def to_dict(self) -> dict:
        result: dict = {}
        result["args"] = from_list(from_str, self.args)
        result["command"] = from_list(from_str, self.command)
        result["image"] = from_str(self.image)
        result["name"] = from_str(self.name)
        result["resources"] = to_class(Resources, self.resources)
        return result


def args_list_from_spec_params(
    celery_app: str,
    queues: str,
    loglevel: str,
    concurrency: int
) -> List[str]:
    return [
        f"--app={celery_app}",
        "worker",
        f"--queues={queues}",
        f"--loglevel={loglevel}",
        f"--concurrency={concurrency}"
    ]


def worker_spec_from_dict(s: Any) -> WorkerSpec:
    return WorkerSpec.from_dict(s)


def worker_spec_to_dict(x: WorkerSpec) -> Any:
    return to_class(WorkerSpec, x)

# To use this code, make sure you
#
#     import json
#
# and then, to convert JSON from a string, do
#
#     result = worker_spec_from_dict(json.loads(json_string))
