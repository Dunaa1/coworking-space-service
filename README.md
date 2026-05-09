# Coworking Space Analytics Service

## Overview

This service is a Flask-based analytics API that reports coworking space usage from a PostgreSQL database. It is containerised with Docker, built and pushed to Amazon ECR via AWS CodeBuild, and deployed to Kubernetes using the manifests in `deployment/`.

## Technology Stack

| Layer | Technology |
|---|---|
| Application | Python 3.10 / Flask |
| Database | PostgreSQL 14 (Kubernetes pod) |
| Container registry | Amazon ECR |
| CI/CD | AWS CodeBuild (triggered on GitHub push) |
| Orchestration | Kubernetes (AWS EKS or local minikube) |
| Observability | AWS CloudWatch Container Insights |

## Build & Release Pipeline

Pushing a commit to the `main` branch triggers CodeBuild, which reads `buildspec.yaml`. The pre-build phase authenticates to ECR using `aws ecr get-login-password`. The build phase runs `docker build` inside the `analytics/` directory and tags the image with `$CODEBUILD_BUILD_NUMBER` (e.g. `1`, `2`, `3`), which gives every build a unique, traceable tag following semantic versioning principles. The post-build phase pushes both the versioned tag and `latest` to ECR. To release a new version, merge your changes to `main` and CodeBuild handles the rest — no manual `docker push` required.

## Deploying to Kubernetes

Apply the manifests in order:

```bash
kubectl apply -f deployment/pvc.yaml
kubectl apply -f deployment/pv.yaml
kubectl apply -f deployment/postgresql-deployment.yaml
kubectl apply -f deployment/postgresql-service.yaml
kubectl apply -f deployment/configmap.yaml
kubectl apply -f deployment/secret.yaml
# Replace <IMAGE_URI> with the ECR URI from the latest CodeBuild run, then:
kubectl apply -f deployment/coworking.yaml
```

To roll out a new image version, edit `coworking.yaml` to reference the new ECR tag and re-apply. Kubernetes performs a rolling update with zero downtime because `replicas: 1` and the readiness probe at `/readiness_check` ensures traffic is only sent to a healthy pod.

## Environment Variables

Plaintext variables (`DB_HOST`, `DB_PORT`, `DB_USERNAME`, `DB_NAME`) are stored in `deployment/configmap.yaml`. The sensitive `DB_PASSWORD` is stored as a base64-encoded Kubernetes Secret in `deployment/secret.yaml` and injected at runtime — it is never baked into the Docker image.

## Recommended AWS Instance Type

For this lightweight analytics service, **t3.small** (2 vCPU, 2 GB RAM) is the right choice. The app's memory footprint at idle is under 60 MB and CPU usage spikes only briefly on report queries, so a burstable instance gives adequate headroom without paying for idle capacity.

## Cost Optimisation

Using **spot instances** for the EKS node group cuts compute costs by up to 70 % versus on-demand; the analytics service is stateless and can tolerate a brief interruption when a spot node is reclaimed. Enabling **CloudWatch Container Insights only on non-production clusters** and switching to basic CloudWatch metrics on production avoids the per-node Container Insights surcharge. Finally, configuring an **ECR lifecycle policy** to expire images older than 30 days keeps storage costs near zero since each build image is only a few hundred megabytes.

## Memory and CPU Allocation

The `coworking` deployment requests `100m` CPU and `128Mi` memory with limits of `250m` CPU and `256Mi` memory, which reflects actual measured usage while leaving headroom for traffic spikes. The `postgresql` deployment is allocated `100m`/`128Mi` (requests) and `200m`/`256Mi` (limits), appropriate for a single-tenant development database.
