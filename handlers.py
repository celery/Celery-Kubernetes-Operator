import os
import kopf
import kubernetes
import requests
import constants
from math import ceil
from collections import namedtuple

from deployment_utils import (
    deploy_celery_workers,
    deploy_flower,
    expose_flower_service
)
from update_utils import (
    update_all_deployments,
    update_worker_deployment,
    update_flower_deployment
)


@kopf.on.create('celeryproject.org', 'v1alpha1', 'celery')
def create_fn(spec, name, namespace, logger, **kwargs):
    """
        Celery custom resource creation handler
    """
    children_count = 0

    # 1. Validation of spec
    val, err_msg = validate_spec(spec)
    if err_msg:
        status = 'Failed validation'
        raise kopf.PermanentError(f"{err_msg}. Got {val}")

    api = kubernetes.client.CoreV1Api()
    apps_api_instance = kubernetes.client.AppsV1Api()

    # 2. Deployment for celery workers
    worker_deployment = deploy_celery_workers(
        apps_api_instance, namespace, spec, logger
    )

    # 3. Deployment for flower
    flower_deployment = deploy_flower(
        apps_api_instance, namespace, spec, logger
    )

    # 4. Expose flower service
    flower_svc = expose_flower_service(
        api, namespace, spec, logger
    )

    children = [
        {
            'name': worker_deployment.metadata.name,
            'replicas': worker_deployment.spec.replicas,
            'kind': constants.DEPLOYMENT_KIND,
            'type': constants.WORKER_TYPE
        },
        {
            'name': flower_deployment.metadata.name,
            'replicas': flower_deployment.spec.replicas,
            'kind': constants.DEPLOYMENT_KIND,
            'type': constants.FLOWER_TYPE
        },
        {
            'name': flower_svc.metadata.name,
            'spec': flower_svc.spec.to_dict(),
            'kind': constants.SERVICE_KIND,
            'type': constants.FLOWER_TYPE
        }
    ]

    return {
        'children': children,
        'children_count': len(children),
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


@kopf.timer('celeryproject.org', 'v1alpha1', 'celery',
            initial_delay=50000, interval=100000, idle=10)
def message_queue_length(spec, status, **kwargs):
    flower_svc_host = "http://192.168.64.2:32289"
    url = f"{flower_svc_host}/api/queues/length"
    response = requests.get(url=url)
    if response.status_code == 200:
        return response.json().get('active_queues')

    return {
        "queue_length": None
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


def validate_stuff(spec):
    """
        1. If the deployment/svc already exists, k8s throws error
        2. Response and spec classes and enums
    """
    pass


def validate_spec(spec):
    """
        Validates the incoming spec
        @returns - True/False, Error Message
    """
    # size = spec.get('size')
    # if not size:
    #     return size, "Size must be set"
    return None, None
