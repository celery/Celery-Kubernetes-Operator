import os
import kopf
import yaml


def deploy_celery_workers(apps_api, namespace, spec, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        '../kubernetes/templates/deployments/celery_worker_deployment.yaml'
    )
    tmpl = open(path, 'rt').read()

    celery_config = spec['workerSpec']
    req_resources = celery_config['resources']['requests']
    lim_resources = celery_config['resources']['limits']

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['common']['appName'],
        celery_app=spec['common']['celeryApp'],
        image=spec['common']['image'],
        num_of_workers=celery_config['numOfWorkers'],
        queues=celery_config['queues'],
        loglevel=celery_config['logLevel'],
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

    logger.info(
        f"Deployment for celery workers successfully created with name: %s",
        deployed_obj.metadata.name
    )

    return deployed_obj


def deploy_flower(apps_api, namespace, spec, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        '../kubernetes/templates/deployments/flower_deployment.yaml'
    )
    tmpl = open(path, 'rt').read()

    flower_config = spec['flowerSpec']
    req_resources = flower_config['resources']['requests']
    lim_resources = flower_config['resources']['limits']
    text = tmpl.format(
        namespace=namespace,
        app_name=spec['common']['appName'],
        celery_app=spec['common']['celeryApp'],
        image=spec['common']['image'],
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
    logger.info(
        f"Deployment for celery flower successfully created with name: %s",
        deployed_obj.metadata.name
    )

    return deployed_obj


def expose_flower_service(api, namespace, spec, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        '../kubernetes/templates/services/flower_service.yaml'
    )
    tmpl = open(path, 'rt').read()

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['common']['appName']
    )
    data = yaml.safe_load(text)
    mark_as_child(data)

    svc_obj = api.create_namespaced_service(
        namespace=namespace,
        body=data
    )
    logger.info(
        f"Flower service successfully created with name: %s",
        svc_obj.metadata.name
    )
    return svc_obj


def mark_as_child(data):
    """
        Marks the incoming data as child of celeryapplications
    """
    kopf.adopt(data)
