import constants
from models.worker_spec import (
    args_list_from_spec_params
)


def update_all_deployments(api, apps_api_instance, spec, status, namespace):
    worker_deployment = update_worker_deployment(
        apps_api_instance, spec, status, namespace
    )

    flower_deployment = update_flower_deployment(
        apps_api_instance, spec, status, namespace
    )

    flower_svc = update_flower_service(
        api, spec, status, namespace
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
        'status': constants.STATUS_UPDATED
    }


def get_curr_deployment_from_handler_status(handler_name, status, child_type):
    """
        Get current deployment name from handler's status
        @param: handler_name - which handler to get from
        @param: child_type - worker or flower
        @returns: current deployment name
    """
    for child in status.get(handler_name).get('children'):
        if child.get('type') == child_type and child.get('kind') == constants.DEPLOYMENT_KIND:  # NOQA
            return child.get('name')

    return None


def get_curr_deployment_name(status, child_type):
    """
        Get current deployment name from parent's status
        @param: child_type - worker or flower
        @returns: current deployment name
    """
    if status.get('update_fn'):
        return get_curr_deployment_from_handler_status('update_fn', status, child_type)

    return get_curr_deployment_from_handler_status('create_fn', status, child_type)


def update_worker_deployment(apps_api_instance, spec, status, namespace):
    worker_spec = spec['workerSpec']
    worker_spec_dict = {
        'args': args_list_from_spec_params(
            celery_app=spec['common']['celeryApp'],
            queues=worker_spec['queues'],
            loglevel=worker_spec['logLevel'],
            concurrency=worker_spec['concurrency']
        ),
        'command': ["celery"],
        'image': spec['common']['image'],
        'name': f"{spec['common']['appName']}-celery-worker",
        'resources': worker_spec['resources']
    }

    # JSON way of submitting spec to deploy/patch
    patch_body = {
        "spec": {
            "replicas": worker_spec['numOfWorkers'],
            "template": {
                "spec": {
                    "containers": [
                        worker_spec_dict
                    ]
                }
            }
        }
    }

    worker_deployment_name = get_curr_deployment_name(
        status, constants.WORKER_TYPE
    )

    return apps_api_instance.patch_namespaced_deployment(
        worker_deployment_name, namespace, patch_body
    )


def update_flower_deployment(apps_api_instance, spec, status, namespace):
    flower_spec = spec['flowerSpec']

    flower_spec_dict = {
        'args': [spec['common']['celeryApp']],
        'command': ['flower'],
        'image': spec['common']['image'],
        'name': f"{spec['common']['appName']}-flower",
        'ports': [
            {"containerPort": 5555}
        ],
        'resources': flower_spec['resources']
    }

    # JSON way of submitting spec to deploy/patch
    patch_body = {
        "spec": {
            "replicas": flower_spec['replicas'],
            "template": {
                "spec": {
                    "containers": [
                        flower_spec_dict
                    ]
                }
            }
        }
    }

    flower_deployment_name = get_curr_deployment_name(
        status, constants.FLOWER_TYPE
    )

    return apps_api_instance.patch_namespaced_deployment(
        flower_deployment_name, namespace, patch_body
    )


def update_flower_service(api, spec, status, namespace):
    # Only app_name change will affect flower service
    patch_body = {
        "spec": {
            "selector": {
                "run": f"{spec['common']['appName']}-flower"
            }
        }
    }

    flower_svc_name = get_curr_deployment_name(
        status, constants.FLOWER_TYPE
    )  # flower svc is named same as flower deployment
    return api.patch_namespaced_service(
        flower_svc_name, namespace, patch_body
    )
