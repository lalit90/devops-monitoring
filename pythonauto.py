import git
import requests
import time
from kubernetes import client, config

# Load kube config
config.load_kube_config()
api = client.CustomObjectsApi()

# Prometheus Pushgateway
pushgateway_url = "http://localhost:9091/metrics/job/devops"

def push_metric(name, value, labels=""):
    metric = f"{name}{labels} {value}\n"
    requests.post(pushgateway_url, data=metric)

repo = git.Repo("https://github.com/lalit90/devops-monitoring.git")
latest_commit = None

while True:
    commit = next(repo.iter_commits('main', max_count=1))
    if latest_commit != commit.hexsha:
        latest_commit = commit.hexsha
        print(f"New commit detected: {latest_commit}")
        push_metric("git_commit_deployments_total", 1, f'{{commit="{latest_commit}"}}')

        chaos_body = {
            "apiVersion": "chaos-mesh.org/v1alpha1",
            "kind": "PodChaos",
            "metadata": {"name": f"pod-kill-{latest_commit}", "namespace": "chaos-testing"},
            "spec": {
                "action": "pod-kill",
                "mode": "one",
                "selector": {"namespaces": ["default"], "labelSelectors": {"app": "python-service"}},
                "duration": "30s"
            }
        }
        api.create_namespaced_custom_object(
            group="chaos-mesh.org", version="v1alpha1",
            namespace="chaos-testing", plural="podchaos", body=chaos_body
        )
        push_metric("chaos_experiment_triggered", 1, f'{{commit="{latest_commit}"}}')

    time.sleep(30)
