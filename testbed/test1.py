from kubernetes import client, config, dynamic, utils
from kubernetes.client import api_client

config.load_kube_config()

k8sclient = client.ApiClient(configuration = config.load_kube_config())
v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

utils.create_from_yaml(k8sclient, yaml_file="test1.yaml", verbose=True)

