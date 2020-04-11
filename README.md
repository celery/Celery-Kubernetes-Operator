# Celery-Kubernetes-Operator
A basic Celery operator to be written with native python kubernetes client(WIP). To be used to manage Celery applications on a Kubernetes cluster.

# Project Scope
This project aims to have following things in place-
1. A Custom Resource Definition(CRD) to spec out a Celery deployment having(not limited to) these attributes -
    - Celery app module name
    - Broker URL
    - Worker Class(sync, gevent etc)
    - Queue name
    - Resource Constraints(lim_cpu, req_cpu, lim_mem, req_mem)
    - Log Level
    - Number of threads
    - Flower setup configuration(if any)
2. A custom controller implementation that registers and manages self-healing capabilities of custom Celery resource for these operations
    - CREATE - Creates the Celery CRD resource along with exposing a native Service object for Flower
    - UPDATE - Reads the CRD modifications and updates the running Celery resource appropriately(delete and re-create)
    - DELETE - Deletes the resource and flower service
3. Keep a watch on CPU/Memory metrics of resource pod and autoscale/downscale the number of workers on given constraints

# Directory Structure

# Inspiration

This project is inspired by proposal [Issue#24](https://github.com/celery/ceps/issues/24) in CEPS(Celery Enhancement Proposals)
