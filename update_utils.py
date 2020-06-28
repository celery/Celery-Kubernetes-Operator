from models.worker_spec import (
    args_list_from_spec_params
)


def update_all_deployments(api, apps_api_instance, spec, status, namespace):
    return {
        'worker_deployment': update_celery_deployment(
            apps_api_instance, spec, status, namespace
        ),
        'flower_deployment': update_flower_deployment(
            apps_api_instance, spec, status, namespace
        ),
        'flower_service': update_flower_service(
            api, spec, status, namespace
        )
    }


def update_celery_deployment(apps_api_instance, spec, status, namespace):
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

    deployment_name = status['create_fn']['children']['worker_deployment']
    apps_api_instance.patch_namespaced_deployment(
        deployment_name, namespace, patch_body
    )

    return deployment_name


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

    deployment_name = status['create_fn']['children']['flower_deployment']
    # TODO: Use a try catch here
    apps_api_instance.patch_namespaced_deployment(
        deployment_name, namespace, patch_body
    )

    return deployment_name


def update_flower_service(api, spec, status, namespace):
    # Only app_name change will affect flower service
    patch_body = {
        "spec": {
            "selector": {
                "run": f"{spec['common']['appName']}-flower"
            }
        }
    }

    svc_name = status['create_fn']['children']['flower_service']
    api.patch_namespaced_service(
        svc_name, namespace, patch_body
    )

    return svc_name
