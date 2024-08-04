from constructs import Construct

from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_autoscaling as autoscaling,
    aws_iam as iam,
)
from aws_cdk.aws_ecr_assets import DockerImageAsset, Platform

import os

from constructs import Construct

class BridgeModeStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Environment configuration for our envoy and app server containers
        envoy_env = {}
        envoy_env["DEPLOY_REGION"] = Stack.of(self).region

        application_env = {}
        application_env["DEPLOY_REGION"] = Stack.of(self).region

        private_subnet_configuration = [ 
                ec2.SubnetConfiguration( cidr_mask=26, name="private1", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS ), 
                ec2.SubnetConfiguration( cidr_mask=26, name="private2", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS ), 
                ec2.SubnetConfiguration( cidr_mask=26, name="private3", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS ),
        ]
        public_subnet_configuration = [
                ec2.SubnetConfiguration( cidr_mask=26, name="public1", subnet_type=ec2.SubnetType.PUBLIC ), 
                ec2.SubnetConfiguration( cidr_mask=26, name="public2", subnet_type=ec2.SubnetType.PUBLIC ), 
                ec2.SubnetConfiguration( cidr_mask=26, name="public3", subnet_type=ec2.SubnetType.PUBLIC )
        ]

        # Create a new VPC
        vpc = ec2.Vpc(self, "BridgeModeVPC", 
            subnet_configuration= private_subnet_configuration.extend(public_subnet_configuration),
                max_azs=3)

        # Create an ECS cluster in our VPC
        cluster = ecs.Cluster(self, "BridgeModeCluster", vpc=vpc)

        # Create an autoscaling group to run our ECS containers
        ecs_asg_role = iam.Role(
            self,
            "ECSAsgRole",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"),
            description="ECS Autoscaling Group Role",
        )
        ecs_asg_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )
    
        auto_scaling_group = autoscaling.AutoScalingGroup(
            self,
            "BridgeModeAsg",
            vpc=vpc,
            instance_type=ec2.InstanceType("m5.large"),
            machine_image=ecs.EcsOptimizedImage.amazon_linux2(),
            desired_capacity=2,
            role=ecs_asg_role,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            )

        capacity_provider = ecs.AsgCapacityProvider(
            self, "AsgCapacityProvider", auto_scaling_group=auto_scaling_group
        )

        # Add the autoscaling group to our ECS cluster so we can schedule continers
        cluster.add_asg_capacity_provider(capacity_provider)

        task_role = iam.Role(
            self,
            "EnvoyFrontendTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # Give envoy the permission to invoke vpc lattice services
        task_role.attach_inline_policy(
            iam.Policy(
                self,
                "EnvoyFrontendTaskPolicy",
                statements=[
                    iam.PolicyStatement(
                        actions=["vpc-lattice-svcs:Invoke"],
                        resources=["*"],
                    ),
                ],
            )
        )

        # Creaate a new task definition for envoy and add in the container we build from containers/envoy directory
        task_definition = ecs.Ec2TaskDefinition(
            self,
            "envoy-task",
            network_mode=ecs.NetworkMode.BRIDGE,
            task_role=task_role,
        )

        # Add net_admin capability so we can run iptables from within our containers
        parameters = ecs.LinuxParameters(self, "LinuxParameters",
                init_process_enabled=True,
            )
        parameters.add_capabilities(ecs.Capability.NET_ADMIN)

        envoy_asset = DockerImageAsset(
            self,
            "envoy-image",
            directory=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "containers/envoy"
            ),
            asset_name="envoy",
            platform=Platform.LINUX_AMD64,
        )

        task_definition.add_container(
            "envoy",
            image=ecs.ContainerImage.from_docker_image_asset(envoy_asset),
            memory_limit_mib=1024,
            essential=True,
            environment=envoy_env,
            logging=ecs.AwsLogDriver.aws_logs(stream_prefix="envoy"),
            linux_parameters=parameters
        )

        app_asset = DockerImageAsset(
            self,
            "app-container",
            directory=os.path.join(
                os.path.dirname(os.path.realpath(__file__)), "containers/app"
            ),
            asset_name="app-container",
            platform=Platform.LINUX_AMD64,
            build_args={"no-cache":"true"}
        )

        task_definition.add_container(
            "app",
            image=ecs.ContainerImage.from_docker_image_asset(app_asset),
            memory_limit_mib=1024,
            essential=True,
            environment=envoy_env,
            logging=ecs.AwsLogDriver.aws_logs(stream_prefix="app"),
            linux_parameters=parameters
        )

        service = ecs.Ec2Service(self, 'Service', enable_execute_command=True,
                                 cluster=cluster, task_definition=task_definition)

