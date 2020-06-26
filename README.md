# Celery-Kubernetes-Operator(WIP)
A basic Celery operator written in Python. To be used to manage simple Celery applications on a Kubernetes cluster. It is being built as a demo project to proposed EuroPython 2020 proposal. With some minor tweaks, to be used in Grofers production as well in the future. This operator is being written with the help of [KOPF](https://github.com/zalando-incubator/kopf) framework open sourced by Zalando SE.

# Project Scope
The general idea is to bridge the gap between infrastructure and application developers where application developers can just spec out a simple celery deployment yaml and have to do nothing more than `kubectl apply -f <file_name>`to spin up their own celery cluster.

It aims to have following things in place-
1. A Custom Resource Definition(CRD) to spec out a Celery deployment having (but not limited to) these attributes -
    - Celery image
    - Celery app module name
    - Queue name
    - Resource Constraints(lim_cpu, req_cpu, lim_mem, req_mem)
    - Log Level
    - Number of workers
    - Concurrency
    - Basic Flower setup configuration for monitoring
2. A custom controller implementation that registers and manages self-healing capabilities of custom Celery resource for these operations
    - CREATE - Creates the worker and flower deployments along with exposing a native Service object for Flower
    - UPDATE - Reads the CRD modifications and updates the running deployments using RollingUpdate strategy
    - DELETE - Deletes the custom resource and all the child deployments
3. Keep a watch on CPU/Memory metrics of resource pod and autoscale/downscale the number of workers on given constraints

# Current Progress

1. `crd.yaml` to spec out a simple celery deployment available under `templates/` directory.
2. Create and update handlers are defined and act accordingly as custom resource is created and updated. Deletion works automagically, thanks to KOPF adopt functions.

# Directory Structure

# Inspiration

This project is inspired by proposal [Issue#24](https://github.com/celery/ceps/issues/24) in CEPS(Celery Enhancement Proposals)
