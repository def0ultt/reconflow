#!/usr/bin/env python3
"""
Test script for boolean variable flag injection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from core.yaml_module import GenericYamlModule

def test_flag_injection():
    """Test that boolean variables correctly inject flags"""
    
    print("=" * 60)
    print("Testing Boolean Variable Flag Injection")
    print("=" * 60)
    print()
    
    # Load test module
    module = GenericYamlModule('modules/test/boolean_test.yml')
    
    print("📋 Test Module Loaded:")
    print(f"   Name: {module.meta['name']}")
    print(f"   ID: {module.meta['id']}")
    print()
    
    # Test 1: Default values (all false)
    print("Test 1: Default values (all boolean flags = False)")
    print("-" * 60)
    
    # Simulate context preparation (same logic as in yaml_module.py run method)
    render_ctx = {}
    for name, opt in module.options.items():
        if opt.value is not None:
            var_type = opt.metadata.get('type', 'string')
            if var_type == "boolean":
                if opt.value is True:
                    flag = opt.metadata.get('flag', '')
                    render_ctx[name] = flag
                else:
                    render_ctx[name] = ""
            else:
                render_ctx[name] = opt.value
    
    # Render command using module's method
    template_str = "nmap {{service_scan}} {{verbose}} {{aggressive}} {{target}}"
    rendered = module._render_template(template_str, render_ctx)
    
    print(f"   Rendered command: {rendered}")
    expected = "nmap    example.com"
    if rendered == expected:
        print(f"   ✅ PASSED: Matches expected: '{expected}'")
    else:
        print(f"   ❌ FAILED: Expected '{expected}'")
    print()
    
    # Test 2: Set service_scan to true
    print("Test 2: Set service_scan = True")
    print("-" * 60)
    
    module.update_option('service_scan', True)
    
    render_ctx = {}
    for name, opt in module.options.items():
        if opt.value is not None:
            var_type = opt.metadata.get('type', 'string')
            if var_type == "boolean":
                if opt.value is True:
                    flag = opt.metadata.get('flag', '')
                    render_ctx[name] = flag
                else:
                    render_ctx[name] = ""
            else:
                render_ctx[name] = opt.value
    
    rendered = module._render_template(template_str, render_ctx)
    print(f"   Rendered command: {rendered}")
    expected = "nmap -sV   example.com"
    if rendered == expected:
        print(f"   ✅ PASSED: Flag '-sV' injected correctly")
    else:
        print(f"   ❌ FAILED: Expected '{expected}'")
    print()
    
    # Test 3: Set all boolean flags to true
    print("Test 3: Set all boolean flags = True")
    print("-" * 60)
    
    module.update_option('service_scan', True)
    module.update_option('verbose', True)
    module.update_option('aggressive', True)
    
    render_ctx = {}
    for name, opt in module.options.items():
        if opt.value is not None:
            var_type = opt.metadata.get('type', 'string')
            if var_type == "boolean":
                if opt.value is True:
                    flag = opt.metadata.get('flag', '')
                    render_ctx[name] = flag
                else:
                    render_ctx[name] = ""
            else:
                render_ctx[name] = opt.value
    
    rendered = module._render_template(template_str, render_ctx)
    print(f"   Rendered command: {rendered}")
    expected = "nmap -sV -v -A example.com"
    if rendered == expected:
        print(f"   ✅ PASSED: All flags injected correctly")
    else:
        print(f"   ❌ FAILED: Expected '{expected}'")
    print()
    
    # Test 4: Mixed boolean values
    print("Test 4: Mixed boolean values (service_scan=True, others=False)")
    print("-" * 60)
    
    module.update_option('service_scan', True)
    module.update_option('verbose', False)
    module.update_option('aggressive', False)
    
    render_ctx = {}
    for name, opt in module.options.items():
        if opt.value is not None:
            var_type = opt.metadata.get('type', 'string')
            if var_type == "boolean":
                if opt.value is True:
                    flag = opt.metadata.get('flag', '')
                    render_ctx[name] = flag
                else:
                    render_ctx[name] = ""
            else:
                render_ctx[name] = opt.value
    
    rendered = module._render_template(template_str, render_ctx)
    print(f"   Rendered command: {rendered}")
    expected = "nmap -sV   example.com"
    if rendered == expected:
        print(f"   ✅ PASSED: Only service_scan flag injected")
    else:
        print(f"   ❌ FAILED: Expected '{expected}'")
    print()
    
    print("=" * 60)
    print("✅ All flag injection tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    test_flag_injection()

