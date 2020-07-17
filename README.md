# Celery-Kubernetes-Operator(WIP)
A basic Celery operator written in Python. To be used to manage Celery applications on a Kubernetes cluster. It is being built as a demo project to proposed EuroPython 2020 [proposal](https://ep2020.europython.eu/talks/BbvZjFa-advanced-infrastructure-management-in-kubernetes-using-python/). 
Beyond the conference based on feedback, it'll be pursued to be a production ready project.

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

# Instructions to see this operator in action

1. Install [minikube](https://kubernetes.io/docs/tasks/tools/install-minikube/). This project is developed and tested only on minikube as of now.
2. Run `minikube start --driver=hyperkit` to start minikube. It is going to download VM boot image and setup a single node kubernetes cluster for you.

We need to build our docker images for celery app and the operator. They are going to be used in creating worker, flower and operator deployments.

3. Switch to minikube docker daemon using `eval $(minikube -p minikube docker-env)` in your shell. This is important so that minikube doesn't try to pull images from remote registry. We're going to use our locally built images for the demo. Not using any remote registry. Image pull policy in all deployment spec is set to `Never` right now
4. For building operator image, run `docker build -t celery-operator .`
5. For building celery-flask example application image, run `docker build -t example-image -f example/Dockerfile .`
6. Apply celery CRD using `kubectl apply -f deploy/crd.yaml`. It'll enable Kubernetes to understand the custom resource named Celery
7. Create the custom resource(CR) using `kubectl apply -f deploy/cr.yaml`. It'll create the Celery resource for you.
8. Apply `kubectl apply -f deploy/rbac.yaml` to give operator necessary permissions to watch, create and modify resources on minikube K8s cluster
9. We need to setup a redis deployment in the cluster before deploying the operator. As soon as worker and flower deployment come up, they'd need a broker ready to connect to. We're using redis as broker for the demo. A deployment and service for redis can be created using `kubectl apply -f templates/static/redis-master.yaml`. 
10. Now to take action on newly created CR, we are going to deploy operator. Apply `kubectl apply -f deploy/operator.yaml` to setup the operator deployment. 

As soon as pod for the operator comes up, it notices the Celery resource and handles the creation event to setup worker deployments flower deployment and exposing Flower svc as a NodePort type to be accessed from outside the cluster. 
You could do `minikube service celery-crd-example-flower --url` to get the url, open it in web browser to see if the newly created workers are in healthy state or not.

To see the custom autoscaling in action, we need to create another deployment - A flask application that keeps pushing messages in the redis broker continuously.

11. Do `kubectl apply -f templates/static/flask-example.yaml` to run a flask example which is going to fill the queue with messages. As soon as each queue length goes beyond the average specified in CR, it'll trigger autoscaling of workers. If you delete the flask deployment(`kubectl delete -f templates/static/flask-example.yaml`), number of messages in queue will come down and hence decreasing the number of workers as well in the process.

# Directory Structure

# Inspiration

This project is inspired by proposal [Issue#24](https://github.com/celery/ceps/issues/24) in CEPS(Celery Enhancement Proposals) and @jmdacruz's POC [project](https://github.com/jmdacruz/celery-k8s-operator/)
