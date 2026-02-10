#!/usr/bin/env python3
import sys
import urllib.parse
import argparse
import yaml  # Requires: pip install pyyaml

def is_static(path):
    static_exts = {
        '.js', '.css', '.html', '.htm', 
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', 
        '.woff', '.woff2', '.ttf', '.eot', '.map', '.json'
    }
    return any(path.lower().endswith(ext) for ext in static_exts)

def get_unique_signature(url):
    """
    Creates a signature based on the path and the *keys* of the query parameters.
    Values are ignored for deduplication.
    """
    parsed = urllib.parse.urlparse(url)
    
    # Parse query params to get keys only
    query_params = urllib.parse.parse_qs(parsed.query)
    sorted_keys = tuple(sorted(query_params.keys()))
    
    # Signature is (Path, Tuple of sorted query keys)
    return parsed.path, sorted_keys

def generate_openapi_spec(urls, title="Generated API Swagger"):
    unique_signatures = set()
    valid_urls = []

    # 1. Filter and Deduplicate
    for url in urls:
        url = url.strip()
        if not url:
            continue

        parsed = urllib.parse.urlparse(url)
        
        # Skip static files
        if is_static(parsed.path):
            continue

        # Check for duplicates
        signature = get_unique_signature(url)
        if signature in unique_signatures:
            continue
        
        unique_signatures.add(signature)
        valid_urls.append(url)

    # 2. Build OpenAPI Structure
    # Try to detect the host from the first URL, default to localhost
    host_url = "http://127.0.0.1:8888"
    if valid_urls:
        first_parsed = urllib.parse.urlparse(valid_urls[0])
        if first_parsed.scheme and first_parsed.netloc:
            host_url = f"{first_parsed.scheme}://{first_parsed.netloc}"

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,  # Uses the argument provided via -n
            "version": "1.0.0",
            "description": "Auto-generated from URL pipeline"
        },
        "servers": [
            {"url": host_url, "description": "Target Server"}
        ],
        "paths": {},
        "x-path-templates": []
    }

    # 3. Populate Paths and Templates
    for url in valid_urls:
        parsed = urllib.parse.urlparse(url)
        path = parsed.path
        if not path:
            path = "/"
            
        # Add to custom x-path-templates
        openapi_spec["x-path-templates"].append(path)

        # Ensure path exists in object
        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}

        # Prepare Query Parameters for the spec
        query_params = urllib.parse.parse_qs(parsed.query)
        parameters_list = []
        
        if query_params:
            for key in query_params.keys():
                parameters_list.append({
                    "name": key,
                    "in": "query",
                    "schema": {"type": "string"},
                    "example": query_params[key][0] # Use the first value as example
                })

        # Define the Operation (GET default)
        operation = {
            "summary": f"GET {path}",
            "responses": {
                "200": {"description": "OK"}
            }
        }
        
        if parameters_list:
            operation["parameters"] = parameters_list

        openapi_spec["paths"][path]["get"] = operation

    return openapi_spec

if __name__ == "__main__":
    # Check dependencies
    try:
        import yaml
    except ImportError:
        sys.stderr.write("Error: 'pyyaml' is missing. Please run: pip install pyyaml\n")
        sys.exit(1)

    # Parse Arguments
    parser = argparse.ArgumentParser(description="Convert URL list to OpenAPI YAML")
    parser.add_argument("-n", "--name", default="Generated API Swagger", help="Name of the API Collection")
    args = parser.parse_args()

    # Read from stdin
    if sys.stdin.isatty():
        print("Usage: cat urls.txt | python3 tool.py -n 'My API Name'")
        sys.exit(1)
        
    input_urls = sys.stdin.readlines()
    
    spec = generate_openapi_spec(input_urls, title=args.name)
    
    # Print YAML to stdout
    print(yaml.dump(spec, sort_keys=False, default_flow_style=False))
