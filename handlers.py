import os
import kopf
import kubernetes
from collections import namedtuple

from deployment_utils import (
    deploy_celery_workers,
    deploy_flower,
    expose_flower_service
)
from update_utils import (
    update_all_deployments,
    update_celery_deployment,
    update_flower_deployment
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


@kopf.on.update('grofers.com', 'v1', 'celeryapplications')
def update_fn(spec, status, namespace, logger, **kwargs):
    # TODO - app name still cannot be updated(Fix that)
    diff = kwargs.get('diff')
    modified_spec = get_modified_spec_object(diff)

    api = kubernetes.client.CoreV1Api()
    apps_api_instance = kubernetes.client.AppsV1Api()

    if modified_spec.common_spec:
        # if common spec was updated, need to update all deployments
        return update_all_deployments(
            api, apps_api_instance, spec, status, namespace
        )
    else:
        result = {}
        if modified_spec.celery_spec:
            result.update({
                'worker_deployment': update_celery_deployment(
                    apps_api_instance, spec, status, namespace
                )
            })

        if modified_spec.flower_spec:
            result.update({
                'flower_deployment': update_flower_deployment(
                    apps_api_instance, spec, status, namespace
                )
            })
        return result


def get_modified_spec_object(diff):
    """
        @param: diff - arg provided by kopf when an object is updated
        diff format - Tuple of (op, (fields tuple), old, new)
        @returns ModifiedSpec namedtuple signifying which spec was updated
    """
    common_spec_checklist = ['app_name', 'celery_app', 'image', 'worker_name']
    celery_config_checklist = ['celery_config']
    flower_config_checklist = ['flower_config']

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
    ModifiedSpec = namedtuple('ModifiedSpec', ['common_spec', 'celery_spec', 'flower_spec'])

    return ModifiedSpec(
        common_spec=common_spec_modified,
        celery_spec=celery_spec_modified,
        flower_spec=flower_spec_modified
    )


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
