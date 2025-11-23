import subprocess
import requests
import time
import json
import os
from dotenv import load_dotenv

# --- Load .env file ---
load_dotenv()

# --- CONFIG from .env ---
DOCKER_USERNAME = os.getenv("DOCKER_USERNAME")
DOCKER_PASSWORD = os.getenv("DOCKER_PASSWORD")
DOCKER_IMAGE = os.getenv("DOCKER_IMAGE")
DEPLOYMENT = os.getenv("DEPLOYMENT")
NAMESPACE = os.getenv("NAMESPACE")
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL")
CHAOS_MANIFEST = os.getenv("CHAOS_MANIFEST")

# --- Helper to run shell commands ---
def run_cmd(cmd, check=True):
    print(f"▶ Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        check=check,
        text=True,
        encoding="utf-8",
        errors="ignore",
        capture_output=True
    )
    return result.stdout.strip()

# --- STEP 1: Git Flow Automation ---
def git_flow_commit_and_merge(message="Automated commit for MMTR"):
    # Detect current branch
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    print(f"📌 Current branch: {branch}")

    # Stage and commit
    run_cmd(["git", "add", "."])
    try:
        run_cmd(["git", "commit", "-m", message])
    except subprocess.CalledProcessError:
        print("ℹ️ No changes to commit")

    # Push current branch
    run_cmd(["git", "push", "-u", "origin", branch])

    # If not master, merge into master
    if branch != "master":
        print("🔀 Merging into master...")
        run_cmd(["git", "checkout", "master"])
        run_cmd(["git", "pull", "origin", "master"])
        run_cmd(["git", "merge", branch])
        run_cmd(["git", "push", "origin", "master"])
    else:
        print("✅ Already on master, pulling latest...")
        run_cmd(["git", "pull", "origin", "master"])

    print("✅ Git flow complete")

# --- STEP 2: Build & Push Docker Image ---
def build_and_push_image(tag="latest"):
    print("🐳 Docker image build and push flow start")
    image_tag = f"{DOCKER_IMAGE}:{tag}"
    run_cmd(["docker", "build", "-t", image_tag, "."])
    run_cmd(["docker", "login", "-u", DOCKER_USERNAME, "-p", DOCKER_PASSWORD])
    run_cmd(["docker", "push", image_tag])
    print(f"✅ Built and pushed {image_tag}")
    return image_tag

# --- STEP 3: Deploy to Kubernetes ---
def deploy_new_image(tag="latest"):
    run_cmd([
        "kubectl", "set", "image", f"deployment/{DEPLOYMENT}",
        f"{DEPLOYMENT}={DOCKER_IMAGE}:{tag}", "-n", NAMESPACE
    ])
    run_cmd([
        "kubectl", "rollout", "status", f"deployment/{DEPLOYMENT}", "-n", NAMESPACE
    ])
    print("✅ Deployment updated")

# --- STEP 4: Chaos Experiment ---
def run_chaos_experiment():
    run_cmd(["kubectl", "apply", "-f", CHAOS_MANIFEST])
    print("🔥 Chaos experiment started (pod kill)")
    time.sleep(40)  # wait for chaos duration
    run_cmd(["kubectl", "delete", "-f", CHAOS_MANIFEST])
    print("✅ Chaos experiment finished")

# --- STEP 5: Validate Monitoring ---
def validate_monitoring():
    query = 'up{job="python-service", instance=~".*5000"}'
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    data = resp.json()
    results = data.get("data", {}).get("result", [])
    if results:
        print("📊 Prometheus UP metric:", json.dumps(results, indent=2))
        print("✅ Monitoring validated")
    else:
        print("❌ No UP metric found — check Prometheus scrape config")


# --- STEP 6: Port Forward Services ---
def port_forward_service(service_name, local_port, service_port, namespace=NAMESPACE):
    print(f"🔌 Port forwarding {service_name} {local_port} -> {service_port}")
    subprocess.Popen([
        "kubectl", "port-forward",
        f"svc/{service_name}", f"{local_port}:{service_port}",
        "-n", namespace
    ])
    time.sleep(5)  # give it a moment to establish
    print(f"✅ {service_name} available at http://localhost:{local_port}")


# --- MAIN FLOW ---
if __name__ == "__main__":
    git_flow_commit_and_merge("MMTR pipeline run")
    build_and_push_image(tag="latest")
    deploy_new_image()
     # Port forward app, Prometheus, and Grafana
    # port_forward_service(service_name=DEPLOYMENT, local_port=5000, service_port=5000)
    # port_forward_service(service_name="prometheus-server", local_port=9090, service_port=80, namespace="monitoring")
    # port_forward_service(service_name="grafana", local_port=3000, service_port=3000, namespace="monitoring")
    run_chaos_experiment()
    validate_monitoring()
