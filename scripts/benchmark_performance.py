#!/usr/bin/env python3
"""NFR-03 / NFR.06: Performance benchmark suite verifying sub-3-second response times."""
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.test import Client
from django.urls import reverse

MAX_ALLOWED_SECONDS = 3.0

def benchmark_endpoint(client, name, method, url, data=None, iterations=5):
    timings = []
    status_codes = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        if method == 'GET':
            resp = client.get(url)
        elif method == 'POST':
            resp = client.post(url, data=data or {})
        else:
            raise ValueError(f'Unsupported method {method}')
        elapsed = time.perf_counter() - t0
        timings.append(elapsed)
        status_codes.append(resp.status_code)

    avg_ms = (sum(timings) / len(timings)) * 1000
    max_ms = max(timings) * 1000
    passed = max(timings) < MAX_ALLOWED_SECONDS

    return {
        'name': name,
        'method': method,
        'url': url,
        'status': status_codes[-1],
        'avg_ms': avg_ms,
        'max_ms': max_ms,
        'passed': passed,
    }

def main():
    print('========================================================================')
    print('   HOSTEL MANAGEMENT SYSTEM — NFR-03 PERFORMANCE BENCHMARK BASELINE     ')
    print(f'   Target Threshold: < {MAX_ALLOWED_SECONDS:.1f} seconds per operation')
    print('========================================================================\n')

    results = []

    # 1. Unauthenticated & Health Check
    anon = Client()
    results.append(benchmark_endpoint(anon, 'Health Check Endpoint', 'GET', reverse('health_check')))
    results.append(benchmark_endpoint(anon, 'Login Page Render', 'GET', reverse('login')))

    # 2. Student Flows
    student_client = Client()
    student_login = student_client.post(reverse('login'), {'username': 'stu1023', 'password': 'Pass@123'}, follow=True)
    if student_login.status_code == 200:
        results.append(benchmark_endpoint(student_client, 'Student Dashboard', 'GET', reverse('core:dashboard_student')))
        results.append(benchmark_endpoint(student_client, 'Student My Room', 'GET', reverse('allocation:my_room')))
        results.append(benchmark_endpoint(student_client, 'Student My Fees', 'GET', reverse('fees:my_fees')))
        results.append(benchmark_endpoint(student_client, 'Student My Leaves', 'GET', reverse('leave:my_leaves')))
        results.append(benchmark_endpoint(student_client, 'Student Notice Board', 'GET', reverse('notices:board')))

    # 3. Warden Flows
    warden_client = Client()
    warden_login = warden_client.post(reverse('login'), {'username': 'wdn05', 'password': 'Warden@12'}, follow=True)
    if warden_login.status_code == 200:
        results.append(benchmark_endpoint(warden_client, 'Warden Dashboard', 'GET', reverse('core:dashboard_warden')))
        results.append(benchmark_endpoint(warden_client, 'Warden Room Allocation Hub', 'GET', reverse('allocation:manage')))
        results.append(benchmark_endpoint(warden_client, 'Warden Complaints Hub', 'GET', reverse('complaints:manage')))
        results.append(benchmark_endpoint(warden_client, 'Warden Visitor Log', 'GET', reverse('visitors:log')))
        results.append(benchmark_endpoint(warden_client, 'Warden Leave Review List', 'GET', reverse('leave:review')))

    # 4. Administrator Flows
    admin_client = Client()
    admin_login = admin_client.post(reverse('login'), {'username': 'admin01', 'password': 'Admin@12'}, follow=True)
    if admin_login.status_code == 200:
        results.append(benchmark_endpoint(admin_client, 'Admin Dashboard', 'GET', reverse('core:dashboard_admin')))
        results.append(benchmark_endpoint(admin_client, 'Admin Student Directory', 'GET', reverse('students:list')))
        results.append(benchmark_endpoint(admin_client, 'Admin Room Management', 'GET', reverse('rooms:manage')))
        results.append(benchmark_endpoint(admin_client, 'Admin Student Search', 'GET', reverse('students:list') + '?search=Arjun'))
        results.append(benchmark_endpoint(admin_client, 'Admin Fee Management Hub', 'GET', reverse('fees:manage')))
        results.append(benchmark_endpoint(admin_client, 'Admin Outstanding Dues Report', 'GET', reverse('fees:dues_report')))
        results.append(benchmark_endpoint(admin_client, 'Admin User Account List', 'GET', reverse('accounts:users')))

    # Print Table
    header = f"{'Operation / Endpoint':<30} | {'Method':<6} | {'Status':<6} | {'Avg (ms)':<9} | {'Max (ms)':<9} | {'Result':<6}"
    print(header)
    print('-' * len(header))

    all_passed = True
    for r in results:
        res_str = 'PASS' if (r['passed'] and r['status'] == 200) else 'FAIL'
        if not (r['passed'] and r['status'] == 200):
            all_passed = False
        print(f"{r['name']:<30} | {r['method']:<6} | {r['status']:<6} | {r['avg_ms']:>8.2f} | {r['max_ms']:>8.2f} | {res_str:<6}")

    print('-' * len(header))
    if all_passed:
        print('\n[SUCCESS] All operations returned HTTP 200 and responded in under 3.0 seconds (NFR-03 requirement verified).')
    else:
        print('\n[WARNING] One or more operations failed or exceeded 3.0 seconds.')

    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())
