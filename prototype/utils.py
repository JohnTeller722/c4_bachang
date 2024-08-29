import os
import shutil
import datetime
from model import Experiment, ComponentType, Component
from kubernetes import client, config, utils, stream
from config import settings
from threading import Thread
import asyncio
import websockets
import yaml
import ssl
import logging


RANGECONFIG_VERSION=1.1
kubeclient = client.ApiClient(configuration=config.load_kube_config(settings.KUBECONFIG))
# kubeclient = client.ApiClient(configuration=config.load_kube_config())
api = client.CoreV1Api()

def current_time():
    return str(datetime.datetime.now())

def component_repr(dumper, component):
    attrs = []
    subattrs = {"types": component.types.name, "config": component.config}
    # subattrs.append(("UUID", component.UUID))
    # subattrs.append(("types", component.types.name))
    # subattrs.append(("config", component.config))
    attrs.append((component.name, subattrs))
    # print(attrs)
    return dumper.represent_mapping(u'tag:yaml.org,2002:map', attrs)


def parseUUID(uuid: str, hascrid=False):
    # TODO: UUID验证
    if hascrid:
        try:
            crid = int(uuid[37:])
            uuid = uuid[:36]
        except:
            return None, None
        # print(uuid, crid)
        return (uuid, crid)
    else:
        return uuid

def exp_path(name):
    return settings.RESOURCE_DIR + '/' + name

def trash_path(name):
    return settings.TRASH_DIR + '/' + name


def write_exp(_t):
    yaml.SafeDumper.add_representer(ComponentType, yaml.representer.SafeRepresenter.represent_int)
    yaml.SafeDumper.add_representer(Component, component_repr)
    try:
        os.mkdir(exp_path(_t.name))
    except FileExistsError:
        pass
    data = dict()
    data["version"] = RANGECONFIG_VERSION
    data.update(_t.dict_dump())
    with open(exp_path(_t.name)+"/range-config.yaml", "w", encoding="utf-8") as f:
        yaml.dump(data, f, yaml.SafeDumper, allow_unicode=True, sort_keys=False)

def remove_exp(_t): # 软删除
    try:
        shutil.move(exp_path(_t.dirname), settings.TRASH_DIR + '/' + _t.name)
        return True
    except:
        return False


def action_from_yaml(yaml_file, workdir="./", action="apply"):
    if workdir[-1] != '/':
        workdir = workdir + '/'
    utils.action_from_yaml(kubeclient, yaml_file=workdir+yaml_file,
                           verbose=True, action=action)

def list_experiments(namespace="default"):
    # TODO:增加list项目
    # print([i.metadata for i in api.list_namespaced_pod(namespace).items])
    return [i.metadata.name for i in api.list_namespaced_pod(namespace).items]

def get_pod_status(pod, namespace="default"):
    try:
        # status = api.read_namespaced_pod_status(pod, namespace).status.container_statuses[0].last_state
        status = api.read_namespaced_pod_status(pod, namespace).status.container_statuses[0]
        print(status)
    except IndexError:
        return "Unknown"
    return "Running"
    if status.running:
        if status.terminated:
            return "Crashed"
        else:
            return "Running"
    else:
        return "Failed"

def read_pod_log(pod, namespace="default"):
    try:
        logdata = api.read_namespaced_pod_log(pod, namespace)
        print(logdata)
        return logdata
    except Exception as e:
        raise e
        return None

class PodExecUnsupportedError(Exception):
    def __init__(self):
        pass

    def __str__(self):
        msg = "This pod doesn't support interactive shell."
        return msg

def get_kube_arch() -> str:
    try:
        response = client.VersionApi(kubeclient).get_code()
        # logging.debug(f"来自服务器的消息：{response}")
        # print(response)
        return response.platform
    except Exception as e:
        logging.warning(e)
        return ""



def ssh_tunnel(pod, namespace="default", port=20022):
    command = ["/bin/sh"]
    # print(api.connect_get_namespaced_pod_exec)
    # print(stream)
    logging.debug(f"utils:连接容器{pod}")
    ssh_stream = stream.stream(api.connect_get_namespaced_pod_exec,
                        name=pod,
                        namespace=namespace,
                        command=command,
                        stderr=True,
                        stdin=True,
                        stdout=True,
                        tty=True,
                        _preload_content=False)

    async def ssh_message_stdin(ws):
        async for message in ws:
            # print("MESSAGE:", message)
            # print(type(message))
            # print(ssh_stream.sock)
            try:
                ssh_stream.write_stdin(message)
            except ssl.SSLEOFError:
                raise PodExecUnsupportedError


    async def ssh_message_stdout(ws):
        while True:
            if ssh_stream.peek_stdout():
                stdout = ssh_stream.read_stdout()
                if stdout:
                    await ws.send(stdout)
                continue
            if ssh_stream.peek_stderr():
                stderr = ssh_stream.read_stderr()
                if stderr:
                    await ws.send(stderr)
            await asyncio.sleep(0.01)

    async def ssh_handle(ws):
        try:
            receiver = asyncio.get_event_loop().create_task(ssh_message_stdin(ws))
        except:
            raise PodExecUnsupportedError
        sender = asyncio.get_event_loop().create_task(ssh_message_stdout(ws))
        try:
            await receiver
        except:
            await ws.send("Failed: this pod doesn't support interactive shell.")
            # raise PodExecUnsupportedError
            logging.warning(f"The pod {pod} doesn't support interactive shell.")
        await sender

    async def run():
        async with websockets.serve(ssh_handle, "0.0.0.0", port):
            await asyncio.Future()

    asyncio.run(run())

    
# if __name__ == "__main__":
    # print(test_kube_connection())
    # print(list_experiments())
    # read_pod_log("coredns-6799fbcd5-dnkxc", namespace="kube-system")
    # for i in list_experiments().items:
    #     print(i.metadata.name)
    # ssh_tunnel("metrics-server-54fd9b65b-wgcw2", namespace="kube-system", port=5002)

