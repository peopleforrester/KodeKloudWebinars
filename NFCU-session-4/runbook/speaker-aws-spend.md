# Speaker AWS Spend

What the EKS demo cluster costs the speaker. Read this **before** `terraform apply`. Figures
are on-demand `us-east-1` list prices as of authoring; check the AWS pricing pages for the
current numbers and your region. These are estimates, not a quote.

## Line items (default sizing: 2× m5.xlarge, 1 NAT gateway, 1 NLB)

| Line item | Unit price | 8-hour cost | Notes |
|---|---|---|---|
| EKS control plane | $0.10 / hr | ~$0.80 | Flat, per cluster |
| Worker nodes (m5.xlarge) | $0.192 / hr each | ~$3–$7 | 2 nodes idle; up to 5 under load — pay for what's running |
| NAT gateway | $0.045 / hr + $0.045/GB | ~$0.40–$1 | Hourly + data processed |
| Network Load Balancer | $0.0225 / hr + LCU | ~$0.20–$0.60 | Fronts Kourier |
| EBS (gp3 node volumes) | $0.08 / GB-month | ~$0.05 | ~20 GB × nodes, prorated to hours |
| S3 (model artifacts) | $0.023 / GB-month | <$0.01 | A few MB |
| **Tight 8-hour total** | | **~$5–$10** | Provision → labs → teardown the same day |

## Why the tfvars anchor says $40–$70

`terraform.tfvars.example` budgets **$40–$70**, well above the ~$5–$10 tight figure. That's a
deliberate **safety ceiling**, not the expected bill. It covers the realistic ways spend
grows:

- Leaving the cluster up across **multiple rehearsal days** before the session (each extra
  day ≈ $10–$15 at 2 idle nodes).
- Sustained **autoscaling to 5 nodes** during heavy load testing.
- NAT gateway **data processing** if you pull large images repeatedly.
- Forgetting to tear down promptly (the classic overrun).

Plan against $70 so a surprise can't hurt; expect to actually spend a fraction of it if you
provision and tear down the same day.

## Spend by phase

| Phase | What's running | Rough cost |
|---|---|---|
| Provisioning (~20 min) | Control plane + nodes coming up | <$0.50 |
| Idle (between rehearsal runs) | Control plane + 2 nodes + NAT + NLB | ~$0.55 / hr |
| Under load (labs + k6) | Up to 5 nodes + NAT data | ~$0.80–$1.20 / hr |
| Teardown verification | Brief, while destroying | <$0.20 |

## Stop the meter

```bash
cd cluster/eks && bash down.sh      # type the cluster name to confirm
aws eks list-clusters --region us-east-1   # confirm empty
```

Then sweep for the silent leftovers — these keep billing after the cluster "looks" gone:

```bash
aws ec2 describe-nat-gateways --filter Name=state,Values=available
aws elbv2 describe-load-balancers
aws ec2 describe-volumes --filters Name=status,Values=available
```

`terraform destroy` (via `down.sh`) removes all of them when it completes cleanly; the sweep
is the belt-and-suspenders check that it did.
