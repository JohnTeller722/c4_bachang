import time
from kubernetes import client, config, utils

config.load_kube_config()

k8sclient = client.ApiClient(configuration = config.load_kube_config())
v1 = client.CoreV1Api()
print("Listing pods with their IPs:")
ret = v1.list_pod_for_all_namespaces(watch=False)
for i in ret.items:
    print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))

utils.action_from_yaml(k8sclient, yaml_file="test1.yaml", verbose=True, action="apply")
time.sleep(2)
utils.action_from_yaml(k8sclient, yaml_file="test1.yaml", verbose=True, action="delete")
time.sleep(2)
utils.action_from_yaml(k8sclient, yaml_file="test1.yaml", verbose=True, action="create")

