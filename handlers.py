import os
import kopf
import kubernetes
import yaml


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

    flower_port = 5555
    # 3. Deployment for flower
    flower_deployment_name = deploy_flower(
        apps_api_instance, namespace, spec, flower_port, logger
    )
    result.update({'flower_deployment': flower_deployment_name})
    children_count += 1

    # 4. Expose flower service
    flower_svc_name = expose_flower_service(
        api, namespace, spec, flower_port, logger
    )
    result.update({'flower_service': flower_svc_name})
    children_count += 1
    status = 'Success'

    return {
        'status': status,
        'children_count': children_count,
        'children': result
    }


def deploy_celery_workers(apps_api, namespace, spec, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        'templates/deployments/celery_worker_deployment.yaml'
    )
    tmpl = open(path, 'rt').read()

    celery_config = spec['celery_config']
    req_resources = celery_config['resources']['requests']
    lim_resources = celery_config['resources']['limits']

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name'],
        celery_app=spec['celery_app'],
        worker_name=spec['worker_name'],
        image=spec['image'],
        num_of_workers=celery_config['num_of_workers'],
        queues=celery_config['queues'],
        loglevel=celery_config['loglevel'],
        concurrency=celery_config['concurrency'],
        lim_cpu=lim_resources['cpu'],
        lim_mem=lim_resources['memory'],
        req_cpu=req_resources['cpu'],
        req_mem=req_resources['memory']
    )
    data = yaml.safe_load(text)
    mark_as_child(data)

    deployed_obj = apps_api.create_namespaced_deployment(
        namespace=namespace,
        body=data
    )
    deployment_name = deployed_obj.metadata.name
    logger.info(
        f"Deployment for celery workers successfully created with name: %s",
        deployment_name
    )

    return deployment_name


def deploy_flower(apps_api, namespace, spec, flower_port, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        'templates/deployments/flower_deployment.yaml'
    )
    tmpl = open(path, 'rt').read()

    flower_config = spec['flower_config']
    req_resources = flower_config['resources']['requests']
    lim_resources = flower_config['resources']['limits']
    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name'],
        celery_app=spec['celery_app'],
        image=spec['image'],
        flower_port=flower_port,
        replicas=flower_config['replicas'],
        lim_cpu=lim_resources['cpu'],
        lim_mem=lim_resources['memory'],
        req_cpu=req_resources['cpu'],
        req_mem=req_resources['memory']
    )
    data = yaml.safe_load(text)
    mark_as_child(data)

    deployed_obj = apps_api.create_namespaced_deployment(
        namespace=namespace,
        body=data
    )
    deployment_name = deployed_obj.metadata.name
    logger.info(
        f"Deployment for celery flower successfully created with name: %s",
        deployment_name
    )

    return deployment_name


def expose_flower_service(api, namespace, spec, flower_port, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        'templates/services/flower_service.yaml'
    )
    tmpl = open(path, 'rt').read()

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name'],
        flower_port=flower_port
    )
    data = yaml.safe_load(text)
    mark_as_child(data)

    svc_obj = api.create_namespaced_service(
        namespace=namespace,
        body=data
    )
    flower_svc_name = svc_obj.metadata.name
    logger.info(
        f"Flower service successfully created with name: %s",
        flower_svc_name
    )

    return flower_svc_name


def mark_as_child(data):
    """
        Marks the incoming data as child of celeryapplications
    """
    kopf.adopt(data)


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
