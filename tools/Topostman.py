#!/usr/bin/env python3
import sys
import urllib.parse
import argparse
import yaml  # Requires: pip install pyyaml


def is_static(path):
    static_exts = {
        ".js",
        ".css",
        ".html",
        ".htm",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
        ".map",
        ".json",
    }
    return any(path.lower().endswith(ext) for ext in static_exts)


def generate_openapi_spec(urls, title="Generated API Swagger"):
    # Dictionary to hold the "best" version of a URL for each path
    # Key: path (e.g., "/test")
    # Value: A tuple (param_count, parsed_object, query_params_dictionary)
    best_paths = {}

    # We keep a list of valid parsed objects just to determine the Host URL later
    all_parsed_objects = []

    for url in urls:
        url = url.strip()
        if not url:
            continue

        parsed = urllib.parse.urlparse(url)

        # Skip static files
        if is_static(parsed.path):
            continue

        all_parsed_objects.append(parsed)

        path = parsed.path or "/"
        query_params = urllib.parse.parse_qs(parsed.query)
        param_count = len(query_params.keys())

        # LOGIC CHANGE:
        # 1. If we haven't seen this path before, add it.
        # 2. If we HAVE seen it, check if the new one has MORE parameters.
        if path not in best_paths:
            best_paths[path] = (param_count, parsed, query_params)
        else:
            current_best_count = best_paths[path][0]
            if param_count > current_best_count:
                # This new URL has more parameters, so we replace the old one
                best_paths[path] = (param_count, parsed, query_params)

    # Determine Host URL from the first available valid URL
    host_url = "http://127.0.0.1:8888"
    if all_parsed_objects:
        first_parsed = all_parsed_objects[0]
        if first_parsed.scheme and first_parsed.netloc:
            host_url = f"{first_parsed.scheme}://{first_parsed.netloc}"

    openapi_spec = {
        "openapi": "3.0.0",
        "info": {
            "title": title,
            "version": "1.0.0",
            "description": "Auto-generated from URL pipeline (Max Parameters Logic)",
        },
        "servers": [{"url": host_url, "description": "Target Server"}],
        "paths": {},
        "x-path-templates": [],
    }

    # Iterate through our "Winner" URLs
    for path, data in best_paths.items():
        _, parsed, query_params = data

        openapi_spec["x-path-templates"].append(path)

        if path not in openapi_spec["paths"]:
            openapi_spec["paths"][path] = {}

        parameters_list = []

        if query_params:
            for key in query_params.keys():
                parameters_list.append(
                    {
                        "name": key,
                        "in": "query",
                        "schema": {"type": "string"},
                        # Take the first example value found
                        "example": query_params[key][0],
                    }
                )

        operation = {
            "summary": f"GET {path}",
            "responses": {"200": {"description": "OK"}},
        }

        if parameters_list:
            operation["parameters"] = parameters_list

        openapi_spec["paths"][path]["get"] = operation

    return openapi_spec


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert URL list to OpenAPI YAML")
    parser.add_argument(
        "-n",
        "--name",
        default="Generated API Swagger",
        help="Name of the API Collection",
    )
    parser.add_argument(
        "-f", "--file", help="Path to a file containing URLs (one per line)"
    )
    args = parser.parse_args()

    input_urls = []

    if args.file:
        try:
            with open(args.file, "r") as f:
                input_urls = f.readlines()
        except FileNotFoundError:
            sys.stderr.write(f"Error: File '{args.file}' not found.\n")
            sys.exit(1)
    elif not sys.stdin.isatty():
        input_urls = sys.stdin.readlines()
    else:
        parser.print_help()
        sys.stderr.write("\nError: No input provided. Use -f or pipe URLs via stdin.\n")
        sys.exit(1)

    spec = generate_openapi_spec(input_urls, title=args.name)
    print(yaml.dump(spec, sort_keys=False, default_flow_style=False))

