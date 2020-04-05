# Celery-Kubernetes-Operator
A basic Celery operator to be written with native python kubernetes client(WIP). To be used to manage Celery applications on a Kubernetes cluster.

# Aim
The ultimate aim of this project is to have following things in place
1. A Custom Resource Definition(CRD) to spec out a Celery Application deployment in a Kubernetes cluster
2. Expose Flower Deployment and Service for the given Celery CRD
3. Controller implementation to connect everything together, maitain the reconciliation loop and handle the autoscaling, downscaling on CPU metric.

# Current Progress

Requirements Finalization

# Directory Structure

# Inspiration

This project is inspired by proposal [Issue#24](https://github.com/celery/ceps/issues/24) in CEPS(Celery Enhancement Proposals)
