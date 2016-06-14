import re
import os
import json
import logging

import requests
from requests import Session

from utils import version_is_binary
from utils import log_r
from utils import version_and_build
from utils import hostname_for_url

from libraries.provision.ansible_runner import AnsibleRunner

def get_sync_gateway_version(host):
    resp = requests.get("http://{}:4984".format(host))
    log_r(resp)
    resp.raise_for_status()
    resp_obj = resp.json()

    running_version = resp_obj["version"]
    running_version_parts = re.split("[ /(;)]", running_version)

    if running_version_parts[3] == "HEAD":
        # Example: resp_obj["version"] = Couchbase Sync Gateway/HEAD(nobranch)(e986c8a)
        running_version_formatted = running_version_parts[6]
    else:
        # Example: resp_obj["version"] = "Couchbase Sync Gateway/1.3.0(183;bfe61c7)"
        running_version_formatted = "{}-{}".format(running_version_parts[3], running_version_parts[4])

    # Returns the version as 338493 commit format or 1.2.1-4 version format
    return running_version_formatted


def verify_sync_gateway_version(host, expected_sync_gateway_version):
    running_sg_version = get_sync_gateway_version(host)

    logging.info("Expected sync_gateway Version: {}".format(expected_sync_gateway_version))
    logging.info("Running sync_gateway Version: {}".format(running_sg_version))

    if version_is_binary(expected_sync_gateway_version):
        # Example, 1.2.1-4
        if running_sg_version != expected_sync_gateway_version:
            raise ValueError("Unexpected sync_gateway version!! Expected: {} Actual: {}".format(expected_sync_gateway_version, running_sg_version))
    else:
        # Since sync_gateway does not return the full commit, verify the prefix
        if running_sg_version != expected_sync_gateway_version[:7]:
            raise ValueError("Unexpected sync_gateway version!! Expected: {} Actual: {}".format(expected_sync_gateway_version, running_sg_version))


def get_sg_accel_version(host):
    resp = requests.get("http://{}:4985".format(host))
    log_r(resp)
    resp.raise_for_status()
    resp_obj = resp.json()

    running_version = resp_obj["version"]
    running_version_parts = re.split("[ /(;)]", running_version)

    if running_version_parts[3] == "HEAD":
        running_version_formatted = running_version_parts[6]
    else:
        running_version_formatted = "{}-{}".format(running_version_parts[3], running_version_parts[4])

    # Returns the version as 338493 commit format or 1.2.1-4 version format
    return running_version_formatted


def verify_sg_accel_version(host, expected_sg_accel_version):
    running_ac_version = get_sg_accel_version(host)

    logging.info("Expected sg_accel Version: {}".format(expected_sg_accel_version))
    logging.info("Running sg_accel Version: {}".format(running_ac_version))

    if version_is_binary(expected_sg_accel_version):
        # Example, 1.2.1-4
        if running_ac_version != expected_sg_accel_version:
            raise ValueError("Unexpected sync_gateway version!! Expected: {} Actual: {}".format(expected_sg_accel_version, running_ac_version))
    else:
        # Since sync_gateway does not return the full commit, verify the prefix
        if running_ac_version != expected_sg_accel_version[:7]:
            raise ValueError("Unexpected sync_gateway version!! Expected: {} Actual: {}".format(expected_sg_accel_version, running_ac_version))


class SyncGateway:

    def __init__(self):
        self._session = Session()

    def install_sync_gateway(self, sync_gateway_version, sync_gateway_config):

        # Dirty hack -- these have to be put here in order to avoid circular imports
        from libraries.provision.install_sync_gateway import install_sync_gateway
        from libraries.provision.install_sync_gateway import SyncGatewayConfig

        if version_is_binary(sync_gateway_version):
            version, build = version_and_build(sync_gateway_version)
            print("VERSION: {} BUILD: {}".format(version, build))
            sg_config = SyncGatewayConfig(None, version, build, sync_gateway_config, "", False)
        else:
            sg_config = SyncGatewayConfig(sync_gateway_version, None, None, sync_gateway_config, "", False)

        install_sync_gateway(sg_config)

        cluster_config = os.environ["CLUSTER_CONFIG"]
        logging.info("Verfying versions for cluster: {}".format(cluster_config))

        with open("{}.json".format(cluster_config)) as f:
            cluster_obj = json.loads(f.read())

        # Verify sync_gateway versions
        for sg in cluster_obj["sync_gateways"]:
            verify_sync_gateway_version(sg["ip"], sync_gateway_version)

        # Verify sg_accel versions, use the same expected version for sync_gateway for now
        for ac in cluster_obj["sg_accels"]:
            verify_sg_accel_version(ac["ip"], sync_gateway_version)

    def start_sync_gateway(self, url, config):
        target = hostname_for_url(url)
        logging.info("Starting sync_gateway on {} ...".format(target))
        ansible_runner = AnsibleRunner()
        config_path =  os.path.abspath(config)
        status = ansible_runner.run_ansible_playbook(
            "start-sync-gateway.yml",
            extra_vars={
                "sync_gateway_config_filepath": config_path
            },
            subset=target
        )
        assert status == 0, "Could not start sync_gateway"

    def stop_sync_gateway(self, url):
        target = hostname_for_url(url)
        logging.info("Shutting down sync_gateway on {} ...".format(target))
        ansible_runner = AnsibleRunner()
        status = ansible_runner.run_ansible_playbook(
            "stop-sync-gateway.yml",
            subset=target
        )
        assert status == 0, "Could not stop sync_gateway"