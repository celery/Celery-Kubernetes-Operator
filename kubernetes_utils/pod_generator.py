from typing import Dict, List, Optional, Union

from kubernetes import client as k8s


class PodGenerator(object):
    """
        Wrapper class to generate a Kubernetes Pod
        Class source taken from: https://github.com/apache/airflow repository

        Any configuration that is container specific gets applied to
        the first container in the list of containers.
        :param image: The docker image
        :type image: Optional[str]
        :param name: name in the metadata section (not the container name)
        :type name: Optional[str]
        :param namespace: pod namespace
        :type namespace: Optional[str]
        :param volume_mounts: list of kubernetes volumes mounts
        :type volume_mounts: Optional[List[Union[k8s.V1VolumeMount, dict]]]
        :param envs: A dict containing the environment variables
        :type envs: Optional[Dict[str, str]]
        :param cmds: The command to be run on the first container
        :type cmds: Optional[List[str]]
        :param args: The arguments to be run on the pod
        :type args: Optional[List[str]]
        :param labels: labels for the pod metadata
        :type labels: Optional[Dict[str, str]]
        :param node_selectors: node selectors for the pod
        :type node_selectors: Optional[Dict[str, str]]
        :param ports: list of ports. Applies to the first container.
        :type ports: Optional[List[Union[k8s.V1ContainerPort, dict]]]
        :param volumes: Volumes to be attached to the first container
        :type volumes: Optional[List[Union[k8s.V1Volume, dict]]]
        :param image_pull_policy: Specify a policy to cache or always pull an image
        :type image_pull_policy: str
        :param restart_policy: The restart policy of the pod
        :type restart_policy: str
        :param image_pull_secrets: Any image pull secrets to be given to the pod.
            If more than one secret is required, provide a comma separated list:
            secret_a,secret_b
        :type image_pull_secrets: str
        :param init_containers: A list of init containers
        :type init_containers: Optional[List[k8s.V1Container]]
        :param service_account_name: Identity for processes that run in a Pod
        :type service_account_name: Optional[str]
        :param resources: Resource requirements for the first containers
        :type resources: Optional[Union[k8s.V1ResourceRequirements, dict]]
        :param readiness_probe: Periodic probe of container service readiness.
        :type readiness_probe: Optional[Union[k8s.V1Probe, dict]]
        :param liveness_probe: Periodic probe of container service liveness.
        :type liveness_probe: Optional[Union[k8s.V1Probe, dict]]
        :param annotations: annotations for the pod
        :type annotations: Optional[Dict[str, str]]
        :param affinity: A dict containing a group of affinity scheduling rules
        :type affinity: Optional[dict]
        :param hostnetwork: If True enable host networking on the pod
        :type hostnetwork: bool
        :param tolerations: A list of kubernetes tolerations
        :type tolerations: Optional[list]
        :param security_context: A dict containing the security context for the pod
        :type security_context: Optional[Union[k8s.V1PodSecurityContext, dict]]
        :param configmaps: Any configmap refs to envfrom.
            If more than one configmap is required, provide a comma separated list
            configmap_a,configmap_b
        :type configmaps: List[str]
        :param dnspolicy: Specify a dnspolicy for the pod
        :type dnspolicy: Optional[str]
        :param schedulername: Specify a schedulername for the pod
        :type schedulername: Optional[str]
        :param pod: The fully specified pod. Mutually exclusive with `path_or_string`
        :type pod: Optional[kubernetes.client.models.V1Pod]
        :param extract_xcom: Whether to bring up a container for xcom
        :type extract_xcom: bool
        :param priority_class_name: priority class name for the launched Pod
        :type priority_class_name: str
        """

    def __init__(
            self,
            image: Optional[str] = None,
            name: Optional[str] = None,
            namespace: Optional[str] = None,
            volume_mounts: Optional[List[Union[k8s.V1VolumeMount, dict]]] = None,
            envs: Optional[Dict[str, str]] = None,
            cmds: Optional[List[str]] = None,
            args: Optional[List[str]] = None,
            container_name: Optional[str] = 'base',
            labels: Optional[Dict[str, str]] = None,
            node_selectors: Optional[Dict[str, str]] = None,
            ports: Optional[List[Union[k8s.V1ContainerPort, dict]]] = None,
            volumes: Optional[List[Union[k8s.V1Volume, dict]]] = None,
            image_pull_policy: Optional[str] = None,
            restart_policy: Optional[str] = None,
            image_pull_secrets: Optional[str] = None,
            init_containers: Optional[List[k8s.V1Container]] = None,
            service_account_name: Optional[str] = None,
            resources: Optional[Union[k8s.V1ResourceRequirements, dict]] = None,
            readiness_probe: Optional[Union[k8s.V1Probe, dict]] = None,
            liveness_probe: Optional[Union[k8s.V1Probe, dict]] = None,
            annotations: Optional[Dict[str, str]] = None,
            affinity: Optional[dict] = None,
            hostnetwork: bool = False,
            tolerations: Optional[list] = None,
            security_context: Optional[Union[k8s.V1PodSecurityContext, dict]] = None,
            configmaps: Optional[List[str]] = None,
            dnspolicy: Optional[str] = None,
            schedulername: Optional[str] = None,
            priority_class_name: Optional[str] = None
    ):

        self.pod = k8s.V1Pod()
        self.pod.api_version = 'v1'
        self.pod.kind = 'Pod'

        # Pod Metadata
        self.metadata = k8s.V1ObjectMeta()
        self.metadata.labels = labels
        self.metadata.name = name
        self.metadata.namespace = namespace
        self.metadata.annotations = annotations

        # Pod Container
        self.container = k8s.V1Container(name=container_name)
        self.container.image = image
        self.container.env = []

        if envs:
            if isinstance(envs, dict):
                for key, val in envs.items():
                    self.container.env.append(k8s.V1EnvVar(name=key, value=val))
            elif isinstance(envs, list):
                self.container.env.extend(envs)

        configmaps = configmaps or []
        self.container.env_from = []
        for configmap in configmaps:
            self.container.env_from.append(
                k8s.V1EnvFromSource(config_map_ref=k8s.V1ConfigMapEnvSource(name=configmap))
            )

        self.container.command = cmds or []
        self.container.args = args or []
        self.container.image_pull_policy = image_pull_policy
        self.container.ports = ports or []
        self.container.resources = resources
        self.container.liveness_probe = liveness_probe
        self.container.readiness_probe = readiness_probe
        self.container.volume_mounts = volume_mounts or []

        # Pod Spec
        self.spec = k8s.V1PodSpec(containers=[])
        self.spec.security_context = security_context
        self.spec.tolerations = tolerations
        self.spec.dns_policy = dnspolicy
        self.spec.scheduler_name = schedulername
        self.spec.host_network = hostnetwork
        self.spec.affinity = affinity
        self.spec.service_account_name = service_account_name
        self.spec.init_containers = init_containers
        self.spec.volumes = volumes or []
        self.spec.node_selector = node_selectors
        self.spec.restart_policy = restart_policy
        self.spec.priority_class_name = priority_class_name

        self.spec.image_pull_secrets = []

        if image_pull_secrets:
            for image_pull_secret in image_pull_secrets.split(','):
                self.spec.image_pull_secrets.append(k8s.V1LocalObjectReference(name=image_pull_secret))

    def gen_pod(self) -> k8s.V1Pod:
        """Generates pod"""
        result = None

        if result is None:
            result = self.pod
            result.spec = self.spec
            result.metadata = self.metadata
            result.spec.containers = [self.container]

        # result.metadata.name = self.make_unique_pod_id(result.metadata.name)
        return result