"""Contract tests for current workflow engine behavior."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# unittest discovery starts at tests/, where tests/workflow would otherwise
# shadow the package under test.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))
sys.modules.pop("workflow", None)

from workflow.engine import build_execution_plan
from workflow.schemas.inputs import ProjectState, WorkflowInput


def sample_infrastructure() -> dict[str, object]:
    return {
        "cluster_arn": "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
        "vpc_id": "vpc-123",
        "private_subnet_ids": ["subnet-123", "subnet-456"],
        "alb_listener_arn": (
            "arn:aws:elasticloadbalancing:us-east-1:123456789012:"
            "listener/app/demo/1/2"
        ),
        "ecs_task_security_group_id": "sg-123",
        "ecr_url": "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo",
    }


def project_state_with_infrastructure() -> ProjectState:
    return ProjectState(
        project_name="demo-project",
        region="us-east-1",
        infrastructure=sample_infrastructure(),
    )


class BuildExecutionPlanTests(unittest.TestCase):
    def test_setup_infra_generates_minimal_infra_file(self) -> None:
        plan = build_execution_plan(
            WorkflowInput(
                intent="setup_infra",
                project_state=ProjectState(project_name="demo-project"),
            )
        )

        self.assertEqual("setup_infra", plan.intent)
        self.assertEqual(1, len(plan.steps))
        step = plan.steps[0]
        self.assertEqual("terraform_apply", step.type)
        self.assertIn("infra/main.tf", step.generated_files)

        rendered = step.generated_files["infra/main.tf"]
        expected_content = [
            'provider "aws"',
            'region = "us-east-1"',
            'resource "aws_vpc" "main"',
            'cidr_block = "10.0.0.0/16"',
            'resource "aws_ecs_cluster" "main"',
            'resource "aws_ecr_repository" "main"',
        ]
        for expected in expected_content:
            self.assertIn(expected, rendered)

    def test_deploy_service_generates_service_file_on_terraform_step(self) -> None:
        plan = build_execution_plan(
            WorkflowInput(
                intent="deploy_service",
                entities={
                    "service_name": "api",
                    "port": 3000,
                    "cpu": 256,
                    "memory": 512,
                    "replicas": 2,
                    "image_tag": "v1",
                    "environment_variables": {"NODE_ENV": "production"},
                },
                project_state=project_state_with_infrastructure(),
            )
        )

        self.assertEqual("deploy_service", plan.intent)
        self.assertEqual(4, len(plan.steps))
        self.assertEqual(
            ["shell_command", "shell_command", "shell_command", "terraform_apply"],
            [step.type for step in plan.steps],
        )
        for step in plan.steps[:3]:
            self.assertEqual({}, step.generated_files)

        terraform_step = plan.steps[3]
        self.assertIn("service/api/main.tf", terraform_step.generated_files)
        rendered = terraform_step.generated_files["service/api/main.tf"]
        expected_content = [
            'resource "aws_cloudwatch_log_group" "main"',
            'resource "aws_lb_target_group" "main"',
            'resource "aws_lb_listener_rule" "main"',
            'resource "aws_ecs_task_definition" "main"',
            'resource "aws_ecs_service" "main"',
            "arn:aws:ecs:us-east-1:123456789012:cluster/demo",
            "vpc-123",
            "subnet-123",
            "subnet-456",
            "arn:aws:elasticloadbalancing:us-east-1:123456789012:listener/app/demo/1/2",
            "sg-123",
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/demo:v1",
            "NODE_ENV",
        ]
        for expected in expected_content:
            self.assertIn(expected, rendered)

    def test_deploy_service_requires_infrastructure_keys(self) -> None:
        with self.assertRaises(ValueError) as context:
            build_execution_plan(
                WorkflowInput(
                    intent="deploy_service",
                    project_state=ProjectState(
                        project_name="demo-project",
                        infrastructure={"cluster_arn": sample_infrastructure()["cluster_arn"]},
                    ),
                )
            )

        message = str(context.exception)
        for missing_key in [
            "vpc_id",
            "private_subnet_ids",
            "alb_listener_arn",
            "ecs_task_security_group_id",
            "ecr_url",
        ]:
            self.assertIn(missing_key, message)

    def test_deploy_service_service_name_fallback_is_explicit(self) -> None:
        plan = build_execution_plan(
            WorkflowInput(
                intent="deploy_service",
                entities={"port": 8080},
                project_state=project_state_with_infrastructure(),
            )
        )

        self.assertIn("service/demo-project/main.tf", plan.steps[3].generated_files)
        self.assertTrue(
            any("project_state.project_name as service_name" in note for note in plan.notes)
        )

    def test_teardown_infra_remains_placeholder_only(self) -> None:
        plan = build_execution_plan(
            WorkflowInput(
                intent="teardown_infra",
                project_state=ProjectState(project_name="demo-project"),
            )
        )

        self.assertEqual("teardown_infra", plan.intent)
        self.assertEqual(1, len(plan.steps))
        self.assertEqual("terraform_destroy", plan.steps[0].type)
        self.assertEqual({}, plan.steps[0].generated_files)


if __name__ == "__main__":
    unittest.main()
