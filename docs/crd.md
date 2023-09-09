Celery spec defines the desired state and configuration parameters for running a custom celery resource in a Kubernetes cluster.

It currently supports these parameters-

- `image` [Required]- Container image name to run in the worker and flower deployments
- `imagePullPolicy` - Image pull policy. One of Always, Never, IfNotPresent
- `imagePullSecrets` - ImagePullSecrets is an optional list of references to secrets in the same namespace to use for pulling any of the images used. If specified, these secrets will be passed to individual puller implementations for them to use. Read more: https://kubernetes.io/docs/concepts/containers/images#specifying-imagepullsecrets-on-a-pod
- `appName` [Required]- Application name for worker and flower deployments, will be suffixed accordingly
- `celeryApp` [Required] - Celery app instance to use (e.g. module.celery_app_attr_name)
- `celeryVersion` - Celery version
- `workerReplicas` - Number of worker pods to be run. Default is 1
- `flowerReplicas` - Number of flower pods to be run. Default is 1
- `workerSpec` - Worker deployment-specific parameters
    + `args` - Arguments to the celery worker command. The docker image's CMD is used if this is not provided. Similar to: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell
    + `env` - EnvVar represents an environment variable present in a Container. Similar to: https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/
    + `nodeSelector` - A map of key-value pairs. For the pod/worker to be eligible to run on a node, the node must have each of the indicated key-value pairs as labels. Read more: https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
    + `resources` - Compute Resources required by the worker container. Cannot be updated. Read more: https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
- `flowerSpec` - Flower deployment specific parameters
    + `args` - Arguments to the celery flower command. Similar to: https://kubernetes.io/docs/tasks/inject-data-application/define-command-argument-container/#running-a-command-in-a-shell
    + `env` - EnvVar represents an environment variable present in a Container. Similar to: https://kubernetes.io/docs/tasks/inject-data-application/define-environment-variable-container/
    + `nodeSelector` - A map of key-value pairs. For the pod/worker to be eligible to run on a node, the node must have each of the indicated key-value pairs as labels. Read more: https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/
    + `resources` - Compute Resources required by the worker container. Cannot be updated. Read more: https://kubernetes.io/docs/concepts/configuration/manage-compute-resources-container/
    + `service` - Service defines the template for the associated Kubernetes Service object for exposing Flower UI. Read more: https://kubernetes.io/docs/concepts/services-networking/service/
- `initContainers` - List of initialization containers belonging to the worker and flower pods. Read more: https://kubernetes.io/docs/concepts/workloads/pods/init-containers/
- `volumes` - Define some extra Kubernetes Volumes for Celery cluster pods. Accepts a list of volumes that can be mounted by containers belonging to the pod. More info: https://kubernetes.io/docs/concepts/storage/volumes
- `volumeMounts` - Define some extra Kubernetes Volume mounts for Celery cluster pods. More info: https://kubernetes.io/docs/concepts/storage/volumes/
- `livenessProbe` - Periodic probe of container liveness. Read more: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/
- `readinessProbe` - Periodic probe of container readiness. Read more: https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/