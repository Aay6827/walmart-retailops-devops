# RetailOps DevOps Operations Runbook

## Purpose
This is a portfolio simulation inspired by retail e-commerce and supply-chain operations. It is not an internal Walmart production runbook.

## Service inventory
| Component | Host port | Purpose |
|---|---:|---|
| RetailOps API | 2100 | Main API |
| Order Service | 2101 | Order operations |
| Inventory Service | 2102 | Inventory operations |
| PostgreSQL | 2103 | Persistent application data |
| Prometheus | 2104 | Metrics and alerts |
| Grafana | 2105 | Dashboards |

## First-response checklist
1. Record the alert name, affected service, severity, and time.
2. Check container status and dependencies.
3. Inspect Prometheus targets and recent service logs.
4. Make one controlled change at a time.
5. Verify recovery using health checks and Prometheus.
6. Record the cause, actions, and follow-up work.

## Health checks
Run these commands in PowerShell from the project directory:

```powershell
docker compose ps
Invoke-RestMethod http://localhost:2100/health
Invoke-RestMethod http://localhost:2101/health
Invoke-RestMethod http://localhost:2102/health
Invoke-RestMethod http://localhost:2105/api/health
$targets = Invoke-RestMethod http://localhost:2104/api/v1/targets
$targets.data.activeTargets | Select-Object @{Name="Job";Expression={$_.labels.job}}, health, lastError
```

## Service outage response
Inspect the affected service before restarting it. Example for the Order Service:

```powershell
docker compose logs --tail 100 order-service
docker compose ps order-service
docker compose start order-service
Invoke-RestMethod http://localhost:2101/health
```

Confirm the Prometheus target returns to up and the alert clears.

## Data protection
- PostgreSQL uses the named postgres-data volume.
- Do not run docker compose down -v during routine troubleshooting.
- Never commit .env or credentials to Git.
- Verify backups before destructive database operations.

## Incident record
- Incident ID and time:
- Alert and affected service:
- Business impact:
- Evidence and logs:
- Cause or hypothesis:
- Actions taken:
- Recovery verification:
- Follow-up tasks:
