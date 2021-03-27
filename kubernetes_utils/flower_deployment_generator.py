from typing import List
from kubernetes import client as k8s
from kubernetes_utils.pod_generator import PodGenerator
from models.celery_custom_resource import CeleryCustomResource


class FlowerDeploymentGenerator(object):

    def __init__(self, namespace: str, celery_cr: CeleryCustomResource):
        self.namespace = namespace
        self.celery_cr = celery_cr

    def get_flower_deployment(self) -> k8s.V1Deployment:
        template = k8s.V1PodTemplateSpec(
            metadata=k8s.V1ObjectMeta(
                labels={"app": f'{self.celery_cr.app_name}-celery-flower'}
            ),
            spec=self.get_flower_pod().spec
        )
        deployment_spec = k8s.V1DeploymentSpec(
            replicas=self.celery_cr.worker_replicas,
            template=template,
            selector={'matchLabels': {'app': f'{self.celery_cr.app_name}-celery-flower'}}
        )

        return k8s.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=k8s.V1ObjectMeta(name=f'{self.celery_cr.app_name}-celery-flower'),
            spec=deployment_spec
        )

    def get_flower_pod(self) -> k8s.V1Pod:
        return PodGenerator(
            namespace=self.namespace,
            image=self.celery_cr.image,
            image_pull_policy=self.celery_cr.image_pull_policy,
            image_pull_secrets=self.celery_cr.image_pull_secrets,
            name=f"{self.celery_cr.app_name}-celery-flower",
            container_name='flower',
            volume_mounts=self.celery_cr.volume_mounts,
            volumes=self.celery_cr.volumes,
            init_containers=self.celery_cr.init_containers,
            cmds=["flower"],
            envs=self.celery_cr.flower_spec.env,
            args=self.__get_flower_container_args(
                self.celery_cr.celery_app, self.celery_cr.flower_spec.args
            ),
            node_selectors=self.celery_cr.flower_spec.node_selector,
            resources=self.celery_cr.flower_spec.resources.to_dict(),
            readiness_probe=self.celery_cr.readiness_probe,
            liveness_probe=self.celery_cr.liveness_probe
        ).gen_pod()

    def get_flower_svc(self) -> k8s.V1Service:
        svc_template = self.celery_cr.flower_spec.service
        metadata = {
            'name': f'{self.celery_cr.app_name}-celery-flower'
        }
        return k8s.V1Service(
            metadata=metadata,
            spec=svc_template.get('spec')
        )

    def __get_flower_container_args(
            self, celery_app: str, args: List[str]
    ) -> List[str]:
        base_args = [f"--app={celery_app}", "flower"]
        if args:
            base_args.extend(args)
        return base_args
