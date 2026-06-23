import os
import subprocess
import socket
import sys
import json

def check_command_exists(cmd):
    try:
        subprocess.run([cmd, "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        return False

def check_port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", port))
            return True
        except socket.error:
            return False

def validate_docker_compose():
    print("Validating docker-compose.yml configuration...")
    if not os.path.exists("docker-compose.yml"):
        return {"status": "error", "message": "docker-compose.yml file missing."}
    
    try:
        # Run docker-compose config check
        res = subprocess.run(["docker", "compose", "config"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode == 0:
            return {"status": "success", "message": "Docker Compose configuration is valid."}
        else:
            return {"status": "error", "message": res.stderr}
    except FileNotFoundError:
        return {"status": "warn", "message": "Docker CLI not installed or docker daemon not running. Cannot validate schema."}

def validate_ports():
    print("Checking ports 80 and 8000 availability...")
    port_80 = check_port_free(80)
    port_8000 = check_port_free(8000)
    
    return {
        "port_80_free": port_80,
        "port_8000_free": port_8000,
        "status": "success" if port_80 and port_8000 else "conflict"
    }

def main():
    print("Phoenix AI Production Environment Validation Tool\n")
    
    docker_present = check_command_exists("docker")
    compose_present = check_command_exists("docker-compose") or docker_present # Docker Compose is now part of docker CLI as `docker compose`
    
    print(f"Docker CLI present: {docker_present}")
    print(f"Docker Compose present: {compose_present}\n")
    
    compose_validation = validate_docker_compose()
    print(f"Compose Schema Status: {compose_validation['status'].upper()} - {compose_validation['message']}\n")
    
    port_validation = validate_ports()
    print(f"Port 80 Free: {port_validation['port_80_free']}")
    print(f"Port 8000 Free: {port_validation['port_8000_free']}")
    if port_validation["status"] == "conflict":
        print("WARNING: One or both of the target deployment ports (80, 8000) are currently occupied.")
    else:
        print("Success: All target deployment ports are available.\n")
        
    nginx_valid = os.path.exists("nginx.conf")
    print(f"Nginx config present: {nginx_valid}")
    
    validation_report = {
        "docker_present": docker_present,
        "docker_compose_present": compose_present,
        "compose_schema_valid": compose_validation["status"] == "success",
        "ports_free": port_validation["status"] == "success",
        "nginx_config_present": nginx_valid
    }
    
    os.makedirs("scratch", exist_ok=True)
    with open("scratch/prod_validation_results.json", "w") as f:
        json.dump(validation_report, f, indent=2)
        
    print("\nValidation results saved to scratch/prod_validation_results.json")
    if docker_present and nginx_valid:
        print("PRODUCTION READINESS VALIDATION: PASSED")
    else:
        print("PRODUCTION READINESS VALIDATION: WARNING (Docker or Nginx missing from host system)")

if __name__ == "__main__":
    main()
