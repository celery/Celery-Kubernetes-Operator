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
    celery_config = spec['celery_config']
    worker_spec_dict = {
        'args': args_list_from_spec_params(
            celery_app=spec['celery_app'],
            queues=celery_config['queues'],
            loglevel=celery_config['loglevel'],
            concurrency=celery_config['concurrency']
        ),
        'command': ["celery"],
        'image': spec['image'],
        'name': spec['worker_name'],
        'resources': celery_config['resources']
    }

    # JSON way of submitting spec to deploy/patch
    patch_body = {
        "spec": {
            "replicas": celery_config['num_of_workers'],
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
    flower_config = spec['flower_config']

    flower_spec_dict = {
        'args': [spec['celery_app']],
        'command': ['flower'],
        'image': spec['image'],
        'name': f"{spec['worker_name']}-flower",
        'ports': [
            {"containerPort": 5555}
        ],
        'resources': flower_config['resources']
    }

    # JSON way of submitting spec to deploy/patch
    patch_body = {
        "spec": {
            "replicas": flower_config['replicas'],
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
                "run": f"{spec['app_name']}-flower"
            }
        }
    }

    svc_name = status['create_fn']['children']['flower_service']
    api.patch_namespaced_service(
        svc_name, namespace, patch_body
    )

    return svc_name
