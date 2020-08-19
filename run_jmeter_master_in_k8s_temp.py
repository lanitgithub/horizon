import time

from kubernetes import config
from kubernetes.client import Configuration
from kubernetes.client.api import core_v1_api
from kubernetes.client.rest import ApiException


def exec_commands(api_instance):
    name = 'jmeter-master-test'
    resp = None
    try:
        resp = api_instance.read_namespaced_pod(name=name,
                                                namespace='default')
    except ApiException as e:
        if e.status != 404:
            print("Unknown error: %s" % e)
            exit(1)

    if not resp:

        print("Pod %s does not exist. Creating it..." % name)
        pod_manifest = {
            'apiVersion': 'v1',
            'kind': 'Pod',
            'metadata': {
                'name': name
            },
            'spec': {
                'containers': [{
                    'image': 'vmarrazzo/jmeter',
                    'volumeMounts': [{
                        'mountPath': '/mnt/jmeter',
                        'name': 'jmeter-script-volume'
                    }],
                    'name': 'sleep',
                    "args": [
                        "-n",
                        "-t /mnt/jmeter/jmeter_debug_test.jmx",
                    ]
                }],
                'restartPolicy': 'Never',
                'volumes': [{
                    'name': 'jmeter-script-volume',
                    'hostPath': {
                        'path': '/host_mnt/d/jmeter-script-volume',
                        'type': 'DirectoryOrCreate'
                    }
                }]
            }
        }
        resp = api_instance.create_namespaced_pod(body=pod_manifest,
                                                  namespace='default')
        while True:
            resp = api_instance.read_namespaced_pod(name=name,
                                                    namespace='default')
            if resp.status.phase != 'Pending':
                break
            time.sleep(1)
        print("Done.")

        while True:
            resp = api_instance.read_namespaced_pod(name=name,
                                                    namespace='default')
            print(resp.status.phase)
            time.sleep(1)
        print("Done.")


def main():
    config.load_kube_config()
    c = Configuration()
    c.assert_hostname = False
    Configuration.set_default(c)
    core_v1 = core_v1_api.CoreV1Api()

    exec_commands(core_v1)


if __name__ == '__main__':
    main()