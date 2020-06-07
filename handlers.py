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

    # 2. configmap creation
    path = os.path.join(os.path.dirname(__file__), 'celery_deployment.yaml')
    tmpl = open(path, 'rt').read()
    text = tmpl.format(name=name, size=size)
    data = yaml.safe_load(text)

    api = kubernetes.client.CoreV1Api()
    # obj = api.create_namespaced_persistent_volume_claim(
    #     namespace=namespace,
    #     body=data,
    # )

    logger.info(f"PVC child is created: %s", obj)

    # 3. Deployment for celery application


def validate_spec(spec):
    size = spec.get('size')
    if not size:
        return size, "Size must be set"
    return None, None
