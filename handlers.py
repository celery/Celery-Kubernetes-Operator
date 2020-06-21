import os
import kopf
import kubernetes

from deployment_utils import (
    deploy_celery_workers,
    deploy_flower,
    expose_flower_service
)


@kopf.on.create('grofers.com', 'v1', 'celeryapplications')
def create_fn(spec, name, namespace, logger, **kwargs):
    """
        TODO -
        1. Validate the spec for incoming obj
        2. Create a config-map for celery
        3. Instantiate a celery Deployment with the specified parameters
        4. Define and expolre a flower Service to keep a watch on those metrics
        5. Scale/Downscale on the basis of task queue length
    """
    result = {}
    children_count = 0
    status = 'Creating'

    # 1. Validation of spec
    val, err_msg = validate_spec(spec)
    if err_msg:
        status = 'Failed validation'
        raise kopf.PermanentError(f"{err_msg}. Got {val}")

    api = kubernetes.client.CoreV1Api()
    apps_api_instance = kubernetes.client.AppsV1Api()

    # 2. Deployment for celery workers
    worker_deployment_name = deploy_celery_workers(
        apps_api_instance, namespace, spec, logger
    )
    result.update({'worker_deployment': worker_deployment_name})
    children_count += 1

    # 3. Deployment for flower
    flower_deployment_name = deploy_flower(
        apps_api_instance, namespace, spec, logger
    )
    result.update({'flower_deployment': flower_deployment_name})
    children_count += 1

    # 4. Expose flower service
    flower_svc_name = expose_flower_service(
        api, namespace, spec, logger
    )
    result.update({'flower_service': flower_svc_name})
    children_count += 1
    status = 'Success'

    return {
        'status': status,
        'children_count': children_count,
        'children': result
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
