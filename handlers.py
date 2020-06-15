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

    # 1. Validation of spec
    val, err_msg = validate_spec(spec)
    if err_msg:
        raise kopf.PermanentError(f"{err_msg}. Got {val}")

    api = kubernetes.client.CoreV1Api()
    # 2. Deployment for celery workers
    deploy_celery_workers(api, namespace, spec)
    # 3. Deployment for flower
    deploy_flower(api, namespace, spec)
    # 4. Expose flower service
    expose_flower_service(api, namespace, spec)


def deploy_celery_workers(api, namespace, spec):
    path = os.path.join(os.path.dirname(__file__), 'templates/celery_worker_deployment.yaml')
    tmpl = open(path, 'rt').read()

    celery_config = spec['celery_config']
    req_resources = spec['resources']['requests']
    lim_resources = spec['resources']['limits']

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
        lim_cpu=lim_resources['lim_cpu'],
        lim_mem=lim_resources['lim_mem'],
        req_cpu=req_resources['req_cpu'],
        req_mem=req_resources['req_mem']
    )
    data = yaml.safe_load(text)

    obj = api.create_namespaced_deployment(
        namespace=namespace,
        body=data
    )
    logger.info(f"Celery worker deployment created: %s", obj)


def expose_flower_service(api, namespace, spec):
    path = os.path.join(os.path.dirname(__file__), 'templates/flower_service.yaml')
    tmpl = open(path, 'rt').read()

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name'],
        flower_port=flower_port
    )
    data = yaml.safe_load(text)

    obj = api.create_namespaced_service(
        namespace=namespace,
        body=data
    )
    logger.info(f"Flower Service has been created: %s", obj)


def deploy_flower(api, namespace, spec):
    path = os.path.join(os.path.dirname(__file__), 'templates/flower_deployment.yaml')
    tmpl = open(path, 'rt').read()

    flower_config = spec['flower_config']
    flower_port = 5555
    req_resources = spec['resources']['requests']
    lim_resources = spec['resources']['limits']
    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name'],
        celery_app=spec['celery_app'],
        image=spec['image'],
        flower_port=flower_port,
        replicas=flower_config['replicas'],
        lim_cpu=lim_resources['lim_cpu'],
        lim_mem=lim_resources['lim_mem'],
        req_cpu=req_resources['req_cpu'],
        req_mem=req_resources['req_mem']
    )
    data = yaml.safe_load(text)

    obj = api.create_namespaced_deployment(
        namespace=namespace,
        body=data
    )
    logger.info(f"Flower deployment has been created: %s", obj)


def validate_spec(spec):
    """
        Validates the incoming spec
        @returns - True/False, Error Message
    """
    size = spec.get('size')
    if not size:
        return size, "Size must be set"
    return None, None
