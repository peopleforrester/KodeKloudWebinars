# Shadow Deployment Specification

## Purpose
Defines the behavior of the shadow-mirror fan-out pattern that enables
champion-challenger model evaluation without affecting real users.
Implementation lives at
`MLOps_Deployment_Workshop/Session_2_Shadow_Deployment/lambdas/shadow-mirror/`.

## Requirements

## ADDED Requirements

### Requirement: Champion Synchronous Invocation
The shadow-mirror Lambda MUST invoke the champion endpoint synchronously
and return ONLY the champion's response to the caller.

#### Scenario: Standard prediction request
- GIVEN both champion and challenger endpoints are InService
- WHEN a caller POSTs a prediction request to the API Gateway URL
- THEN the shadow-mirror invokes the champion endpoint synchronously
- AND the response body contains the champion's prediction and
  `endpoint_source: "champion"`
- AND the challenger's response is NOT returned to the caller

### Requirement: Challenger Asynchronous Invocation
The shadow-mirror Lambda MUST invoke the challenger endpoint
asynchronously such that challenger latency or failure cannot affect
the caller-visible response.

#### Scenario: Slow challenger
- GIVEN the challenger endpoint takes 10 seconds to respond
- WHEN a caller POSTs a prediction request
- THEN the caller receives the champion's response within the champion's
  normal latency envelope
- AND the challenger continues processing asynchronously
- AND the challenger's eventual response is captured to S3 async output

#### Scenario: Failing challenger
- GIVEN the challenger endpoint returns 500 errors
- WHEN a caller POSTs a prediction request
- THEN the caller receives the champion's response normally
- AND the challenger failure is logged to CloudWatch Logs
- AND no error propagates to the caller

### Requirement: Request Correlation
Every prediction request MUST be assigned a UUID request_id that links
the champion synchronous response with the challenger asynchronous
output.

#### Scenario: Successful join
- GIVEN a prediction request with request_id X is processed
- WHEN both champion and challenger have completed
- THEN the shadow-log entry for X contains the input payload, the
  champion's response, and a reference to the challenger's async output URI
- AND the comparison Lambda can join the two responses using request_id X

### Requirement: Per-Attendee Isolation
Each attendee's shadow-mirror Lambda MUST write to attendee-scoped S3
buckets and invoke only that attendee's SageMaker endpoints.

#### Scenario: Two attendees, parallel sessions
- GIVEN attendees alice and bob are running labs simultaneously
- WHEN alice's shadow-mirror processes a request
- THEN the shadow-log entry is written to
  `s3://workshop-lab-alice-shadow-logs/` and NOT to bob's bucket
- AND the champion invocation targets
  `workshop-lab-alice-production` and NOT bob's endpoint
