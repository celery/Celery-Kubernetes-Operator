import os
import kopf
import yaml


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
        image=spec['image'],
        worker_name=celery_config['worker_name'],
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


def deploy_flower(apps_api, namespace, spec, logger):
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


def expose_flower_service(api, namespace, spec, logger):
    path = os.path.join(
        os.path.dirname(__file__),
        'templates/services/flower_service.yaml'
    )
    tmpl = open(path, 'rt').read()

    text = tmpl.format(
        namespace=namespace,
        app_name=spec['app_name']
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
