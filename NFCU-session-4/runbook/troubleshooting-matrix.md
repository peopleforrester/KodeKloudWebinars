# Troubleshooting Matrix

Known failure modes, ordered roughly by how often they bite. Each row: the symptom, the
likely cause, the exact command to fix it, and how to confirm it worked. Goal: resolve a
known symptom in under 5 minutes. `$NS` is the affected namespace throughout.

| # | Symptom | Likely cause | Remediation | Confirm |
|---|---|---|---|---|
| 1 | InferenceService stuck `READY=False`, predictor pod has an Init error | Storage initializer can't read `storageUri` | Check `kubectl logs <pod> -c storage-initializer -n $NS`; fix the `storageUri` or the Pod Identity association for `kserve-sa` | Pod leaves Init; `kubectl get isvc -n $NS` shows `READY=True` |
| 2 | Predictor pod `Pending` | ResourceQuota exhausted or no node capacity | `kubectl describe pod <pod> -n $NS` (look for quota/insufficient cpu); free pods or wait for autoscaler | Pod moves to `Running` within ~5 min |
| 3 | 503 on the first request after idle | Cold start (scale-to-zero) — pod spinning up | Retry after ~10s; for demos set `minReplicas: 1` to keep one warm | Second request returns 200 |
| 4 | Pods never scale back to zero | Steady background traffic, or `minReplicas>0` | `kubectl get ksvc -n $NS`; stop stray clients; verify `minReplicas: 0` in the manifest | `kubectl get pods -n $NS` → 0 predictor pods after ~60s idle |
| 5 | k6 reports high `http_req_failed` | Wrong `Host` header or `BASE_URL` | Re-check `BASE_URL`/`NAMESPACE`/`DOMAIN`; curl one request manually first | `tests/smoke/curl-tests.sh` returns 200 for the service |
| 6 | TinyLlama pod `OOMKilled` | Memory limit too low for the model | Raise `limits.memory` to 6Gi (or use distilGPT-2 fallback image) | Pod stays `Running` under `k6-tinyllama.js`; no restarts |
| 7 | OpenCost shows no / blank cost data | OpenCost can't reach Prometheus | `kubectl logs deploy/opencost -n opencost`; confirm `serviceName`/`namespaceName` in `opencost.yaml` match the Prometheus svc | OpenCost UI shows non-zero cost for a running model |
| 8 | Canary not splitting (100% to one revision) | Only one revision exists, or `canaryTrafficPercent` not applied | `kubectl get revisions -n $NS`; re-apply the canary manifest; check `.status...traffic` | Traffic status shows ~10/90 split |
| 9 | Rollback didn't restore v1.0.0 | Previous revision was garbage-collected | `kubectl get revisions -n $NS`; if gone, re-deploy v1.0.0 then re-apply rollback | Traffic status shows 100% on v1.0.0 |
| 10 | (kind) `curl localhost:31080` connection refused | Kourier not patched to NodePort 31080, or kind port mapping missing | Re-run `cluster/addons/bootstrap.sh local`; verify `kubectl get svc kourier -n kourier-system` is NodePort 31080 | `curl` reaches the ingress; smoke test passes |
| 11 | `helm ... release named X already exists` / conflict | Prior partial install of an add-on | `helm upgrade --install` is idempotent — re-run `bootstrap.sh`; if wedged, `helm uninstall X -n <ns>` then re-run | `cluster/addons/verify.sh` exits 0 |
| 12 | Predictor pod `ImagePullBackOff` | Image tag/registry wrong, or not pulled to nodes | `kubectl describe pod <pod> -n $NS`; fix the image in the manifest; pre-pull on nodes | Pod pulls and reaches `Running` |
| 13 | Webhook errors applying an InferenceService | cert-manager / KServe webhook not ready | `cluster/addons/verify.sh`; check cert-manager pods `Ready` | `kubectl apply` of the manifest succeeds |
| 14 | Knative activator 503s under load | Activator saturated / autoscaler lag | Raise `maxReplicas`; check `kubectl get pods -n knative-serving`; for EKS, confirm node autoscaler is scaling | Error rate drops below threshold in the next k6 run |

## Escalation

If a symptom isn't here or the fix doesn't hold within 5 minutes during the live session,
flip the affected attendee to the **distilGPT-2 fallback** (Lab 3) or to `minReplicas: 1`
(Labs 1/2) to stabilize, note it, and move on. Post-session, add the new symptom as a row.
