from math import ceil
from collections import namedtuple
import requests
import kubernetes
import kopf
import constants
from models.celery_custom_resource import celery_custom_resource_from_dict
from kubernetes_utils.worker_deployment_generator import WorkerDeploymentGenerator
from kubernetes_utils.flower_deployment_generator import FlowerDeploymentGenerator

from utilities.patching import (
    update_all_deployments,
    update_worker_deployment,
    update_flower_deployment
)


@kopf.on.create('celeryproject.org', 'v1alpha1', 'celery')
def create_fn(spec, namespace, logger, **kwargs):
    """
        Celery custom resource creation handler
    """
    api = kubernetes.client.CoreV1Api()
    apps_api_instance = kubernetes.client.AppsV1Api()
    try:
        celery_cr = celery_custom_resource_from_dict(dict(spec))
    except Exception as e:
        raise kopf.PermanentError(e)

    # deploy worker
    worker_deployment = WorkerDeploymentGenerator(
        namespace=namespace, celery_cr=celery_cr
    ).get_worker_deployment()
    kopf.adopt(worker_deployment)
    apps_api_instance.create_namespaced_deployment(
        namespace=namespace,
        body=worker_deployment
    )

    # deploy flower
    flower_dep_gen_instance = FlowerDeploymentGenerator(
        namespace=namespace, celery_cr=celery_cr
    )
    flower_deployment = flower_dep_gen_instance.get_flower_deployment()
    kopf.adopt(flower_deployment)
    apps_api_instance.create_namespaced_deployment(
        namespace=namespace,
        body=flower_deployment
    )

    # expose service
    flower_svc = flower_dep_gen_instance.get_flower_svc()
    kopf.adopt(flower_svc)
    api.create_namespaced_service(namespace=namespace, body=flower_svc)

    # TODO: Decide the return structure
    return {
        'children': 3,
        'status': constants.STATUS_CREATED
    }


@kopf.on.update('celeryproject.org', 'v1alpha1', 'celery')
def update_fn(spec, status, namespace, logger, **kwargs):
    diff = kwargs.get('diff')
    modified_spec = get_modified_spec_object(diff)

    api = kubernetes.client.CoreV1Api()
    apps_api_instance = kubernetes.client.AppsV1Api()
    result = status.get('update_fn') or status.get('create_fn')

    if modified_spec.common_spec:
        # if common spec was updated, need to update all deployments
        return update_all_deployments(
            api, apps_api_instance, spec, status, namespace
        )
    else:
        if modified_spec.worker_spec:
            # if worker spec was updated, just update worker deployments
            worker_deployment = update_worker_deployment(
                apps_api_instance, spec, status, namespace
            )
            deployment_status = next(child for child in result.get('children') if child['type'] == constants.WORKER_TYPE)  # NOQA

            deployment_status.update({
                'name': worker_deployment.metadata.name,
                'replicas': worker_deployment.spec.replicas
            })

        if modified_spec.flower_spec:
            # if flower spec was updated, just update flower deployments
            flower_deployment = update_flower_deployment(
                apps_api_instance, spec, status, namespace
            )
            deployment_status = next(child for child in result.get('children') if child['type'] == constants.FLOWER_TYPE)  # NOQA

            deployment_status.update({
                'name': flower_deployment.metadata.name,
                'replicas': flower_deployment.spec.replicas
            })
        return result


def get_modified_spec_object(diff):
    """
        @param: diff - arg provided by kopf when an object is updated
        diff format - Tuple of (op, (fields tuple), old, new)
        @returns ModifiedSpec namedtuple signifying which spec was updated
    """
    common_spec_checklist = ['appName', 'celeryApp', 'image']
    celery_config_checklist = ['workerSpec']
    flower_config_checklist = ['flowerSpec']

    common_spec_modified = False
    celery_spec_modified = False
    flower_spec_modified = False

    # TODO - Optimize this loop maybe
    for op, fields, old, new in diff:
        if any(field in fields for field in common_spec_checklist):
            common_spec_modified = True
        if any(field in fields for field in celery_config_checklist):
            celery_spec_modified = True
        if any(field in fields for field in flower_config_checklist):
            flower_spec_modified = True

    # a namedtuple to give structure to which spec was updated
    ModifiedSpec = namedtuple('ModifiedSpec', ['common_spec', 'worker_spec', 'flower_spec'])

    return ModifiedSpec(
        common_spec=common_spec_modified,
        worker_spec=celery_spec_modified,
        flower_spec=flower_spec_modified
    )


def check_flower_label(value, spec, **_):
    """
        Checks if incoming label value is the one assigned to
        flower service and deployment
    """
    return value == f"{spec['common']['appName']}-flower"


def get_flower_svc_host(status):
    """
        Get latest flower SVC host from parent's status
    """
    handler = status.get('update_fn') or status.get('create_fn')

    for child in handler.get('children'):
        if child.get('kind') == constants.SERVICE_KIND and child.get('type') == constants.FLOWER_TYPE:  # NOQA
            return f"{child.get('name')}:{child['spec']['ports'][0]['port']}"

    return None


@kopf.timer('celeryproject.org', 'v1alpha1', 'celery',
            initial_delay=50000, interval=10000, idle=10)
def message_queue_length(spec, status, **kwargs):
    flower_svc_host = get_flower_svc_host(status)
    if not flower_svc_host:
        return

    url = f"http://{flower_svc_host}/api/queues/length"
    response = requests.get(url=url)
    if response.status_code == 200:
        return response.json().get('active_queues')

    return {
        "queue_length": 0
    }


def get_current_replicas(child_name, status):
    children = status.get('create_fn').get('children')
    for child in children:
        if child.get('name') == child_name:
            return child.get('replicas')


def get_current_queue_len(child_name, status):
    for queue in status.get('message_queue_length', []):
        if queue.get('name') == child_name:
            return queue.get('messages')

    return 0


@kopf.on.field('celeryproject.org', 'v1alpha1', 'celery',
               field='status.message_queue_length')
def horizontal_autoscale(spec, status, namespace, **kwargs):
    worker_deployment_name = f"{spec['common']['appName']}-celery-worker"
    current_replicas = get_current_replicas(worker_deployment_name, status)
    updated_num_of_replicas = current_replicas
    scaling_targets = spec['scaleTargetRef']
    for scaling_target in scaling_targets:
        # For now we only support 1 i.e message queue length
        if scaling_target.get('kind') == 'worker':
            min_replicas = scaling_target.get('minReplicas', spec['workerSpec']['numOfWorkers'])
            max_replicas = scaling_target.get('maxReplicas')
            queue_name = spec['workerSpec']['queues']
            current_queue_length = get_current_queue_len(queue_name, status)
            avg_queue_length = scaling_target['metrics'][0].get('target').get('averageValue')
            updated_num_of_replicas = min(
                max(
                    ceil(
                        current_replicas * (current_queue_length / avg_queue_length)
                    ),
                    min_replicas
                ),
                max_replicas
            )

    patch_body = {
        "spec": {
            "replicas": updated_num_of_replicas,
        }
    }

    apps_api_instance = kubernetes.client.AppsV1Api()
    updated_deployment = apps_api_instance.patch_namespaced_deployment(
        worker_deployment_name, namespace, patch_body
    )

    return {
        'deploymentName': updated_deployment.metadata.name,
        'updated_num_of_replicas': updated_num_of_replicas
    }