# Celery-Kubernetes-Operator(WIP)
A basic Celery operator written in Python. To be used to manage Celery applications on a Kubernetes cluster. It is being built as a demo project to proposed EuroPython 2020 [proposal](https://ep2020.europython.eu/talks/BbvZjFa-advanced-infrastructure-management-in-kubernetes-using-python/). 
Beyond the conference, it'll be pursued to be a production ready project.

Please report an issue for improvement suggestions/feedback. This operator is being written with the help of [KOPF](https://github.com/zalando-incubator/kopf) framework open sourced by Zalando SE.

# Project Scope
The general idea is to bridge the gap between infrastructure and application developers where application developers can just spec out a simple celery deployment yaml and have to do nothing more than `kubectl apply -f <file_name>`to spin up their own celery cluster.

It aims to have following things in place-
1. A Custom Resource Definition(CRD) to spec out a Celery and Flower deployment having all the options that they support.
2. A custom controller implementation that registers and manages self-healing capabilities of custom Celery object for these operations
    - CREATE - Creates the worker and flower deployments along with exposing a native Service object for Flower
    - UPDATE - Reads the CRD modifications and updates the running deployments using specified strategy
    - DELETE - Deletes the custom resource and all the child deployments
3. Keep a watch on important metrics(queue length, cpu, memory etc) using flower(and native K8s solutions) to autoscale/downscale the number of workers on specified constraints.

# Directory Structure

# Inspiration

This project is inspired by proposal [Issue#24](https://github.com/celery/ceps/issues/24) in CEPS(Celery Enhancement Proposals) and @jmdacruz's POC [project](https://github.com/jmdacruz/celery-k8s-operator/)
