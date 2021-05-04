"""
This file contains the test code for commands that target a bonsai brain in version 2 of the bonsai command line.
"""
__author__ = "Karthik Sankara Subramanian"
__copyright__ = "Copyright 2021, Microsoft Corp."

from click.testing import CliRunner
from datetime import datetime, timezone
import json
import time
import unittest

from bonsai_cli.commands.bonsai import cli

runner = CliRunner()

current_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")


class CliTests(unittest.TestCase):
    def setUp(self):
        self.brain_name = "cli_brain_" + current_timestamp
        self.container_simulator_package_name = (
            "cli_container_simulator_package{}".format(current_timestamp)
        )
        self.modelfile_simulator_package_name = (
            "cli_modelfile_simulator_package{}".format(current_timestamp)
        )
        self.assessment_name = "cli_assessment_{}".format(current_timestamp)

    def test_cli(self):
        self.brain_create()
        self.brain_show()
        self.brain_update()
        self.brain_list()
        self.brain_version_copy()
        self.brain_version_show()
        self.brain_version_update()
        self.brain_version_list()
        self.brain_version_update_inkling()
        self.brain_version_get_inkling()
        self.simulator_package_container_create()
        self.simulator_package_modelfile_create()
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
        self.brain_version_delete()
        self.simulator_package_remove()
        self.brain_delete()

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

    def simulator_package_container_create(self):
        create_simulator_package_container = (
            "simulator package container create "
            "--name {} "
            "--instance-count 16  "
            "--cores-per-instance 1 "
            "--memory-in-gb-per-instance 1 "
            "--image-uri mcr.microsoft.com/bonsai/cartpoledemo:5 "
            "--os-type Linux "
            "--display-name {} "
            "--description {} "
            "--min-instance-count 10 "
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

    def brain_version_start_training(self):
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


if __name__ == "__main__":
    unittest.main()
