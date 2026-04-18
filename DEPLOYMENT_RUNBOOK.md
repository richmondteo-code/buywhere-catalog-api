# Deployment Runbook for BuyWhere API

## Overview
This document outlines the deployment process for the BuyWhere API to staging and production environments.

## Prerequisites
- Docker and docker-compose installed
- AWS CLI configured with appropriate permissions
- Access to the BuyWhere GitHub repository
- Secrets configured in GitHub:
  - AWS_ACCESS_KEY_ID
  - AWS_SECRET_ACCESS_KEY
  - GITHUB_TOKEN (for CI/CD)

## CI/CD Pipeline
The CI/CD pipeline is defined in `.github/workflows/ci.yml` and includes the following stages:
1. **Lint**: Runs `ruff` to check code quality.
2. **TypeCheck**: Runs `mypy` to check type annotations.
3. **Test**: Runs the test suite with coverage using `pytest`.
4. **Build**: Builds Docker images for the API and MCP server.
5. **Deploy-Staging**: Deploys to the staging ECS cluster (if on main/master branch).
6. **Deploy-Production**: Deploys to the production ECS cluster (if pushing a version tag).
7. **Docs**: Builds the documentation using MkDocs.

## Staging Deployment
The staging deployment is triggered automatically on pushes to the `main` or `master` branches.
It uses the `deploy-staging` job in the CI workflow, which:
- Pulls the latest Docker image
- Updates the ECS service with a force-new-deployment
- Waits for the service to stabilize
- Performs health check validation (retries up to 3 times with 10-second intervals)
- Rolls back on failure

## Production Deployment
The production deployment is triggered when pushing a version tag (e.g., `v1.0.0`).
It uses the `deploy-prod` job in the CI workflow, which follows the same steps as staging but targets the production cluster.

## Local Development
To run the API and MCP server locally for development:
```bash
docker compose up
```
This will start:
- API on port 8000
- MCP server on port 8080
- Postgres on port 5432
- Redis on port 6379

## Health Checks
The API provides a health check endpoint at `/v1/health` that returns:
- Database health
- Disk space
- API self-test
- Scraper health

This endpoint is used in the CI/CD pipeline for validation.

## Rollback Procedure
In case of a failed deployment, the CI/CD pipeline automatically rolls back to the previous task definition.
Manual rollback can be performed using:
```bash
aws ecs update-service --cluster <cluster> --service buywhere-api --task-definition <previous-task-definition> --force-new-deployment
```
Replace `<cluster>` with `buywhere-staging` or `buywhere-prod` as needed, and `<previous-task-definition>` with the task definition ARN to rollback to.

## Monitoring
Basic monitoring is available through the health check endpoint.
For production, consider setting up:
- CloudWatch alarms on ECS service metrics
- DNS-level health checks
- Application Performance Monitoring (APM) tools

## Troubleshooting
1. **Deployment fails health check**: Check the logs of the ECS service and verify the API is responding.
2. **Image pull fails**: Ensure the Docker image was built and pushed correctly to the registry.
3. **Credentials issues**: Verify that AWS credentials are correctly set in GitHub secrets.
4. **Database connection issues**: Verify that the RDS instance is accessible and the credentials in the task definition are correct.

## Contact
For questions, contact the DevOps team (Bolt, Gate, Stack, Forge, Ops, Pipe).
