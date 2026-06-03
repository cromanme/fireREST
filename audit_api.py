#!/usr/bin/env python3
"""
fireREST API Audit Script
Compares every fireREST resource implementation against the OAS3 spec.
"""

import ast
import json
import os
import re
from collections import defaultdict
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. Load OAS3 spec
# ---------------------------------------------------------------------------
SPEC_PATH = '.llm/fmc_oas3_7.4.2.json'
with open(SPEC_PATH) as f:
    SPEC = json.load(f)

# ---------------------------------------------------------------------------
# 2. Normalise OAS3 path → fireREST relative PATH
#    e.g. /api/fmc_config/v1/domain/{domainUUID}/object/networks/{networkId}
#         → /object/networks/{uuid}   (last path-level UUID → {uuid})
#    Containers get {container_uuid}, nested containers get {child_container_uuid}
# ---------------------------------------------------------------------------
BASE_PREFIXES = [
    '/api/fmc_config/v1/domain/{domainUUID}',
    '/api/fmc_platform/v1/domain/{domainUUID}',
    '/api/fmc_platform/v1',
    '/api/fmc_tid/v1',
    '/api/fmc_troubleshoot/v1/domain/{domainUUID}',
    '/api/fmc_netmap/v1/domain/{domainUUID}',
]

UUID_RE = re.compile(r'\{[A-Za-z][A-Za-z0-9]*(?:UUID|Id|ID|uuid)\}')

def detect_namespace(raw_path: str) -> str:
    for p in BASE_PREFIXES:
        if raw_path.startswith(p):
            if 'fmc_platform' in p and 'domainUUID' in p:
                return 'platform_with_domain'
            if 'fmc_platform' in p:
                return 'platform'
            if 'fmc_tid' in p:
                return 'tid'
            if 'fmc_troubleshoot' in p:
                return 'troubleshoot'
            if 'fmc_netmap' in p:
                return 'netmap'
    return 'config'


def normalize_path(raw_path: str) -> str:
    """Strip base prefix and normalize UUID placeholders."""
    rel = raw_path
    for prefix in sorted(BASE_PREFIXES, key=len, reverse=True):
        if raw_path.startswith(prefix):
            rel = raw_path[len(prefix):]
            break
    # Count UUID-like placeholders
    uuids = UUID_RE.findall(rel)
    if len(uuids) >= 3:
        rel = UUID_RE.sub(lambda m, c=iter(['{child_container_uuid}', '{container_uuid}', '{uuid}']):
                          next(c), rel, count=3)
    elif len(uuids) == 2:
        rel = UUID_RE.sub(lambda m, c=iter(['{container_uuid}', '{uuid}']):
                          next(c), rel, count=2)
    elif len(uuids) == 1:
        rel = UUID_RE.sub('{uuid}', rel, count=1)
    return rel or '/'


# Build: norm_path → {method: {query_params, filter_params, has_filter_param}}
spec_paths: dict[str, dict] = {}
for raw_path, path_item in SPEC['paths'].items():
    ns = detect_namespace(raw_path)
    norm = normalize_path(raw_path)
    if norm not in spec_paths:
        spec_paths[norm] = {'namespace': ns, 'raw': raw_path, 'methods': {}}
    for method, op_data in path_item.items():
        if method.startswith('x-') or method == 'parameters':
            continue
        params = op_data.get('parameters', [])
        query_params = set()
        filter_params = set()
        has_filter_str = False
        for p in params:
            if p.get('in') == 'query':
                name = p.get('name', '')
                if name == 'filter':
                    has_filter_str = True
                else:
                    query_params.add(name)
        spec_paths[norm]['methods'][method.upper()] = {
            'query_params': query_params,
            'has_filter': has_filter_str,
            'op_id': op_data.get('operationId', ''),
            'summary': op_data.get('summary', ''),
        }

# ---------------------------------------------------------------------------
# 3. Read all fireREST resource implementations via AST
# ---------------------------------------------------------------------------
FMC_ROOT = Path('fireREST/fmc')

FILTER_KEYS = {
    'command', 'current_security_level', 'destination_interface', 'deployed_status',
    'device_id', 'device_uuids', 'end_time', 'fetch_zero_hitcount', 'fts', 'gid',
    'group_by', 'ids', 'include_count', 'ip_address', 'ips_policy', 'metric',
    'module_ids', 'name', 'name_or_value', 'obj_type', 'overrides', 'protocol',
    'port', 'realm', 'rule_ids', 'operation', 'original_destination',
    'original_destination_port', 'original_source', 'original_source_port',
    'show_only_parents', 'sid', 'sort_by', 'source_interface', 'status',
    'start_time', 'translated_destination', 'translated_destination_port',
    'translated_source', 'translated_source_port', 'unused_only', 'vpn_topology_id',
    'vuln_id',
}
PARAM_KEYS = {
    'above_category', 'category', 'group_dependency', 'hostname', 'insert_after',
    'insert_before', 'name', 'override_target_id', 'section', 'skip_control_readiness',
    'target_index',
}

FILTER_MAP = {
    'command': 'command', 'current_security_level': 'currentSecurityLevel',
    'destination_interface': 'destinationInterface', 'deployed_status': 'deployedStatus',
    'device_id': 'deviceId', 'device_uuids': 'deviceUUIDs', 'end_time': 'endTime',
    'fetch_zero_hitcount': 'fetchZeroHitCount', 'fts': 'fts', 'gid': 'gid',
    'group_by': 'groupBy', 'ids': 'ids', 'include_count': 'includeCount',
    'ip_address': 'ipAddress', 'ips_policy': 'ipspolicy', 'metric': 'metric',
    'module_ids': 'moduleIDs', 'name': 'name', 'name_or_value': 'nameOrValue',
    'obj_type': 'type', 'overrides': 'overrides', 'protocol': 'protocol',
    'port': 'port', 'realm': 'realm', 'rule_ids': 'ids', 'operation': 'operation',
    'original_destination': 'originalDestination',
    'original_destination_port': 'originalDestinationPort',
    'original_source': 'originalSource', 'original_source_port': 'originalSourcePort',
    'show_only_parents': 'showonlyparents', 'sid': 'sid', 'sort_by': 'sortBy',
    'source_interface': 'sourceInterface', 'status': 'status', 'start_time': 'startTime',
    'translated_destination': 'translatedDestination',
    'translated_destination_port': 'translatedDestinationPort',
    'translated_source': 'translatedSource',
    'translated_source_port': 'translatedSourcePort',
    'unused_only': 'unusedOnly', 'vpn_topology_id': 'vpnTopologyId', 'vuln_id': 'id',
}
PARAM_MAP = {
    'above_category': 'aboveCategory', 'category': 'category',
    'group_dependency': 'groupDependency', 'hostname': 'hostname',
    'insert_after': 'insertAfter', 'insert_before': 'insertBefore',
    'name': 'name', 'override_target_id': 'overrideTargetId',
    'section': 'section', 'skip_control_readiness': 'skipControlReadiness',
    'target_index': 'targetIndex',
}


def extract_class_info(file_path: Path) -> list[dict]:
    """Parse a resource __init__.py and return class info dicts."""
    try:
        source = file_path.read_text(encoding='utf-8')
        tree = ast.parse(source)
    except Exception as e:
        return [{'error': str(e), 'file': str(file_path)}]

    classes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [b.id if isinstance(b, ast.Name) else
                 (b.attr if isinstance(b, ast.Attribute) else '') for b in node.bases]
        info = {
            'file': str(file_path),
            'class': node.name,
            'bases': bases,
            'path': None,
            'container_path': None,
            'child_container_path': None,
            'namespace': 'config',
            'supported_filters': [],
            'supported_params': [],
            'min_ver_create': None,
            'min_ver_get': None,
            'min_ver_update': None,
            'min_ver_delete': None,
            'has_get': False,
            'has_create': False,
            'has_update': False,
            'has_delete': False,
        }
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if not isinstance(target, ast.Name):
                        continue
                    name = target.id
                    val = item.value
                    if name == 'PATH' and isinstance(val, ast.Constant):
                        info['path'] = val.value
                    elif name == 'CONTAINER_PATH' and isinstance(val, ast.Constant):
                        info['container_path'] = val.value
                    elif name == 'CHILD_CONTAINER_PATH' and isinstance(val, ast.Constant):
                        info['child_container_path'] = val.value
                    elif name == 'NAMESPACE' and isinstance(val, ast.Constant):
                        info['namespace'] = val.value
                    elif name == 'SUPPORTED_FILTERS' and isinstance(val, (ast.List, ast.Constant)):
                        if isinstance(val, ast.List):
                            info['supported_filters'] = [
                                e.value for e in val.elts if isinstance(e, ast.Constant)
                            ]
                    elif name == 'SUPPORTED_PARAMS' and isinstance(val, (ast.List, ast.Constant)):
                        if isinstance(val, ast.List):
                            info['supported_params'] = [
                                e.value for e in val.elts if isinstance(e, ast.Constant)
                            ]
                    elif name in ('MINIMUM_VERSION_REQUIRED_CREATE',) and isinstance(val, ast.Constant):
                        info['min_ver_create'] = val.value
                    elif name in ('MINIMUM_VERSION_REQUIRED_GET',) and isinstance(val, ast.Constant):
                        info['min_ver_get'] = val.value
                    elif name in ('MINIMUM_VERSION_REQUIRED_UPDATE',) and isinstance(val, ast.Constant):
                        info['min_ver_update'] = val.value
                    elif name in ('MINIMUM_VERSION_REQUIRED_DELETE',) and isinstance(val, ast.Constant):
                        info['min_ver_delete'] = val.value
            elif isinstance(item, ast.FunctionDef):
                fname = item.name
                if fname == 'get':
                    info['has_get'] = True
                elif fname in ('create', 'post'):
                    info['has_create'] = True
                elif fname in ('update', 'put'):
                    info['has_update'] = True
                elif fname in ('delete',):
                    info['has_delete'] = True

        # Check inherited methods by looking at superclass names
        for base in bases:
            if base in ('Resource', 'ChildResource', 'NestedChildResource'):
                # Base classes provide default get/create/update/delete
                info['has_get'] = info['has_get'] or True
                # Default CRUD is provided by base class
        classes.append(info)
    return classes


all_impls = []
for fpath in FMC_ROOT.rglob('__init__.py'):
    # Skip namespace grouping files (those that only contain class with __init__ calling sub-resources)
    if fpath.parent == FMC_ROOT:
        continue
    classes = extract_class_info(fpath)
    for c in classes:
        if c.get('path') is not None:
            all_impls.append(c)

# ---------------------------------------------------------------------------
# 4. Build lookup: normalized path → impl info
# ---------------------------------------------------------------------------
def norm_impl_path(p: str, ns: str) -> str:
    """Normalize impl PATH to match OAS3 normalized form."""
    # Already relative; just ensure it looks like /segment/{uuid} etc.
    return p


# Build reverse map: impl_path → spec_path candidates
impl_by_path: dict[str, list] = defaultdict(list)
for impl in all_impls:
    if impl['path']:
        impl_by_path[impl['path']].append(impl)


# ---------------------------------------------------------------------------
# 5. Run checks and collect findings
# ---------------------------------------------------------------------------

FINDINGS = []

KNOWN_METHODS = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH'}

def add_finding(severity, category, resource_class, file_path, message, breaking=False):
    FINDINGS.append({
        'severity': severity,
        'category': category,
        'class': resource_class,
        'file': file_path,
        'message': message,
        'breaking': breaking,
    })


# 5a. For each impl, try to match it to a spec path
for impl in all_impls:
    impl_path = impl['path']
    cls = impl['class']
    fpath = impl['file']

    if not impl_path:
        continue

    # Attempt to find matching spec path
    # The impl path may be /object/networks/{uuid}
    # The spec norm path is also /object/networks/{uuid}
    matched_spec = spec_paths.get(impl_path)

    # Also try the "list" path (strip /{uuid} suffix for list endpoint)
    list_path = re.sub(r'/\{uuid\}$', '', impl_path)
    matched_spec_list = spec_paths.get(list_path) if list_path != impl_path else None

    # Try container path for ChildResource (list endpoint)
    if matched_spec is None and matched_spec_list is None:
        # Try stripping /None equivalent patterns
        alt_path = impl_path.replace('/{uuid}', '')
        matched_spec = spec_paths.get(impl_path) or spec_paths.get(alt_path)

    if matched_spec is None and matched_spec_list is None:
        # Check if it's a path that uses {container_uuid}
        # Try some path variations
        pass

    # Collect all methods from both individual and list spec paths
    spec_methods = {}
    if matched_spec:
        spec_methods.update(matched_spec.get('methods', {}))
    if matched_spec_list:
        spec_methods.update(matched_spec_list.get('methods', {}))

    if not spec_methods:
        # PATH not found in OAS3 spec at all
        add_finding(
            'WARNING', 'PATH_NOT_IN_SPEC', cls, fpath,
            f'PATH `{impl_path}` not found in OAS3 spec (may be deprecated or wrong path)',
            breaking=False,
        )
        continue

    # --- Check method support ---
    # Base classes implement: GET(list), GET(single), CREATE(POST), UPDATE(PUT), DELETE
    # Check which methods spec defines
    for method, mdata in spec_methods.items():
        if method not in KNOWN_METHODS:
            continue
        if method == 'PATCH':
            # PATCH is rarely used; check if implemented
            add_finding(
                'INFO', 'MISSING_METHOD', cls, fpath,
                f'Spec defines PATCH `{impl_path}` — verify fireREST implements update() via PATCH not PUT',
                breaking=False,
            )

    # --- Check query params: expanded, offset, limit are universal, skip them ---
    UNIVERSAL_PARAMS = {'expanded', 'offset', 'limit', 'bulk', 'domainUUID'}

    for method, mdata in spec_methods.items():
        qparams = mdata.get('query_params', set()) - UNIVERSAL_PARAMS
        has_filter = mdata.get('has_filter', False)

        # Check if spec has a 'filter' query param but impl doesn't declare SUPPORTED_FILTERS
        if has_filter and not impl.get('supported_filters'):
            add_finding(
                'HIGH', 'MISSING_FILTER_SUPPORT', cls, fpath,
                f'Spec defines `filter` query param for {method} `{impl_path}` but SUPPORTED_FILTERS is empty',
                breaking=False,
            )

        # Check for undeclared query params
        for qp in sorted(qparams):
            # Check if it's in PARAM_MAP values
            param_in_map = any(v == qp for v in PARAM_MAP.values())
            param_in_impl = any(PARAM_MAP.get(k) == qp for k in impl.get('supported_params', []))
            if not param_in_map:
                add_finding(
                    'MEDIUM', 'UNMAPPED_QUERY_PARAM', cls, fpath,
                    f'Spec query param `{qp}` for {method} `{impl_path}` has no mapping in PARAMS dict',
                    breaking=False,
                )
            elif qp not in UNIVERSAL_PARAMS and not param_in_impl:
                add_finding(
                    'LOW', 'MISSING_PARAM', cls, fpath,
                    f'Spec query param `{qp}` ({method}) not in SUPPORTED_PARAMS',
                    breaking=False,
                )


# 5b. Check for spec paths with no implementation
impl_paths_set = {impl['path'] for impl in all_impls if impl.get('path')}
# Also build set of list paths
impl_list_paths = {re.sub(r'/\{uuid\}$', '', p) for p in impl_paths_set}

for norm_path, pdata in sorted(spec_paths.items()):
    methods = set(pdata['methods'].keys())
    # Skip paths that are just parameter variations
    if norm_path in impl_paths_set or norm_path in impl_list_paths:
        continue
    # Check if any impl uses this as list path
    found = False
    for ip in impl_paths_set:
        if ip.startswith(norm_path) or norm_path.startswith(ip.rstrip('/{uuid}')):
            found = True
            break
    if not found:
        add_finding(
            'HIGH', 'UNIMPLEMENTED_PATH', '(none)', norm_path,
            f'OAS3 path `{norm_path}` [{",".join(sorted(methods))}] has NO fireREST implementation',
            breaking=False,
        )


# 5c. Check MINIMUM_VERSION constants
for impl in all_impls:
    cls = impl['class']
    fpath = impl['file']
    missing_vers = []
    for attr in ('min_ver_create', 'min_ver_get', 'min_ver_update', 'min_ver_delete'):
        if impl.get(attr) is None:
            missing_vers.append(attr.replace('min_ver_', 'MINIMUM_VERSION_REQUIRED_').upper())
    if missing_vers:
        add_finding(
            'LOW', 'MISSING_VERSION_CONST', cls, fpath,
            f'Missing version constants: {", ".join(missing_vers)}',
            breaking=False,
        )


# ---------------------------------------------------------------------------
# 6. Sort and print findings
# ---------------------------------------------------------------------------
SEV_ORDER = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'WARNING': 3, 'INFO': 4}

FINDINGS.sort(key=lambda x: (SEV_ORDER.get(x['severity'], 9), x['category'], x['class']))

# Summary counts
by_sev = defaultdict(int)
by_cat = defaultdict(int)
for f in FINDINGS:
    by_sev[f['severity']] += 1
    by_cat[f['category']] += 1

print('=' * 80)
print('FIRREST API AUDIT REPORT — vs fmc_oas3_7.4.2')
print('=' * 80)
print(f'\nTotal findings: {len(FINDINGS)}')
print('\nBy severity:')
for sev in ['HIGH', 'MEDIUM', 'LOW', 'WARNING', 'INFO']:
    print(f'  {sev}: {by_sev[sev]}')
print('\nBy category:')
for cat, cnt in sorted(by_cat.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {cnt}')

print('\n' + '=' * 80)
print('DETAILED FINDINGS')
print('=' * 80)
for f in FINDINGS:
    breaking = ' [BREAKING]' if f['breaking'] else ''
    file_short = f['file'].replace('fireREST/', '').replace('\\', '/')
    print(f"\n[{f['severity']}] {f['category']}{breaking}")
    print(f"  Class  : {f['class']}")
    print(f"  File   : {file_short}")
    print(f"  Detail : {f['message']}")

# Save JSON for report generation
with open('audit_findings.json', 'w') as f_out:
    json.dump(FINDINGS, f_out, indent=2)

print(f'\n\nSaved {len(FINDINGS)} findings to audit_findings.json')
