from bonsai_cli.api import BonsaiAPI
from unittest import TestCase
from unittest.mock import patch
from typing import Any, Dict, List, Optional, Union
from click.testing import CliRunner
from bonsai_cli.commands.bonsai import cli
import json


class BonsaiAPIForTest(BonsaiAPI):
    def __init__(self):
        self.patches: Dict[str, Any] = {}
        self.brain_versions: Dict[str, List[int]] = {}
        self.sessions: Dict[str, Any] = {}

    def with_brain_version(self, brain_name: str, version: int):
        if brain_name not in self.brain_versions:
            self.brain_versions[brain_name] = []

        self.brain_versions[brain_name].append(version)
        return self

    def with_brain_versions(self, brain_name: str, versions: List[int]):
        if brain_name not in self.brain_versions:
            self.brain_versions[brain_name] = []

        self.brain_versions[brain_name].extend(versions)
        return self

    def _parse_purpose(self, purpose_str: str) -> Dict[str, Any]:
        b1 = purpose_str.split(" ")

        action = b1[0].capitalize()

        b2 = b1[1].split("/")
        workspace = b2[0]
        brain = b2[1] if len(b2) > 1 else ""
        version = int(b2[2]) if len(b2) > 2 else 0
        concept = b2[3] if len(b2) > 3 else ""

        return {
            "purpose": {
                "action": action,
                "target": {
                    "workspaceName": workspace,
                    "brainName": brain,
                    "version": version,
                    "concept": concept,
                },
            }
        }

    def with_session(self, session_id: str, simulator_name: str, purpose: str):
        self.sessions.update(
            {
                session_id: {
                    "sessionId": session_id,
                    "simulatorName": simulator_name,
                    "simulatorContext": self._parse_purpose(purpose),
                }
            }
        )
        return self

    def list_brain_versions(
        self,
        name: str,
        workspace: Optional[str] = None,
        debug: bool = False,
        output: Optional[str] = None,
    ) -> Dict[str, List[Dict[str, Union[int, str]]]]:
        if name not in self.brain_versions:
            return {"value": []}

        return {
            "value": [
                {"version": n, "trainingState": "Idle", "assessmentState": "Idle"}
                for n in self.brain_versions[name]
            ]
        }

    def list_unmanaged_sim_session(
        self,
        workspace: Optional[str] = None,
        debug: bool = False,
        output: Optional[str] = None,
    ):
        return {
            "value": [
                {
                    "sessionId": k,
                    "simulatorName": v["simulatorName"],
                    "simulatorContext": v["simulatorContext"],
                }
                for k, v in self.sessions.items()
            ]
        }

    def patch_sim_session(
        self,
        session_id: str,
        brain_name: str,
        version: int,
        purpose_action: str,
        concept_name: str,
        workspace: Optional[str] = None,
        debug: bool = False,
        output: Optional[str] = None,
    ):
        matches: List[Dict[str, Any]] = [
            {k: v} for k, v in self.sessions.items() if k == session_id
        ]

        if len(matches) != 1:
            return {"status": "NotFound", "statusCode": 404}

        self.sessions[session_id]["simulatorContext"]["purpose"][
            "action"
        ] = purpose_action
        self.sessions[session_id]["simulatorContext"]["purpose"]["target"][
            "brainName"
        ] = brain_name
        self.sessions[session_id]["simulatorContext"]["purpose"]["target"][
            "version"
        ] = version
        self.sessions[session_id]["simulatorContext"]["purpose"]["target"][
            "concept"
        ] = concept_name

        self.patches.update(
            {
                session_id: "{} {}/{}/{}/{}".format(
                    purpose_action, workspace, brain_name, version, concept_name
                )
            }
        )
        return {"status": "Succeeded", "statusCode": 200}


class TestPatchSimulatorPurpose(TestCase):
    def _do_patch(self, test_api: BonsaiAPI, cmd_line: str):
        with patch(
            "bonsai_cli.commands.simulator_unmanaged.api", return_value=test_api
        ):
            with patch("bonsai_cli.utils.api", return_value=test_api):
                runner = CliRunner()

                return runner.invoke(
                    cli, "simulator unmanaged connect {} --output json".format(cmd_line)
                )

    def test_patch_purpose_one_session(self):

        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("adder", [3, 9, 4])
            .with_session("12345_10.1.2.3", "old_sim", "Inactive bdeadmin")
        )

        response = self._do_patch(
            test_api,
            "--workspace-id bdeadmin "
            "--brain-name adder "
            "--brain-version 1 "
            "--concept-name addition "
            "--session-id 12345_10.1.2.3 "
            "--action train",
        )

        self.assertEqual(0, response.exit_code)
        output = json.loads(response.output)
        self.assertIn("statusCode", output)
        self.assertEqual(200, output["statusCode"])

        self.assertIn("12345_10.1.2.3", test_api.patches)
        self.assertEqual(
            "Train bdeadmin/adder/1/addition", test_api.patches["12345_10.1.2.3"]
        )

    def test_patch_purpose_one_active_session(self):

        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("adder", [3, 9, 4])
            .with_session(
                "12345_10.1.2.3", "old_sim", "Train bdeadmin/adder/1/addition"
            )
        )

        response = self._do_patch(
            test_api,
            "--workspace-id bdeadmin "
            "--brain-name adder "
            "--brain-version 2 "
            "--concept-name addition "
            "--session-id 12345_10.1.2.3 "
            "--action train",
        )

        self.assertEqual(0, response.exit_code)
        output = json.loads(response.output)
        self.assertIn("statusCode", output)
        self.assertEqual(200, output["statusCode"])

        self.assertIn("12345_10.1.2.3", test_api.patches)
        self.assertEqual(
            "Train bdeadmin/adder/2/addition", test_api.patches["12345_10.1.2.3"]
        )

    def test_patch_purpose_simulator_name(self):

        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("cortex", [3, 9, 4])
            .with_brain_versions("viper", [2, 3])
            .with_session(
                "1234_10.2.3.4", "small_sim", "Train bdeadmin/cortex/3/synapse"
            )
            .with_session("2345_10.3.4.5", "big_sim", "Inactive bdeadmin")
            .with_session("2346_10.3.4.5", "little_sim", "Inactive bdeadmin")
            .with_session("2347_10.3.4.2", "big_sim", "Train bdeadmin/cortex/3/synapse")
            .with_session("2348_10.3.4.5", "big_sim", "Inactive bdeadmin")
        )

        response = self._do_patch(
            test_api,
            "--workspace-id bdeadmin2 "
            "--brain-name viper "
            "--brain-version 8 "
            "--concept-name reduction "
            "--simulator-name big_sim "
            "--action Assess",
        )

        self.assertEqual(0, response.exit_code)
        output = json.loads(response.output)
        self.assertIn("statusCode", output)
        self.assertEqual(200, output["statusCode"])
        self.assertIn("statusMessage", output)
        self.assertIn("simulatorsFound", output["statusMessage"])
        self.assertEqual(3, output["statusMessage"]["simulatorsFound"])
        self.assertIn("simulatorsConnected", output["statusMessage"])
        self.assertEqual(3, output["statusMessage"]["simulatorsConnected"])
        self.assertIn("simulatorsNotConnected", output["statusMessage"])
        self.assertEqual(0, output["statusMessage"]["simulatorsNotConnected"])

        self.assertEqual(3, len(test_api.patches))

        self.assertNotIn("1234_10.2.3.4", test_api.patches)

        self.assertIn("2345_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2345_10.3.4.5"]
        )

        self.assertNotIn("2346_10.3.4.5", test_api.patches)

        self.assertIn("2347_10.3.4.2", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2347_10.3.4.2"]
        )

        self.assertIn("2348_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2345_10.3.4.5"]
        )

    def test_patch_purpose_simulator_name_then_session_id(self):
        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("cortex", [3, 9, 4])
            .with_brain_versions("viper", [8, 9])
            .with_brain_versions("asp", [9])
            .with_session(
                "1234_10.2.3.4", "small_sim", "Train bdeadmin/cortex/3/synapse"
            )
            .with_session("2345_10.3.4.5", "big_sim", "Inactive bdeadmin")
            .with_session("2346_10.3.4.5", "little_sim", "Inactive bdeadmin")
            .with_session("2347_10.3.4.2", "big_sim", "Inactive bdeadmin")
            .with_session("2348_10.3.4.5", "big_sim", "Inactive bdeadmin")
        )

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin2 "
            "--brain-name viper "
            "--brain-version 8 "
            "--concept-name reduction "
            "--simulator-name big_sim "
            "--action Assess",
        )

        self.assertEqual(3, len(test_api.patches))

        self.assertNotIn("1234_10.2.3.4", test_api.patches)

        self.assertIn("2345_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2345_10.3.4.5"]
        )

        self.assertNotIn("2346_10.3.4.5", test_api.patches)

        self.assertIn("2347_10.3.4.2", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2347_10.3.4.2"]
        )

        self.assertIn("2348_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/viper/8/reduction", test_api.patches["2348_10.3.4.5"]
        )

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin2 "
            "--brain-name asp "
            "--brain-version 9 "
            "--concept-name cleopatra "
            "--session-id 2348_10.3.4.5 "
            "--action Assess",
        )

        self.assertEqual(3, len(test_api.patches))

        self.assertIn("2348_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin2/asp/9/cleopatra", test_api.patches["2348_10.3.4.5"]
        )

    def test_patch_purpose_simulator_name_nosuch_name(self):
        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("cortex", [3, 9, 4])
            .with_brain_versions("viper", [7, 8])
            .with_session(
                "1234_10.2.3.4", "small_sim", "Train bdeadmin/cortex/3/synapse"
            )
            .with_session("2345_10.3.4.5", "big_sim", "Inactive bdeadmin")
            .with_session("2346_10.3.4.5", "little_sim", "Inactive bdeadmin")
            .with_session("2347_10.3.4.2", "big_sim", "Inactive bdeadmin")
            .with_session("2348_10.3.4.5", "big_sim", "Inactive bdeadmin")
        )

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin2 "
            "--brain-name viper "
            "--brain-version 8 "
            "--concept-name reduction "
            "--simulator-name elite_sim "
            "--action Train",
        )

        self.assertEqual(0, len(test_api.patches))

    def test_patch_purpose_latest(self):

        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("cortex", [3, 9, 4])
            .with_brain_versions("viper", [12, 15, 13])
            .with_session(
                "1234_10.2.3.4", "small_sim", "Train bdeadmin/cortex/3/synapse"
            )
            .with_session("2345_10.3.4.5", "big_sim", "Inactive bdeadmin")
            .with_session("2346_10.3.4.5", "little_sim", "Inactive bdeadmin")
            .with_session("2347_10.3.4.2", "big_sim", "Train bdeadmin/cortex/4/axon")
            .with_session("2348_10.3.4.5", "big_sim", "Inactive bdeadmin")
        )

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin "
            "--brain-name viper "
            "--concept-name reduction "
            "--simulator-name big_sim "
            "--action Assess",
        )

        self.assertEqual(3, len(test_api.patches))

        self.assertNotIn("1234_10.2.3.4", test_api.patches)

        self.assertIn("2345_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin/viper/15/reduction", test_api.patches["2345_10.3.4.5"]
        )

        self.assertNotIn("2346_10.3.4.5", test_api.patches)

        self.assertIn("2347_10.3.4.2", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin/viper/15/reduction", test_api.patches["2347_10.3.4.2"]
        )

        self.assertIn("2348_10.3.4.5", test_api.patches)
        self.assertEqual(
            "Assess bdeadmin/viper/15/reduction", test_api.patches["2348_10.3.4.5"]
        )

    def test_patch_purpose_latest_nosuch_brain(self):
        test_api = (
            BonsaiAPIForTest()
            .with_brain_versions("cortex", [3, 9, 4])
            .with_brain_versions("viper", [12, 15, 13])
            .with_session(
                "1234_10.2.3.4", "small_sim", "Train bdeadmin/cortex/3/synapse"
            )
            .with_session("2345_10.3.4.5", "big_sim", "Inactive bdeadmin")
            .with_session("2346_10.3.4.5", "little_sim", "Inactive bdeadmin")
            .with_session("2347_10.3.4.2", "big_sim", "Train bdeadmin/cortex/4/axon")
            .with_session("2348_10.3.4.5", "big_sim", "Inactive bdeadmin")
        )

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin "
            "--brain-name cobra "
            "--concept-name reduction "
            "--simulator-name big_sim "
            "--action Assess",
        )

        self.assertEqual(0, len(test_api.patches))

        self._do_patch(
            test_api,
            "--workspace-id bdeadmin "
            "--brain-name cobra "
            "--concept-name reduction "
            "--session-id 2345_10.3.4.5 "
            "--action Assess",
        )

        self.assertEqual(0, len(test_api.patches))
