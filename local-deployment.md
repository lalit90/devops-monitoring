# 1. Environment Setup
Enable Kubernetes in Docker Desktop.
Install Helm and kubectl.
Install Python 3.9+ with libraries:

```bash
pip install kubernetes gitpython requests flask
pip install flask prometheus-flask-exporter


docker build -t python-service:latest .
docker push lalit1029/python-service:latest

kubectl apply -f python-service.yaml
kubectl port-forward svc/python-service 5000:80


helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl create ns monitoring
helm install prometheus prometheus-community/prometheus -n monitoring
helm upgrade prometheus prometheus-community/prometheus -n monitoring -f values.yaml

kubectl port-forward svc/prometheus-server 9090:80 -n monitoring

helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install grafana grafana/grafana -n monitoring
# 1. Get your 'admin' user password by running:

   kubectl get secret --namespace monitoring grafana -o jsonpath="{.data.admin-password}" 
# Decode password in base 64
    [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('paste_your_base64_string_here'))

   #  dIKGkAFERUUxlIETblzmiAw86Azq27i29IkmEMh2

   kubectl port-forward svc/grafana 3000:80 -n monitoring


helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update
kubectl create ns chaos-testing
helm install chaos-mesh chaos-mesh/chaos-mesh -n chaos-testing

kubectl apply -f python-chaos.yaml

# In grafana add the below path for prometheus as data source
http://prometheus-server.monitoring.svc.cluster.local:80







```
