"""
This file contains the test code for commands that target a bonsai brain in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2021, Microsoft Corp."

from click.testing import CliRunner
from datetime import datetime, timezone
import json
import os
import subprocess
import time
import unittest
import getpass
import socket

from bonsai_cli.commands.bonsai import cli

runner = CliRunner()

current_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


class TestCLI(unittest.TestCase):
    def setUp(self):
        # Uncomment and populate empty value when testing CLI commands against prod endpoints before pypi release
        # os.environ["SIM_WORKSPACE"] = "" # Workspace ID
        # os.environ["TENANT_ID"] = "" # Tenant ID
        # os.environ["URL"] = "https://cp-api.bons.ai"
        # os.environ["GATEWAY_URL"] = "https://api.bons.ai"
        # os.environ["SIM_API_HOST"] = "https://api.bons.ai"
        # os.environ[
        #     "SIM_ACCESS_KEY"
        # ] = "" # Prod sim access key

        # This is required to make workspace id unique
        user_name = getpass.getuser()
        host_name = socket.gethostname()
        machine_name = host_name.split(".")[0]

        os.environ["SIM_WORKSPACE"] = (
            "bdeadmin" + "-" + user_name + "-" + machine_name
        ).lower()  # Workspace ID

        self.workspace_id = os.environ["SIM_WORKSPACE"]
        self.brain_name = "cli_brain_" + current_timestamp
        self.container_simulator_package_name = (
            "cli_container_simulator_package{}".format(current_timestamp)
        )
        self.modelfile_simulator_package_name = (
            "cli_modelfile_simulator_package{}".format(current_timestamp)
        )
        self.assessment_name = "cli_assessment_{}".format(current_timestamp)
        self.unmanaged_simulator_name = None
        self.unmanaged_simulator_session_id = None
        self.brain_version = 1
        self.concept_name = "BalancePole"
        self.action_name = "Train"

    def test_cli(self):
        self.configure()
        self.brain_create()
        self.start_unmanaged_sims()
        self.brain_show()
        self.brain_update()
        self.brain_list()
        self.brain_version_show()
        self.brain_version_update()
        self.brain_version_list()
        self.brain_version_update_inkling()
        self.brain_version_get_inkling()
        self.simulator_unmanaged_list()
        self.simulator_unmanaged_show()
        self.simulator_unmanaged_connect()

        # TODO: start logging and stop logging are disabled since they are unstable. Command owners to investigate and enable
        # TODO: IMPORTANT: Needs to be enabled when running the cli tests before pypi release
        # self.brain_version_start_logging()
        # self.brain_version_stop_logging()
        self.simulator_package_container_create()

        # TODO: Since base image details are not present in database in BDE, modelfile create needs to be disabled till the command owner fixes this
        # TODO: IMPORTANT: Needs to be enabled when running the cli tests before pypi release
        # self.simulator_package_modelfile_create()

        self.simulator_package_modelfile_base_image_list()
        self.simulator_package_show()
        self.simulator_package_update()
        self.simulator_package_list()
        self.brain_version_start_training()
        self.brain_version_assessment_start()
        self.brain_version_assessment_show()
        self.brain_version_assessment_get_configuration()
        self.brain_version_assessment_update()
        self.brain_version_assessment_list()
        self.brain_version_assessment_stop()
        self.brain_version_assessment_delete()
        self.brain_version_stop_training()
        self.brain_version_reset_training()
        self.brain_version_copy()
        self.brain_version_delete()
        self.simulator_package_remove()
        self.brain_delete()

    def configure(self):
        configure = (
            "configure -w {} --tenant-id {} --url {} --gateway-url {} --test".format(
                self.workspace_id,
                os.environ["TENANT_ID"],
                os.environ["URL"],
                os.environ["GATEWAY_URL"],
            )
        )

        response = runner.invoke(cli, configure).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(configure, response),
        )

        print("\n\n{} succeeded".format(configure))

    def brain_create(self):
        create_brain = "brain create -n {} -o json".format(self.brain_name)

        response = runner.invoke(cli, create_brain).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(create_brain, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(create_brain))

    def start_unmanaged_sims(self):
        for x in range(16):
            sim_context = (
                f'{{"deploymentMode": "Testing", '
                f'"purpose": {{ '
                f'"action": "{self.action_name}", '
                f'"target": {{ '
                f'"workspaceName": "{self.workspace_id}", '
                f'"brainName": "{self.brain_name}", '
                f'"brainVersion": "{self.brain_version}", '
                f'"conceptName": "{self.concept_name}" }} }} }}'
            )

            command = subprocess.Popen(
                [
                    "python",
                    "src/sdk3/samples/cartpole-py/cartpole.py",
                    "--sim-context",
                    sim_context,
                    "--workspace",
                    self.workspace_id,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )

            print(f"Starting local sim {x+1} with {command.args}")

    def brain_show(self):
        show_brain = "brain show -n {} -o json".format(self.brain_name)

        response = runner.invoke(cli, show_brain).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(show_brain, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(show_brain))

    def brain_update(self):
        update_brain = "brain update -n {} --description update -o json".format(
            self.brain_name
        )

        response = runner.invoke(cli, update_brain).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(update_brain, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(update_brain))

    def brain_list(self):
        list_brain = "brain list -o json".format(self.brain_name)

        response = runner.invoke(cli, list_brain).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(list_brain, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(list_brain))

    def brain_version_copy(self):
        copy_brain_version = "brain version copy -n {} -o json".format(self.brain_name)

        response = runner.invoke(cli, copy_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(copy_brain_version, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(copy_brain_version))

    def brain_version_show(self):
        show_brain_version = "brain version show -n {} -o json".format(self.brain_name)

        response = runner.invoke(cli, show_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(show_brain_version, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(show_brain_version))

    def brain_version_update(self):
        update_brain_version = (
            "brain version update -n {} --notes updatednotes -o json".format(
                self.brain_name
            )
        )

        response = runner.invoke(cli, update_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(update_brain_version, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(update_brain_version))

    def brain_version_list(self):
        list_brain_version = "brain version list -n {} -o json".format(self.brain_name)

        response = runner.invoke(cli, list_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(list_brain_version, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(list_brain_version))

    def brain_version_update_inkling(self):
        inkling_file = "src/sdk3/samples/cartpole-py/cartpole.ink"
        update_inkling_brain_version = (
            "brain version update-inkling -n {} --file {} -o json".format(
                self.brain_name, inkling_file
            )
        )

        response = runner.invoke(cli, update_inkling_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                update_inkling_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(update_inkling_brain_version))

    def brain_version_get_inkling(self):
        get_inkling_brain_version = "brain version get-inkling -n {} -o json".format(
            self.brain_name
        )

        response = runner.invoke(cli, get_inkling_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                get_inkling_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(get_inkling_brain_version))

    def brain_version_start_logging(self):
        start_logging_brain_version = (
            "brain version start-logging -n {} -d {} -o json".format(
                self.brain_name, self.unmanaged_simulator_session_id
            )
        )

        response = runner.invoke(cli, start_logging_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                start_logging_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(start_logging_brain_version))

    def brain_version_stop_logging(self):
        stop_logging_brain_version = (
            "brain version stop-logging -n {} -d {} -o json".format(
                self.brain_name, self.unmanaged_simulator_session_id
            )
        )

        response = runner.invoke(cli, stop_logging_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                stop_logging_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(stop_logging_brain_version))

    def simulator_package_container_create(self):
        create_simulator_package_container = (
            "simulator package container create "
            "--name {} "
            "--cores-per-instance 1 "
            "--memory-in-gb-per-instance 1 "
            "--image-uri mcr.microsoft.com/bonsai/cartpoledemo:5 "
            "--os-type Linux "
            "--display-name {} "
            "--description {} "
            "--max-instance-count 16 "
            "-o json".format(
                self.container_simulator_package_name,
                self.container_simulator_package_name,
                self.container_simulator_package_name,
            )
        )

        response = runner.invoke(cli, create_simulator_package_container).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                create_simulator_package_container, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 201)

        print("\n\n{} succeeded".format(create_simulator_package_container))

    def simulator_package_modelfile_create(self):
        model_file = "src/Services/EndToEndTestsV2/EndToEndTestsV2/Configuration/InputFiles/mwcartpole_simmodel.zip"
        create_simulator_package_modelfile = (
            "simulator package modelfile create "
            "-n {} "
            "-f {} "
            "--base-image mathworks-simulink-2020a "
            "-o json".format(self.modelfile_simulator_package_name, model_file)
        )

        response = runner.invoke(cli, create_simulator_package_modelfile).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                create_simulator_package_modelfile, response
            ),
        )

        start_index = response.index("{")
        end_index = response.index("}")

        response = response[start_index : end_index + 1]

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 201)

        print("\n\n{} succeeded".format(create_simulator_package_modelfile))

    def simulator_package_modelfile_base_image_list(self):
        list_simulator_package_base_image = (
            "simulator package modelfile list-base-image -o json".format(
                self.container_simulator_package_name
            )
        )

        response = runner.invoke(cli, list_simulator_package_base_image).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                list_simulator_package_base_image, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(list_simulator_package_base_image))

    def simulator_package_show(self):
        show_simulator_package = "simulator package show -n {} -o json".format(
            self.container_simulator_package_name
        )

        response = runner.invoke(cli, show_simulator_package).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(show_simulator_package, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(show_simulator_package))

    def simulator_package_update(self):
        update_simulator_package = (
            "simulator package update -n {} -i 16 -o json".format(
                self.container_simulator_package_name
            )
        )

        response = runner.invoke(cli, update_simulator_package).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(update_simulator_package, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(update_simulator_package))

    def simulator_package_list(self):
        list_simulator_package = "simulator package list -o json"

        response = runner.invoke(cli, list_simulator_package).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(list_simulator_package, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(list_simulator_package))

    def simulator_unmanaged_list(self):
        list_simulator_unmanaged = "simulator unmanaged list -o json"

        response = runner.invoke(cli, list_simulator_unmanaged).output

        print(f"Output of simulator unmanaged list -o json is {response}")

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(list_simulator_unmanaged, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        self.unmanaged_simulator_session_id = response["value"][0]["sessionId"]
        self.unmanaged_simulator_name = response["value"][0]["name"]

        print("\n\n{} succeeded".format(list_simulator_unmanaged))

    def simulator_unmanaged_show(self):
        show_simulator_unmanaged = "simulator unmanaged show -d {} -o json".format(
            self.unmanaged_simulator_session_id
        )

        response = runner.invoke(cli, show_simulator_unmanaged).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(show_simulator_unmanaged, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(show_simulator_unmanaged))

    def simulator_unmanaged_connect(self):
        connect_simulator_unmanaged = "simulator unmanaged connect -b {} -a Train -c BalancePole -d {} -o json".format(
            self.brain_name, self.unmanaged_simulator_session_id
        )

        response = runner.invoke(cli, connect_simulator_unmanaged).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                connect_simulator_unmanaged, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(connect_simulator_unmanaged))

    def brain_version_start_training(self):
        if "BONSAI_IS_BDE" in os.environ:
            start_training_brain_version = (
                "brain version start-training "
                "-n {} "
                "-c BalancePole "
                "-o json".format(self.brain_name)
            )

        else:
            start_training_brain_version = (
                "brain version start-training "
                "-n {} "
                "--simulator-package-name {} "
                "-c BalancePole "
                "--instance-count 16 "
                "-o json".format(self.brain_name, self.container_simulator_package_name)
            )

        response = runner.invoke(cli, start_training_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                start_training_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(start_training_brain_version))
        print(
            "\n\nWaiting for 10 mins for training to progress to test assessment start at {}".format(
                datetime.now()
            )
        )
        time.sleep(
            600
        )  # wait for 10 minutes for training to generate checkpoints so that assessment can be started

    def brain_version_assessment_start(self):
        assessment_config_file = (
            "src/Services/bonsaicli2/bonsai_cli/tests/cartpole-assessment-config.json"
        )

        if "BONSAI_IS_BDE" in os.environ:
            start_brain_version_assessment = (
                "brain version assessment start "
                "-n {} "
                "-b {} "
                "-c BalancePole "
                "-f {} "
                "-o json".format(
                    self.assessment_name,
                    self.brain_name,
                    assessment_config_file,
                )
            )

        else:
            start_brain_version_assessment = (
                "brain version assessment start "
                "-n {} "
                "-b {} "
                "-c BalancePole "
                "--simulator-package-name {} "
                "-f {} "
                "--instance-count 16 "
                "-o json".format(
                    self.assessment_name,
                    self.brain_name,
                    self.container_simulator_package_name,
                    assessment_config_file,
                )
            )

        response = runner.invoke(cli, start_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                start_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(start_brain_version_assessment))

    def brain_version_assessment_show(self):
        show_brain_version_assessment = (
            "brain version assessment show -n {} -b {} -o json".format(
                self.assessment_name, self.brain_name
            )
        )

        response = runner.invoke(cli, show_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                show_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(show_brain_version_assessment))

    def brain_version_assessment_get_configuration(self):
        get_configuration_brain_version_assessment = (
            "brain version assessment get-configuration -n {} -b {} -o json".format(
                self.assessment_name, self.brain_name
            )
        )

        response = runner.invoke(cli, get_configuration_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                get_configuration_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(get_configuration_brain_version_assessment))

    def brain_version_assessment_update(self):
        update_brain_version_assessment = "brain version assessment update -n {} -b {} -des testdescription -o json".format(
            self.assessment_name, self.brain_name
        )

        response = runner.invoke(cli, update_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                update_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(update_brain_version_assessment))

    def brain_version_assessment_list(self):
        list_brain_version_assessment = (
            "brain version assessment list -b {} -o json".format(self.brain_name)
        )

        response = runner.invoke(cli, list_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                list_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(list_brain_version_assessment))

    def brain_version_assessment_stop(self):
        stop_brain_version_assessment = (
            "brain version assessment stop -n {} -b {} -o json".format(
                self.assessment_name, self.brain_name
            )
        )

        response = runner.invoke(cli, stop_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                stop_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(stop_brain_version_assessment))

    def brain_version_stop_training(self):
        stop_training_brain_version = (
            "brain version stop-training "
            "-n {} "
            "-o json".format(self.brain_name, self.container_simulator_package_name)
        )

        response = runner.invoke(cli, stop_training_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                stop_training_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(stop_training_brain_version))

    def brain_version_assessment_delete(self):
        delete_brain_version_assessment = (
            "brain version assessment delete -n {} -b {} -y -o json".format(
                self.assessment_name, self.brain_name
            )
        )

        response = runner.invoke(cli, delete_brain_version_assessment).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                delete_brain_version_assessment, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(delete_brain_version_assessment))

    def brain_version_reset_training(self):
        reset_training_brain_version = (
            "brain version reset-training -n {} --all -y -o json".format(
                self.brain_name
            )
        )

        response = runner.invoke(cli, reset_training_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(
                reset_training_brain_version, response
            ),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(reset_training_brain_version))

    def brain_version_delete(self):
        delete_brain_version = "brain version delete -n {} -y -o json".format(
            self.brain_name
        )

        response = runner.invoke(cli, delete_brain_version).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(delete_brain_version, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(delete_brain_version))

    def simulator_package_remove(self):
        remove_simulator_package = "simulator package remove -n {} -y -o json".format(
            self.container_simulator_package_name
        )

        response = runner.invoke(cli, remove_simulator_package).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(remove_simulator_package, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 202)

        print("\n\n{} succeeded".format(remove_simulator_package))

    def brain_delete(self):
        delete_brain = "brain delete -n {} -y -o json".format(self.brain_name)

        response = runner.invoke(cli, delete_brain).output

        self.assertFalse(
            "Error" in response,
            msg="{} failed with response {}".format(delete_brain, response),
        )

        response = json.loads(response)

        self.assertTrue(response["statusCode"] == 200)

        print("\n\n{} succeeded".format(delete_brain))

    def tearDown(self):
        print("\n\nTearing down all python processes except the test process")

        child_processes = subprocess.Popen(["ps", "-A"], stdout=subprocess.PIPE)
        output, error = child_processes.communicate()

        target_process = "python"

        if output is not None:
            for line in output.splitlines():
                if target_process in str(line):
                    pid = int(line.split(None, 1)[0])

                    if pid != os.getpid():
                        os.system("sudo kill %s" % (pid))

        if error is not None:
            for line in error.splitlines():
                if target_process in str(line):
                    pid = int(line.split(None, 1)[0])

                    if pid != os.getpid():
                        os.system("sudo kill %s" % (pid))


if __name__ == "__main__":
    unittest.main()
