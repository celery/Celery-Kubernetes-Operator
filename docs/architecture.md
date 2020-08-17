## Celery Kubernetes Operator - Architecture Document

### Overview

[Celery](https://docs.celeryproject.org/en/stable/) is a popular distributed task-queue system written in Python. To run Celery in production on Kubernetes, there are multiple manual steps involved like -
- Writing deployment spec for workers
- Setting up monitoring using [Flower](https://flower.readthedocs.io/en/latest/)
- Setting up autoscaling configuration

Apart from that, there's no consistent way to setup multiple clusters, everyone configures there own way which could create problems for infrastructure teams to manage and audit later.

This project attempts to solve(or automate) these issues. It is aiming to bridge the gap between application engineers and infrastructure operators who manually manage the celery clusters.

### Scope

1. Provide a Custom Resource Definition(CRD) to spec out a Celery and Flower deployment having all the configuration options that they support.
2. A custom controller implementation that registers and manages self-healing capabilities of custom Celery resource for these operations -
- CREATE - Creates the worker and flower deployments along with exposing a native Service object for Flower
- UPDATE - Reads the CRD modifications and updates the running deployments using specified strategy
- DELETE - Deletes the custom resource and all the child deployments
3. Support worker autoscaling/downscaling based on resource constraints(cpu, memory) and task queue length automatically.

Discussions involving other things that this operator should do based on your production use-case are welcome.

### Diagram

### Components

#### Worker Deployment
A Kubernetes [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) to manage celery worker pods/replicaset. These workers consume the tasks from broker and process them.

#### Flower Deployment
A Kubernetes [Deployment](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) to manage flower pods/replicaset. Flower is de-facto standard to monitor and remote control celery.

#### Flower Service
Expose flower UI to an external IP through a Kubernetes [Service](https://kubernetes.io/docs/concepts/services-networking/service/) object. We should additionally explore [Ingress](https://kubernetes.io/docs/concepts/services-networking/ingress/) as well(TODO).

#### Celery CRD(Custom Resource Definition)
CRDs are a native way to extend Kubernetes APIs to recognize custom applications/objects. Celery CRD will contain the schema for celery cluster to be setup.

We plan to have following objects in place with their high level description -
- `common` - common configuration parameters for Celery cluster
    + `image` - Celery application image to be run
    + `imagePullPolicy` - [Always, Never, IfNotPresent]
    + `imagePullSecrets` - to pull the image from a private registry
    + `volumeMounts` - describes mounting of a volume within container.
    + `volumes` - describes a volume to be used for storage
    + `celeryVersion` - Celery version
    + `appName` - App name for worker and flower deployments
    + `celeryApp` - celery app instance to use (e.g. module.celery_app_attr_name)
- `workerSpec` - worker deployment specific parameters
    + `numOfWorkers` - Number of workers to launch initially
    + `args` - array of arguments(all celery supported options) to pass to worker process in container  (TODO: Entrypoint vs args vs individual params)
    + `resources` - optional argument to specify cpu, mem constraints for worker deployment
- `flowerSpec` - flower deployment and service specific parameters
    + `replicas` - Number of replicas for flower deployment
    + `args` - array of arguments(all flower supported options) to pass to flower process in the container
    + `servicePort` - Port to expose flower UI in the container
    + `serviceType` - [Default, NodePort, LoadBalancer]
    + `resources` - optional argument to specify cpu, mem constraints for flower deployment
- `scaleTargetRef` - array of items describing auto scaling targets
    + `kind` - which application kind to scale (worker, flower)
    + `minReplicas` - min num of replicas
    + `maxReplicas` - max num of replicas
    + `metrics` - list of metrics to monitor
        * `name` - Enum type (memory, cpu, task_queue_length)
        * `target` - target values
            - `type` - [Utilization, Average Value]
            - `averageValue/averageUtilization` - Average values to maintain

A more detailed version/documentation for CRD spec is underway.

#### Celery CR(Custom Resource)
Custom Resource Object for a Celery application. Multiple clusters will have multiple custom resource objects.

#### Custom Controller
[Custom controller](https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/#custom-controllers) implementation to manage Celery applications(CRs). Contains the code for creation, updation, deletion and scaling handlers of the cluster.


### Controller Handlers(Controller Implementation Details)

#### Creation Handler

#### Updation Handler

#### Scaling Handlers

### Workflow

### Want to Help?
If you're running celery on a Kubernetes cluster, your inputs to how you manage applications will be valuable. You could contribute to the discussion on this issue - (TODO -- ISSUE)

### Motivation

Celery is one of the most popular distributed task queue system written in Python. Kubernetes is the de-facto standard for container-orchestration. We plan to write this operator to help manage celery applications gracefully and with ease on a Kubernetes cluster.

Moreover, we wish to build this operator with Python. Kubernetes is written in golang. There is a good learning curve to understand internals and write(also maintain) an operator with Go. With the help of KOPF like tool, it'll be good to have Celery spearhead the Python ecosystem for developing production ready Kubernetes extensions. It'll motivate community to overcome the learning barrier and create useful libraries, tools and other operators while staying in Python ecosystem.

### TODOs for Exploration
- [ ] Helm chart to install the operator along with a broker of choice
- [ ] Role based access control section for the operator
- [ ] Ingress Resource
- [ ] KEDA Autoscaling
- [ ] Create new issue thread to discuss Celery use-cases
- [ ] What is not in scope of operator
