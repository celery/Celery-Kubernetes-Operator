## Celery Kubernetes Operator - High Level Architecture

### Overview

[Celery](https://docs.celeryproject.org/en/stable/) is a popular distributed task-queue system written in Python. To run Celery in production on Kubernetes, there are multiple manual steps involved like -
- Writing deployment spec for workers
- Setting up monitoring using [Flower](https://flower.readthedocs.io/en/latest/)
- Setting up Autoscaling

Apart from that, there's no consistent way to setup multiple clusters, everyone configures their own way which could create problems for infrastructure teams to manage and audit later.
This project attempts to solve(or automate) these issues. It is aiming to bridge the gap between application engineers and infrastructure operators who manually manage the celery clusters.

Moreover, since Celery is written in Python, we plan to use open source [KOPF](https://github.com/zalando-incubator/kopf)(Kubernetes Operator Pythonic Framework) to write the custom controller implementation.

### Scope

1. Provide a Custom Resource Definition(CRD) to spec out a Celery and Flower deployment having all the configuration options that they support.
2. A custom controller implementation that registers and manages self-healing capabilities of custom Celery resource for these operations -
    + CREATE - Creates the worker and flower deployments along with exposing a native Service object for Flower
    + UPDATE - Reads the CRD modifications and updates the running deployments using specified strategy
    + DELETE - Deletes the custom resource and all the child deployments
3. Support worker autoscaling/downscaling based on resource constraints(cpu, memory) and task queue length automatically.

Discussions involving other things that this operator should do based on your production use-case are welcome.

### Diagram

![CKO Arch Diagram](https://i.imgur.com/dTBuG58.png)

### Workflow

End user starts by writing and creating a YAML spec for the desired celery cluster. Creation event is listened by the Creation Handler(KOPF based) which creates deployment for workers, flower and a Service object to expose flower UI to external users.

Assuming we have broker in place, any user facing application can start pushing messages to broker now and celery workers will start processing them.

User can update the custom resource, when that happens, updation handler listening to the event will patch the relevant deployments for change. Rollout strategy can be default or to be specified by user in the spec.

Both creation and updation handlers will return their statuses to be stored in parent resource's status field. Status field will contain the latest status of the cluster children at all times.

User can choose to setup autoscaling of workers by resource constraints(CPU, Memory) or broker queue length. Operator will automatically take care of creating an HPA or use KEDA based autoscaling(See [Autoscaling](#Autoscaling) section below) to make that happen.

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
    + `rolloutStrategy` - Rollout strategy to spawn new worker pods
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


### Async KOPF Handlers(Controller Implementation)
This section contains brief overview of creation and updation handlers which are going to react on celery resource creation and updation respectively and return their status to be stored back as resource's status.

#### Creation Handler
Generates deployment spec for worker and flower deployments dynamically based on incoming parameters specified in custom celery resource. Also creates the flower service to expose flower UI. Status of each children is sent back to be stored under parent resource status field.

Additionally, it might handle the HPA object creation too if the scaling is to be done on native metrics(CPU and Memory utilization).

#### Updation Handler
Updates deployment spec for worker and flower deployments(and service + HPA) dynamically and patch them. Status of each children is sent back to be stored under parent resource status field.

### Autoscaling
This section covers how operator is going to handle autoscaling. We plan to supporting scaling based on following two metrics.

#### Native Metrics(CPU, Memory Utilization)
If workers need to be scaled only on CPU/Memory constraints, we can simply create an HPA object in creation/updation handlers and it'll take care of scaling relevant worker deployment automatically. HPA supports these two metrics out of the box. For custom metrics, we need to do additional work.

#### Broker Queue Length(KEDA based autoscaling)
Queue Length based scaling needs custom metric server for an HPA to work. [KEDA](https://keda.sh/docs/1.5/concepts/) is a wonderful option because it is built for the same. It provides the [scalers](https://keda.sh/docs/1.5/scalers/) for all the popular brokers(RabbitMQ, Redis, Amazon SQS) supported in Celery.

KEDA provides multiple ways to be deployed on a Kubernetes cluster - Helm, Operator Hub and Yaml. Celery Operator can package KEDA along with itself for distribution.

### Deployment Strategy

Probably the best way would be distribute a Helm Chart which packages CRD, controller and KEDA together(More to be explored here). We'll also support YAML apply based deployments.

Additionally, Helm approach is extensible in the sense that we can package additional components like preferred broker(Redis, RMQ, SQS) as well to start with Celery on Kubernetes out of the box without much efforts.

### Want to Help?
If you're running celery on a Kubernetes cluster, your inputs to how you manage applications will be valuable. You could contribute to the discussion by creating a new issue on the repo.

### Motivation

Celery is one of the most popular distributed task queue system written in Python. Kubernetes is the de-facto standard for container-orchestration. We plan to write this operator to help manage celery applications gracefully and with ease on a Kubernetes cluster.

Moreover, we wish to build this operator with Python. Kubernetes is written in golang. There is a good learning curve to understand internals and write(also maintain) an operator with Go. With the help of KOPF like tool, it'll be good to have Celery spearhead the Python ecosystem for developing production ready Kubernetes extensions. It'll motivate community to overcome the learning barrier and create useful libraries, tools and other operators while staying in Python ecosystem.

### TODOs for Exploration
- [ ] Helm chart to install the operator along with a broker of choice
- [ ] Add role based access control section for the operator
- [ ] Ingress Resource
- [ ] KEDA Autoscaling Implementation
- [ ] Create new issue thread to discuss Celery use-cases
- [ ] What should not be in scope of celery operator?
