# fireREST API Audit Report

**Spec:** `.llm/fmc_oas3_7.4.2.json` (FMC 7.4.2)  
**Branch:** `code-audit`  
**Date:** 2026-06-03 (updated 2026-06-03 with Objects API doc cross-reference)  
**Scope:** All HTTP methods (GET, POST, PUT, DELETE, PATCH) across all 628 OAS3 paths and 368 resource implementation files; cross-referenced against `.llm/Objectsin the RESTAPI.md` namespace ToC.

---

## Summary

| Severity | Count | Description                                                    |
|----------|-------|----------------------------------------------------------------|
| CRITICAL | 4     | Requests always fail or cause Python exceptions                |
| HIGH     | 14    | Wrong path/container — every API call returns 4xx              |
| MEDIUM   | 8     | Missing filter/param entries — KeyError on use                 |
| LOW      | 30+   | Missing implementations for spec-defined endpoints             |
| INFO     | 64+   | Spec `filter` param supported but `SUPPORTED_FILTERS` is empty |

**Breaking change column** marks fixes that change public API surface (attribute paths, method signatures, or observable behavior).

---

## CRITICAL — Requests always fail

### C-01: `Hitcount.update()` and `Hitcount.delete()` are no-ops (both classes)

**Files:**  
- [policy/accesspolicy/operational/hitcounts/__init__.py](fireREST/fmc/policy/accesspolicy/operational/hitcounts/__init__.py)  
- [policy/prefilterpolicy/operational/hitcounts/__init__.py](fireREST/fmc/policy/prefilterpolicy/operational/hitcounts/__init__.py)

**Problem:** Both `update()` and `delete()` methods consist of only `return` — they make no HTTP call and silently do nothing.

```python
# current (broken)
@utils.support_params
def update(self):
    return

@utils.support_params
def delete(self):
    return
```

**OAS3 spec:** `PUT /policy/accesspolicies/{containerUUID}/operational/hitcounts` with `filter` param; `DELETE` same path.

**Fix:** Implement both methods with proper `container_uuid` parameter and filter support. See branch `fix/102-hitcount-delete` which has the fix but is not yet merged to `master`.

**Breaking:** NO — methods already return `None` silently; making them functional is additive.

---

### C-02: TID namespace URL builder missing `/domain/{domainUUID}` segment

**File:** [fmc/__init__.py](fireREST/fmc/__init__.py#L394)

**Problem:** The `'tid'` namespace URL builder is:
```python
'tid': f'{self.conn.protocol}://{self.conn.hostname}{defaults.API_TID_URL}{path}',
```
This produces `/api/fmc_tid/v1/tid/element/{uuid}` but the OAS3 spec requires `/api/fmc_tid/v1/domain/{domainUUID}/tid/element/{objectId}`. All TID resource calls return `404 Not Found`.

**Affected resources:** `Element`, `Incident`, `Indicator`, `Observable`, `Setting`, `Source` (all in `fireREST/fmc/intelligence/tid/`)

**Fix:**
```python
'tid': f'{self.conn.protocol}://{self.conn.hostname}{defaults.API_TID_URL}/domain/{self.conn.domain["id"]}{path}',
```

**Breaking:** YES — changes the resolved URL for all TID resources, but since current URLs always return 404 the functional change is net-positive.

---

### C-03: TaxiiConfig namespace URL missing `/domain/{domainUUID}`

**Files:**  
- [intelligence/taxiiconfig/collection/__init__.py](fireREST/fmc/intelligence/taxiiconfig/collection/__init__.py)  
- [intelligence/taxiiconfig/discoveryinfo/__init__.py](fireREST/fmc/intelligence/taxiiconfig/discoveryinfo/__init__.py)

**Problem:** Same root cause as C-02. Uses NAMESPACE `'tid'` which lacks the domain UUID segment. OAS3 spec paths:
- `POST /api/fmc_tid/v1/domain/{domainUUID}/taxiiconfig/collections`
- `POST /api/fmc_tid/v1/domain/{domainUUID}/taxiiconfig/discoveryinfo`

Additional issue: both have PATH `/{uuid}` suffix but the spec endpoints are POST-only list paths with no individual UUID endpoint.

**Fix:** Fix URL builder (same as C-02) and remove `/{uuid}` from PATH.

**Breaking:** YES (URL change; removing `/{uuid}` suffix is safe since GET-by-UUID doesn't exist in spec).

---

### C-04: `IpsecCryptoMap` placed under wrong container (`FtdS2sVpn` instead of `RaVpn`)

**File:** [policy/ftds2svpn/ipseccryptomap/__init__.py](fireREST/fmc/policy/ftds2svpn/ipseccryptomap/__init__.py)

**Problem:** Current implementation:
```python
CONTAINER_NAME = 'FtdS2sVpn'
CONTAINER_PATH = '/policy/ftds2svpns/{uuid}'
PATH = '/policy/ftds2svpns/{container_uuid}/ipseccryptomaps/{uuid}'
```
OAS3 spec has `ipseccryptomaps` exclusively under `ravpns`:
`/api/fmc_config/v1/domain/{domainUUID}/policy/ravpns/{containerUUID}/ipseccryptomaps/{objectId}`

The `ftds2svpns` container has no `ipseccryptomaps` endpoint at all. Every call generates a 404.

**Fix:**
```python
CONTAINER_NAME = 'RaVpn'
CONTAINER_PATH = '/policy/ravpns/{uuid}'
PATH = '/policy/ravpns/{container_uuid}/ipseccryptomaps/{uuid}'
```
Move the file from `policy/ftds2svpn/ipseccryptomap/` to `policy/ravpn/ipseccryptomap/` and update the `RaVpn` namespace `__init__.py`.

**Breaking:** YES — `fmc.policy.ftds2svpn.ipseccryptomap` → `fmc.policy.ravpn.ipseccryptomap` attribute path changes.

---

## HIGH — Wrong path, every call returns 4xx

### H-01: `AllowDnsRule` path uses singular name and incorrect `/{uuid}` suffix

**File:** [policy/dnspolicy/allowdnsrule/__init__.py](fireREST/fmc/policy/dnspolicy/allowdnsrule/__init__.py)

**Current PATH:** `/policy/dnspolicies/{container_uuid}/allowdnsrule/{uuid}`  
**Correct PATH:** `/policy/dnspolicies/{container_uuid}/allowdnsrules`  
**OAS3:** `GET /policy/dnspolicies/{containerUUID}/allowdnsrules` — list-only, no individual UUID endpoint.

**Fix:** Rename path segment to `allowdnsrules` (plural); remove `/{uuid}`.

**Breaking:** NO — individual UUID GET never worked (404); list GET continues to work via `fix_url` stripping `/None`.

---

### H-02: `BlockDnsRule` — same issue as H-01

**File:** [policy/dnspolicy/blockdnsrule/__init__.py](fireREST/fmc/policy/dnspolicy/blockdnsrule/__init__.py)

**Current PATH:** `/policy/dnspolicies/{container_uuid}/blockdnsrule/{uuid}`  
**Correct PATH:** `/policy/dnspolicies/{container_uuid}/blockdnsrules`

**Breaking:** NO (same reasoning as H-01).

---

### H-03: `EbsSnapshot` uses plural segment `ebssnapshots` but spec uses singular `ebssnapshot`

**File:** [integration/ebssnapshot/__init__.py](fireREST/fmc/integration/ebssnapshot/__init__.py)

**Current PATH:** `/integration/ebssnapshots/{uuid}` (plural)  
**Correct PATH:** `/integration/ebssnapshot/{uuid}` (singular)  
**OAS3:** `GET /integration/ebssnapshot/{objectId}`, `POST /integration/ebssnapshot`

**Breaking:** YES — minor path segment rename.

---

### H-04: `PolicyLock` wrong path — missing `/operational/` segment

**File:** Find with `grep -r "policylocks" fireREST/fmc/`

**Current PATH:** `/policy/policylocks/{uuid}`  
**Correct PATH:** `/policy/operational/policylocks`  
**OAS3:** `GET /policy/operational/policylocks`, `POST /policy/operational/policylocks` — list/create, no UUID.

**Breaking:** YES — path changes; removing `/{uuid}` is safe (no individual endpoint in spec).

---

### H-05: `Usage` (object operational) has typo `objects` instead of `object`

**File:** [object/operational/usage/__init__.py](fireREST/fmc/object/operational/usage/__init__.py)

**Current PATH:** `/objects/operational/usage` (typo: `objects`)  
**Correct PATH:** `/object/operational/usage`  
**OAS3:** `GET /api/fmc_config/v1/domain/{domainUUID}/object/operational/usage`

**Breaking:** YES — path change; every call currently returns 404.

---

### H-06: `Hitcount` PATH has `/{uuid}` suffix but OAS3 has no individual endpoint

**Files:**  
- [policy/accesspolicy/operational/hitcounts/__init__.py](fireREST/fmc/policy/accesspolicy/operational/hitcounts/__init__.py)  
- [policy/prefilterpolicy/operational/hitcounts/__init__.py](fireREST/fmc/policy/prefilterpolicy/operational/hitcounts/__init__.py)

**Current PATH:** `/policy/accesspolicies/{container_uuid}/operational/hitcounts/{uuid}`  
**Correct PATH:** `/policy/accesspolicies/{container_uuid}/operational/hitcounts`  
**OAS3:** The endpoint is always at `/hitcounts` — filter params select specific rules.

**Breaking:** NO — `fix_url()` strips `/None` for list calls; UUID individual GET never existed in spec.

---

### H-07: `S2sVpnSummary` implemented as `ChildResource` under `FtdS2sVpn` — spec has it as standalone list

**File:** [policy/ftds2svpn/s2svpnsummary/__init__.py](fireREST/fmc/policy/ftds2svpn/s2svpnsummary/__init__.py)

**Current:** `ChildResource` with PATH `/policy/ftds2svpns/{container_uuid}/summaries/{uuid}`  
**Correct:** `Resource` with PATH `/policy/s2svpnsummaries/{uuid}`  
**OAS3:** `GET /policy/s2svpnsummaries` (top-level list, no container)

**Breaking:** YES — resource type changes, access path changes from `fmc.policy.ftds2svpn.s2svpnsummary` to `fmc.policy.s2svpnsummary` (or similar).

---

### H-08: `PreviewChanges` has `/{uuid}` suffix — spec is list-only

**File:** [changemanagement/ticket/previewchanges/__init__.py](fireREST/fmc/changemanagement/ticket/previewchanges/__init__.py)

**Current PATH:** `/changemanagement/tickets/{container_uuid}/previewchanges/{uuid}`  
**Correct PATH:** `/changemanagement/tickets/{container_uuid}/previewchanges`  
**OAS3:** `GET /changemanagement/tickets/{containerUUID}/previewchanges` — list-only.

**Breaking:** NO — individual UUID GET never existed.

---

### H-09: `ValidationResults` has `/{uuid}` suffix — spec is list-only

**File:** [changemanagement/ticket/validationresults/__init__.py](fireREST/fmc/changemanagement/ticket/validationresults/__init__.py)

**Current PATH:** `/changemanagement/tickets/{container_uuid}/validationresults/{uuid}`  
**Correct PATH:** `/changemanagement/tickets/{container_uuid}/validationresults`

**Breaking:** NO.

---

### H-10: `DownloadReport` has `/{uuid}` suffix — spec is list-only GET

**File:** [deployment/jobhistory/downloadreport/__init__.py](fireREST/fmc/deployment/jobhistory/downloadreport/__init__.py)

**Current PATH:** `/deployment/jobhistories/{container_uuid}/operational/downloadreports/{uuid}`  
**Correct PATH:** `/deployment/jobhistories/{container_uuid}/operational/downloadreports`  
**OAS3:** `GET /deployment/jobhistories/{containerUUID}/operational/downloadreports` — list-only.

**Breaking:** NO.

---

### H-11: `EmailReport` has `/{uuid}` suffix and wrong version constant name

**File:** [deployment/jobhistory/emailreport/__init__.py](fireREST/fmc/deployment/jobhistory/emailreport/__init__.py)

**Current PATH:** `/deployment/jobhistories/{container_uuid}/operational/emailreports/{uuid}`  
**Correct PATH:** `/deployment/jobhistories/{container_uuid}/operational/emailreports`  
**OAS3:** `POST /deployment/jobhistories/{containerUUID}/operational/emailreports` — create-only.  
**Additional:** `MINIMUM_VERSION_REQUIRED_GET` is declared but the supported operation is `CREATE`, not GET.

**Breaking:** NO (path fix); changing version constant name is a minor rename.

---

### H-12: `FpInterfaceStatistics` has `/{uuid}` suffix — spec is list-only

**File:** [device/devicerecord/fpinterfacestatistics/__init__.py](fireREST/fmc/device/devicerecord/fpinterfacestatistics/__init__.py)

**Current PATH:** `/devices/devicerecords/{container_uuid}/fpinterfacestatistics/{uuid}`  
**Correct PATH:** `/devices/devicerecords/{container_uuid}/fpinterfacestatistics`

**Breaking:** NO.

---

### H-13: `ManagementConvergenceMode` has `/{uuid}` suffix — spec is list/create only

**File:** [device/devicerecord/managementconvergencemode/__init__.py](fireREST/fmc/device/devicerecord/managementconvergencemode/__init__.py)

**Current PATH:** `/devices/devicerecords/{container_uuid}/managementconvergencemode/{uuid}`  
**Correct PATH:** `/devices/devicerecords/{container_uuid}/managementconvergencemode`  
**OAS3:** `GET + POST /devices/devicerecords/{containerUUID}/managementconvergencemode`

**Breaking:** NO.

---

### H-14: `TestUmbrellaConnection` missing `/operational/` segment

**File:** [integration/testumbrellaconnection/\_\_init\_\_.py](fireREST/fmc/integration/testumbrellaconnection/__init__.py)

**Current PATH:** `/integration/testumbrellaconnections`  
**Correct PATH:** `/integration/operational/testumbrellaconnections`  
**OAS3:** `POST /integration/operational/testumbrellaconnections`

**Breaking:** NO — POST-only endpoint, path segment addition.

---

## MEDIUM — Unmapped filter/param keys cause `KeyError` at runtime

When a user calls `get()` with one of these keyword arguments, `utils.support_params` looks up the key in the `FILTERS` or `PARAMS` dict and raises `KeyError` because the key is missing.

### M-01: `JobHistory` — `device_uuid` not in `FILTERS` dict

**File:** [deployment/jobhistory/__init__.py](fireREST/fmc/deployment/jobhistory/__init__.py)

`SUPPORTED_FILTERS = ['device_uuid']` — but `FILTERS` dict has `device_id` and `device_uuids`, not `device_uuid`.  
**Fix:** Change to `device_uuids` (or add `'device_uuid': 'deviceUUID'` to `FILTERS`; verify against spec filter format).

**Breaking:** YES (keyword argument rename if changed to `device_uuids`).

---

### M-02: `PendingChanges` — `parent_entity_types`, `parent_uuid` not in `FILTERS`

**File:** [deployment/deployabledevice/pendingchanges/__init__.py](fireREST/fmc/deployment/deployabledevice/pendingchanges/__init__.py)

`SUPPORTED_FILTERS = ['parent_entity_types', 'parent_uuid']`  
**Fix:** Add both keys to `FILTERS` dict in `fireREST/mapping.py` with appropriate camelCase values (`ParentEntityTypes`, `ParentEntityUUID` or similar — verify against actual filter format in spec).

**Breaking:** NO (adding new entries to FILTERS).

---

### M-03: `Vulnerability` (netmap) — `source` not in `FILTERS`

**File:** [netmap/vulnerability/__init__.py](fireREST/fmc/netmap/vulnerability/__init__.py)

`SUPPORTED_FILTERS = ['vuln_id', 'ip_address', 'protocol', 'port', 'source']` — all except `source` are mapped.  
**Fix:** Add `'source': 'source'` to `FILTERS` dict.

**Breaking:** NO.

---

### M-04: `Metric` (health) — `regex_filter`, `query_function`, `step` not in `FILTERS`

**File:** [health/metric/__init__.py](fireREST/fmc/health/metric/__init__.py)

`SUPPORTED_FILTERS` includes `'regex_filter'`, `'query_function'`, `'step'` with no corresponding entries in `FILTERS`.  
**Fix:** Add to `FILTERS`: `'regex_filter': 'regexFilter'`, `'query_function': 'queryFunction'`, `'step': 'step'`.

**Breaking:** NO.

---

### M-05: `NatRule` — `section` in `SUPPORTED_FILTERS` but `section` belongs in `SUPPORTED_PARAMS`

**File:** [policy/ftdnatpolicy/natrule/__init__.py](fireREST/fmc/policy/ftdnatpolicy/natrule/__init__.py)

`SUPPORTED_FILTERS = ['section', 'source_interface', ...]` — `section` is a URL query parameter (not a `filter=` value). It IS in the `PARAMS` dict already.  
**Fix:** Move `'section'` from `SUPPORTED_FILTERS` to `SUPPORTED_PARAMS`.

**Breaking:** YES (minor) — `section` will be sent as `?section=...` instead of `?filter=section:...` (which is the correct API behavior anyway).

---

### M-06: `Chassis Interface` — `operation` in `SUPPORTED_PARAMS` but should be in `SUPPORTED_FILTERS`

**File:** [chassis/interface/__init__.py](fireREST/fmc/chassis/interface/__init__.py)

`SUPPORTED_PARAMS = ['operation']` — but `operation` is mapped in `FILTERS`, not `PARAMS`.  
**Fix:** Move `'operation'` from `SUPPORTED_PARAMS` to `SUPPORTED_FILTERS`.

**Breaking:** YES (minor) — `operation` will be sent as `?filter=operation:...` instead of `?operation=...`.

---

### M-07: `Usage` (object/operational) — `uuid` not in `FILTERS`

**File:** [object/operational/usage/__init__.py](fireREST/fmc/object/operational/usage/__init__.py)

`SUPPORTED_FILTERS = ['uuid', 'obj_type']` — `uuid` is not in the `FILTERS` dict.  
**Fix:** Add `'uuid': 'uuid'` to `FILTERS` dict (also fix PATH per H-05).

**Breaking:** NO.

---

### M-08: `PreviewChanges` declares `SUPPORTED_FILTERS` but keys not in `FILTERS`

**File:** [changemanagement/ticket/previewchanges/__init__.py](fireREST/fmc/changemanagement/ticket/previewchanges/__init__.py)

Has a `filter` param in spec (`ParentEntityTypes`, `EntityUUID`) but `SUPPORTED_FILTERS` entries are not mapped.  
**Fix:** Add relevant filter mappings to `FILTERS` dict or verify what keys are expected.

**Breaking:** NO.

---

## LOW — Missing implementations

The following OAS3-defined endpoints have no corresponding fireREST implementation.

### L-01: Missing entire resources (new classes needed)

**Object namespace:**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/object/extendedcommunitylists/{uuid}` | GET, POST, PUT, DELETE | Full CRUD + overrides child |
| `/object/extendedcommunitylists/{container_uuid}/overrides/{uuid}` | GET | Override child resource |
| `/object/localrealmusers/{uuid}` | GET, POST, PUT, DELETE | Full CRUD |
| `/object/operational/umbrellaprotectionpolicies` | GET, POST | List-only (no `/{uuid}`) |

**Search namespace (entire namespace missing — wire as `fmc.search`):**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/search/global` | GET | Global cross-object search |
| `/search/object` | GET | Object-scoped search |
| `/search/policy` | GET | Policy-scoped search |
| `/search/device` | GET | Device-scoped search |

**NetMap namespace:**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/vulns/{uuid}` (NAMESPACE=`netmap`) | GET, POST, DELETE | Vulnerability feed |

**Device namespace — interfaces:**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/devices/devicerecords/{container_uuid}/vniinterfaces/{uuid}` | GET, POST, PUT, DELETE | VXLAN VNI interface |
| `/devices/devicerecords/{container_uuid}/vteppolicies/{uuid}` | GET, POST, PUT, DELETE | VXLAN VTEP policy |

**Device namespace — routing (non-VR):**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/devices/devicerecords/{container_uuid}/routing/ecmpzones/{uuid}` | GET, POST, PUT, DELETE | ECMP zone (device-level) |
| `/devices/devicerecords/{container_uuid}/routing/ospfv3routes/{uuid}` | GET | OSPFv3 route table (read-only) |

**Device namespace — routing (VR-level nested):**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/devices/devicerecords/{container_uuid}/routing/virtualrouters/{child_container_uuid}/ecmpzones/{uuid}` | GET, POST, PUT, DELETE | ECMP zone (VR-level `NestedChildResource`) |

**Policy namespace:**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/policy/operational/policylocks` | GET, POST | Replaces broken `PolicyLock` (H-04) — list-only |
| `/policy/s2svpnsummaries` | GET | Replaces broken `S2sVpnSummary` (H-07) — `Resource` |
| `/policy/ravpns/{container_uuid}/ipseccryptomaps/{uuid}` | GET, PUT | Replaces broken `IpsecCryptoMap` (C-04) under `RaVpn` |

**Integration namespace:**

| OAS3 Path | Methods | Notes |
|---|---|---|
| `/integration/operational/refreshsecurexconfigs` | POST | Operational action |

### L-02: Missing operational action endpoints (custom methods needed)

| OAS3 Path | Method | Suggested location |
|---|---|---|
| `POST /backup/operational/devicebackup` | POST | New `DeviceBackup` operational resource |
| `POST /deviceclusters/ftdclusterreadinesscheck` | POST | `DeviceCluster` operational method |
| `POST /deviceclusters/{uuid}/operational/ftdclusterdevicecommands` | POST | `DeviceCluster` operational method |
| `POST /devices/copyconfigrequests` | POST | `DeviceRecord` operational method |
| `POST /devices/operational/changemanagers` | POST | `DeviceRecord` operational method |
| `POST /devices/operational/exports` | POST | `DeviceRecord` operational method |
| `POST /devices/operational/imports` | POST | `DeviceRecord` operational method |
| `DELETE+POST /object/dynamicobjectmappings` | DELETE, POST | `DynamicObject` methods |
| `POST /object/bulkdynamicobjects` | POST | `DynamicObject.bulk_create()` |
| `POST /object/downloadinternalca` | POST | Object operational method |
| `POST /object/validatecertfile` | POST | Object operational method |

### L-03: Deprecated / not in OAS3 7.4.2

These implementations exist in fireREST but have no corresponding path in the 7.4.2 spec:

| Class | File | Notes |
|---|---|---|
| `Csdac` | [health/csdac/__init__.py](fireREST/fmc/health/csdac/__init__.py) | PATH `/health/csdac/{uuid}` — removed from API in 7.4.x |

---

## INFO — Filter support missing for spec-defined `filter` param

The following **64 resource classes** accept a `filter` query parameter according to the OAS3 spec but declare `SUPPORTED_FILTERS = []` (or omit it entirely), so callers cannot use filters through the SDK.

Representative examples (non-exhaustive):

| Class | Spec filter examples |
|---|---|
| `AccessPolicy` | Policy name filter |
| `DeviceRecord` | Device type, group filter |
| `AnyProtocolPortObject` | nameOrValue filter |
| `BfdTemplate` | Name filter |
| `DecryptionPolicy` | Policy name filter |
| `DeviceLicense` | License type filter |
| `DnsPolicy` | Policy name filter |
| `DynamicObject` | Name/value filter |
| `DistinguishedName` | Name filter |
| `CipherSuiteList` | Name filter |

**Fix pattern:** For each resource:
1. Identify which `filter=key:value` pairs the spec accepts (check OAS3 `filter` param description).
2. Add corresponding snake_case keys to `SUPPORTED_FILTERS`.
3. Ensure each key has a camelCase entry in `fireREST/mapping.py` `FILTERS` dict.
4. Override `get()` with `@utils.support_params` and the filter kwargs.

**Breaking:** NO — purely additive.

---

## Additional Observations

### PATCH method usage

Several OAS3 paths define `PATCH` instead of `PUT` for updates. The fireREST `update()` method in `Resource`/`ChildResource` always uses `PUT`. Verify whether the FMC API actually enforces the distinction or accepts either verb. Affected paths include chassis interface endpoints.

### Chassis AppInfo list-only endpoint

**File:** [chassis/appinfo/__init__.py](fireREST/fmc/chassis/appinfo/__init__.py)

OAS3 has `/chassis/fmcmanagedchassis/{containerUUID}/appinfo` as a list-only endpoint (no `/{uuid}`). The current implementation appends `/{uuid}` to the PATH. Calling `get(uuid='xxx')` fails; `get()` without UUID works via `fix_url`.

### `RaVpnSession` GET path has no OAS3 backing

**File:** [health/ravpnsession/__init__.py](fireREST/fmc/health/ravpnsession/__init__.py)

PATH `/health/ravpnsessions/{uuid}` — the OAS3 spec only defines `POST /health/ravpnsessions/operational/terminateravpnsessions`. There is no GET for this resource in 7.4.2. The `terminate()` custom method is correct; the inherited `get()` always returns 404.

### `TunnelDetails` has `/{uuid}` suffix — spec is list-only

**File:** [health/tunnelstatus/tunneldetails/__init__.py](fireREST/fmc/health/tunnelstatus/tunneldetails/__init__.py) *(if exists)*

OAS3: `GET /health/tunnelstatuses/{containerUUID}/tunneldetails` — list-only, no individual UUID endpoint.

### Intelligence TID `ospfv3routes` in VirtualRouter sub-namespace

The `OspfV3Route` class in `fireREST/fmc/device/devicerecord/routing/virtualrouter/ospfv3route/` uses path `/ospfv3routes/{uuid}` but the OAS3 spec under virtualrouters uses `ospfv3routes` while also having a `ospfv3routes` under the direct device routing path. Both paths exist in the spec and appear correctly implemented.

---

## Implementation Plan

### Phase 1 — Critical bug fixes (unblock broken namespaces)

| # | Task | File(s) | Breaking |
|---|---|---|---|
| 1.1 | Merge branch `fix/102-hitcount-delete` into `master` (fixes C-01) | — | NO |
| 1.2 | Fix TID URL builder: add `/domain/{domain_id}` segment (C-02) | `fireREST/fmc/__init__.py` | YES |
| 1.3 | Fix TaxiiConfig: same URL fix + remove `/{uuid}` from both PATHs (C-03) | `intelligence/taxiiconfig/collection/__init__.py`, `intelligence/taxiiconfig/discoveryinfo/__init__.py` | YES |
| 1.4 | Move `IpsecCryptoMap` from `ftds2svpn/` to `ravpn/` with correct PATH (C-04) | `policy/ftds2svpn/ipseccryptomap/`, `policy/ravpn/__init__.py` | YES |

### Phase 2 — HIGH path fixes (all existing classes returning 4xx)

| # | Task | File | Breaking |
|---|---|---|---|
| 2.1 | `AllowDnsRule`: pluralize + remove `/{uuid}` (H-01) | `policy/dnspolicy/allowdnsrule/__init__.py` | NO |
| 2.2 | `BlockDnsRule`: pluralize + remove `/{uuid}` (H-02) | `policy/dnspolicy/blockdnsrule/__init__.py` | NO |
| 2.3 | `EbsSnapshot`: singular path `ebssnapshot` (H-03) | `integration/ebssnapshot/__init__.py` | YES |
| 2.4 | `PolicyLock`: add `/operational/` + remove `/{uuid}` (H-04) | `policy/policylock/__init__.py` | YES |
| 2.5 | `Usage`: fix `/objects/` → `/object/` typo (H-05) | `object/operational/usage/__init__.py` | YES |
| 2.6 | `Hitcount` (both): remove `/{uuid}` suffix (H-06) | `policy/accesspolicy/operational/hitcounts/__init__.py`, `policy/prefilterpolicy/operational/hitcounts/__init__.py` | NO |
| 2.7 | `S2sVpnSummary`: convert to `Resource` with correct PATH (H-07) | `policy/ftds2svpn/s2svpnsummary/__init__.py`, `policy/__init__.py` | YES |
| 2.8 | `PreviewChanges`: remove `/{uuid}` suffix (H-08) | `changemanagement/ticket/previewchanges/__init__.py` | NO |
| 2.9 | `ValidationResults`: remove `/{uuid}` suffix (H-09) | `changemanagement/ticket/validationresults/__init__.py` | NO |
| 2.10 | `DownloadReport`: remove `/{uuid}` suffix (H-10) | `deployment/jobhistory/downloadreport/__init__.py` | NO |
| 2.11 | `EmailReport`: remove `/{uuid}` + fix version constant (H-11) | `deployment/jobhistory/emailreport/__init__.py` | NO |
| 2.12 | `FpInterfaceStatistics`: remove `/{uuid}` suffix (H-12) | `device/devicerecord/fpinterfacestatistics/__init__.py` | NO |
| 2.13 | `ManagementConvergenceMode`: remove `/{uuid}` suffix (H-13) | `device/devicerecord/managementconvergencemode/__init__.py` | NO |
| 2.14 | `TestUmbrellaConnection`: add `/operational/` segment (H-14) | `integration/testumbrellaconnection/__init__.py` | NO |

### Phase 3 — MEDIUM mapping fixes (prevent KeyError at runtime)

| # | Task | File |
|---|---|---|
| 3.1 | `JobHistory`: fix `device_uuid` → `device_uuids` in `SUPPORTED_FILTERS` (M-01) | `deployment/jobhistory/__init__.py` |
| 3.2 | Add `parent_entity_types`, `parent_uuid` to `FILTERS` in `mapping.py` (M-02) | `fireREST/mapping.py` |
| 3.3 | Add `source` to `FILTERS` in `mapping.py` (M-03) | `fireREST/mapping.py` |
| 3.4 | Add `regex_filter`, `query_function`, `step` to `FILTERS` in `mapping.py` (M-04) | `fireREST/mapping.py` |
| 3.5 | Move `section` from `SUPPORTED_FILTERS` → `SUPPORTED_PARAMS` in `NatRule` (M-05) | `policy/ftdnatpolicy/natrule/__init__.py` |
| 3.6 | Move `operation` from `SUPPORTED_PARAMS` → `SUPPORTED_FILTERS` in `ChassisInterface` (M-06) | `chassis/interface/__init__.py` |
| 3.7 | Add `uuid` to `FILTERS` in `mapping.py` (M-07) | `fireREST/mapping.py` |
| 3.8 | Add `PreviewChanges` filter keys to `FILTERS` in `mapping.py` (M-08) | `fireREST/mapping.py` |

### Phase 4 — New resource classes (additive, no breaking changes)

Each item requires: new folder + `__init__.py`, wire into parent namespace `__init__.py`, wire into `FMC.__init__` if new top-level namespace.

**4A — Search namespace (new top-level `fmc.search`)**

| # | Class | PATH | Type |
|---|---|---|---|
| 4A.1 | `GlobalSearch` | `'/search/global'` | `Resource` (GET-only, list-only) |
| 4A.2 | `ObjectSearch` | `'/search/object'` | `Resource` (GET-only, list-only) |
| 4A.3 | `PolicySearch` | `'/search/policy'` | `Resource` (GET-only, list-only) |
| 4A.4 | `DeviceSearch` | `'/search/device'` | `Resource` (GET-only, list-only) |
| 4A.5 | `Search` grouping class | — | Wire into `FMC.__init__` as `self.search` |

**4B — Object namespace additions**

| # | Class | PATH | Type |
|---|---|---|---|
| 4B.1 | `LocalRealmUser` | `'/object/localrealmusers/{uuid}'` | `Resource` (full CRUD) |
| 4B.2 | `ExtendedCommunityList` | `'/object/extendedcommunitylists/{uuid}'` | `Resource` (full CRUD) |
| 4B.3 | `ExtendedCommunityListOverride` | `'/object/extendedcommunitylists/{container_uuid}/overrides/{uuid}'` | `ChildResource` of `ExtendedCommunityList` (GET-only) |

**4C — NetMap namespace addition**

| # | Class | PATH | Type |
|---|---|---|---|
| 4C.1 | `Vulns` | `'/vulns/{uuid}'` (NAMESPACE=`netmap`) | `Resource` (GET, POST, DELETE) |

**4D — Device namespace — VXLAN interfaces**

| # | Class | PATH | Type |
|---|---|---|---|
| 4D.1 | `VniInterface` | `'/devices/devicerecords/{container_uuid}/vniinterfaces/{uuid}'` | `ChildResource` of `DeviceRecord` (full CRUD) |
| 4D.2 | `VtepPolicy` | `'/devices/devicerecords/{container_uuid}/vteppolicies/{uuid}'` | `ChildResource` of `DeviceRecord` (full CRUD) |

**4E — Device namespace — routing additions**

| # | Class | PATH | Type |
|---|---|---|---|
| 4E.1 | `EcmpZone` (device-level) | `'/devices/devicerecords/{container_uuid}/routing/ecmpzones/{uuid}'` | `ChildResource` of `DeviceRecord` (full CRUD) |
| 4E.2 | `Ospfv3Route` (device-level) | `'/devices/devicerecords/{container_uuid}/routing/ospfv3routes/{uuid}'` | `ChildResource` of `DeviceRecord` (GET-only) |
| 4E.3 | `EcmpZone` (VR-level) | `'/devices/devicerecords/{container_uuid}/routing/virtualrouters/{child_container_uuid}/ecmpzones/{uuid}'` | `NestedChildResource` (CONTAINER=`DeviceRecord`, CHILD_CONTAINER=`VirtualRouter`, full CRUD) |

**4F — Integration namespace addition**

| # | Class | PATH | Type |
|---|---|---|---|
| 4F.1 | `RefreshSecurexConfig` | `'/integration/operational/refreshsecurexconfigs'` | `Resource` (POST-only, list-only) |

### Phase 5 — Operational/custom method additions (L-02)

Lower priority. Each is a custom method added to an existing class rather than a new class.

| # | Method | Class/File | OAS3 Path |
|---|---|---|---|
| 5.1 | `backup()` | `Backup` | `POST /backup/operational/devicebackup` |
| 5.2 | `readiness_check()` | `FtdDeviceCluster` | `POST /deviceclusters/ftdclusterreadinesscheck` |
| 5.3 | `device_command()` | `FtdDeviceCluster` | `POST /deviceclusters/{uuid}/operational/ftdclusterdevicecommands` |
| 5.4 | `copy_config()` | `DeviceRecord` | `POST /devices/copyconfigrequests` |
| 5.5 | `export()` | `DeviceRecord` | `POST /devices/operational/exports` |
| 5.6 | `import_device()` | `DeviceRecord` | `POST /devices/operational/imports` |
| 5.7 | `bulk_create()` | `DynamicObject` | `POST /object/bulkdynamicobjects` |
| 5.8 | `bulk_create_mappings()` / `bulk_delete_mappings()` | `DynamicObject.mapping` | `POST/DELETE /object/dynamicobjectmappings` |
| 5.9 | `download()` | `InternalCa` | `POST /object/downloadinternalca` |
| 5.10 | `validate_cert()` | cert class | `POST /object/validatecertfile` |

### Phase 6 — Deprecation cleanup

| # | Task | File |
|---|---|---|
| 6.1 | Remove `Csdac` class (L-03): endpoint removed in 7.4.x | `health/csdac/__init__.py` |

---

### CHANGELOG entries required for breaking changes

Breaking changes from Phases 1–2 that need a `## Breaking Changes` section:

- `IpsecCryptoMap` moved from `fmc.policy.ftds2svpn.ipseccryptomap` → `fmc.policy.ravpn.ipseccryptomap`
- `S2sVpnSummary` moved from `fmc.policy.ftds2svpn.s2svpnsummary` → `fmc.policy.s2svpnsummary`
- TID URL builder fix changes resolved URLs for all `fmc.intelligence.tid.*` resources
- `EbsSnapshot` PATH changes from `/integration/ebssnapshots/` → `/integration/ebssnapshot/`
- `PolicyLock` PATH changes from `/policy/policylocks/` → `/policy/operational/policylocks`
- `Usage` PATH changes from `/objects/` → `/object/`
- `Csdac` removed (Phase 6)
