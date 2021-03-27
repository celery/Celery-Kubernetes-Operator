from typing import List
from kubernetes import client as k8s
from kubernetes_utils.pod_generator import PodGenerator
from models.celery_custom_resource import CeleryCustomResource


class WorkerDeploymentGenerator(object):

    def __init__(self, namespace: str, celery_cr: CeleryCustomResource):
        self.namespace = namespace
        self.celery_cr = celery_cr

    def get_worker_deployment(self) -> k8s.V1Deployment:
        template = k8s.V1PodTemplateSpec(
            metadata=k8s.V1ObjectMeta(
                labels={"app": f'{self.celery_cr.app_name}-celery-worker'}
            ),
            spec=self.get_worker_pod().spec
        )
        deployment_spec = k8s.V1DeploymentSpec(
            replicas=self.celery_cr.worker_replicas,
            template=template,
            selector={'matchLabels': {'app': f'{self.celery_cr.app_name}-celery-worker'}}
        )

        return k8s.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=k8s.V1ObjectMeta(name=f'{self.celery_cr.app_name}-celery'),
            spec=deployment_spec
        )

    def get_worker_pod(self) -> k8s.V1Pod:
        return PodGenerator(
            namespace=self.namespace,
            image=self.celery_cr.image,
            image_pull_policy=self.celery_cr.image_pull_policy,
            image_pull_secrets=self.celery_cr.image_pull_secrets,
            name=f"{self.celery_cr.app_name}-celery-worker",
            container_name='celery',
            volume_mounts=self.celery_cr.volume_mounts,
            volumes=self.celery_cr.volumes,
            init_containers=self.celery_cr.init_containers,
            envs=self.celery_cr.worker_spec.env,
            cmds=["celery"],
            args=self.__get_worker_container_args(
                self.celery_cr.celery_app, self.celery_cr.worker_spec.args
            ),
            node_selectors=self.celery_cr.worker_spec.node_selector,
            resources=self.celery_cr.worker_spec.resources.to_dict(),
            readiness_probe=self.celery_cr.readiness_probe,
            liveness_probe=self.celery_cr.liveness_probe
        ).gen_pod()

    def __get_worker_container_args(
            self, celery_app: str, args: List[str]
    ) -> List[str]:
        base_args = [f"--app={celery_app}", "worker"]
        if args:
            base_args.extend(args)
        return base_args
