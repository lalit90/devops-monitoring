import subprocess
import requests
import time
import json

# --- CONFIG ---
DOCKER_IMAGE = "lalit1029/python-service2:latest"
DEPLOYMENT = "python-service"
NAMESPACE = "default"
PROMETHEUS_URL = "http://prometheus-server.monitoring.svc.cluster.local:80"
CHAOS_MANIFEST = "python-chaos.yaml"

# --- Helper to run shell commands ---
def run_cmd(cmd, check=True):
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, check=check, text=True, capture_output=True)

# --- STEP 1: Git Flow Automation ---
def git_flow_commit_and_merge(message="Automated commit for MMTR"):
    # Detect current branch
    branch = run_cmd(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()
    print(f"Current branch: {branch}")

    # Stage and commit
    run_cmd(["git", "add", "."])
    try:
        run_cmd(["git", "commit", "-m", message])
    except subprocess.CalledProcessError:
        print(" No changes to commit")

    # Push current branch
    run_cmd(["git", "push", "-u", "origin", branch])

    # If not master, merge into master
    if branch != "master":
        print("Merging into master...")
        run_cmd(["git", "checkout", "master"])
        run_cmd(["git", "pull", "origin", "master"])
        run_cmd(["git", "merge", branch])
        run_cmd(["git", "push", "origin", "master"])
    else:
        print("Already on master, pulling latest...")
        run_cmd(["git", "pull", "origin", "master"])

    print("Git flow complete")

# --- STEP 2: Deploy to Kubernetes ---
def deploy_new_image():
    run_cmd([
        "kubectl", "set", "image", f"deployment/{DEPLOYMENT}",
        f"{DEPLOYMENT}={DOCKER_IMAGE}", "-n", NAMESPACE
    ])
    run_cmd([
        "kubectl", "rollout", "status", f"deployment/{DEPLOYMENT}", "-n", NAMESPACE
    ])
    print("Deployment updated")

# --- STEP 3: Chaos Experiment ---
def run_chaos_experiment():
    run_cmd(["kubectl", "apply", "-f", CHAOS_MANIFEST])
    print("Chaos experiment started (pod kill)")
    time.sleep(40)  # wait for chaos duration
    run_cmd(["kubectl", "delete", "-f", CHAOS_MANIFEST])
    print("Chaos experiment finished")

# --- STEP 4: Validate Monitoring ---
def validate_monitoring():
    query = 'up{job="python-service", instance=~".*5000"}'
    resp = requests.get(f"{PROMETHEUS_URL}/api/v1/query", params={"query": query})
    data = resp.json()
    results = data.get("data", {}).get("result", [])
    if results:
        print("Prometheus UP metric:", json.dumps(results, indent=2))
        print("Monitoring validated")
    else:
        print("No UP metric found — check Prometheus scrape config")

# --- MAIN FLOW ---
if __name__ == "__main__":
    git_flow_commit_and_merge("MMTR pipeline run")
    deploy_new_image()
    run_chaos_experiment()
    validate_monitoring()
