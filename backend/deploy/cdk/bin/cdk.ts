#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as s3Deploy from 'aws-cdk-lib/aws-s3-deployment'; 
import * as logs from 'aws-cdk-lib/aws-logs'; 
import * as ec2 from 'aws-cdk-lib/aws-ec2'; 
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigw from 'aws-cdk-lib/aws-apigatewayv2';
import { StackProps } from 'aws-cdk-lib'; 
import { HttpLambdaIntegration } from 'aws-cdk-lib/aws-apigatewayv2-integrations';

const app = new cdk.App(); 

export class LitellmStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props: StackProps) {
    super(scope, id, props);

    const vpc = new ec2.Vpc(this, 'MyVpc', {
      maxAzs: 2, // Maximum Availability Zones
    });

    const securityGroup = new ec2.SecurityGroup(this, 'MySecurityGroup', {
      vpc,
      allowAllOutbound: true,
      securityGroupName: 'MySecurityGroup'
    });
    
    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(22), 'Allow HTTP traffic');
    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(4000), 'Allow HTTPS traffic');
    securityGroup.addIngressRule(ec2.Peer.anyIpv4(), ec2.Port.tcp(3306), 'Allow HTTPS traffic');
    const suffix = Math.random().toString(36).substring(2, 6);

    const ecrRepo = new ecr.Repository(this, 'MyECR', {
      repositoryName: `litellm-${suffix}`,
    });

    
    
    const configBucket = new s3.Bucket(this, 'ConfigBucket', {
      bucketName: `bedrock-china-${suffix}`,
    });

    new s3Deploy.BucketDeployment(this, 'ConfigFile', {
      sources: [s3Deploy.Source.asset('../config')],
      destinationBucket: configBucket,
    });

    // 创建 RDS Serverless 集群
    // const rdsCluster = new rds.ServerlessCluster(this, `litellm_${suffix}`, {
    //   engine: rds.DatabaseClusterEngine.auroraPostgres({ version: rds.AuroraPostgresEngineVersion.VER_15_2 }),
    //   vpc: vpc,
    //   removalPolicy: cdk.RemovalPolicy.DESTROY,
    //   parameterGroup: rds.ParameterGroup.fromParameterGroupName(
    //     this,
    //     'ParameterGroup',
    //     'default.aurora-postgresql15'),
    //   scaling: { autoPause: cdk.Duration.minutes(10) },
    //   defaultDatabaseName: 'litellm', 
    // });
    const rdsCluster = new rds.ServerlessCluster(this, `litellm-${suffix}`, {
      engine: rds.DatabaseClusterEngine.auroraPostgres({
        version: rds.AuroraPostgresEngineVersion.VER_15_2 }),
      vpc: vpc,
      scaling: {
        autoPause: cdk.Duration.minutes(10), // Auto pause after 10 minutes of inactivity
        minCapacity: rds.AuroraCapacityUnit.ACU_1, // Minimum capacity
        maxCapacity: rds.AuroraCapacityUnit.ACU_4, // Maximum capacity
      },
      credentials: rds.Credentials.fromPassword('anbei', cdk.SecretValue.plainText('Qwer1234')),
      defaultDatabaseName: 'litellm',  // Optional: specify a database name
    });

    const ecsTaskExecutionRole = new iam.Role(this, 'EcsTaskExecutionRole', {
      assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
    });

    ecsTaskExecutionRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AmazonECSTaskExecutionRolePolicy'));
    ecsTaskExecutionRole.addManagedPolicy(iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonS3ReadOnlyAccess'));

    const ecsCluster = new ecs.Cluster(this, 'LitellmCluster', {
      clusterName: `litellm_${suffix}`,
      vpc: vpc,
    });

    const taskDefinition = new ecs.FargateTaskDefinition(this, 'LitellmTask', {
      taskRole: ecsTaskExecutionRole,
      executionRole: ecsTaskExecutionRole,
      cpu: 2048, // Increase to 2048 (2 vCPUs)
      memoryLimitMiB: 4096, // Increase to 4096 (4 GB)阿·
    });

    taskDefinition.addContainer('LitellmContainer', {
      image: ecs.ContainerImage.fromEcrRepository(ecrRepo),
      memoryLimitMiB: 2048,
      cpu: 1024,
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'ecs',
        logGroup: new logs.LogGroup(this, '/ecs/litellm'),
      }),
      environment: {
        GLOBAL_AWS_REGION: 'us-west-2',
        GLOBAL_AWS_SECRET_ACCESS_KEY: '',
        GLOBAL_AWS_ACCESS_KEY_ID: '',
        LITELLM_CONFIG_BUCKET_OBJECT_KEY: 'litellm_config.yaml',
        AWS_DEFAULT_REGION: 'cn-northwest-1',
        LITELLM_CONFIG_BUCKET_NAME: configBucket.bucketName,
        LITELLM_LOG: 'DEBUG',
        DEEPSEEK_KEY: '',
        DATA_BASE_URL: '',
      },
      portMappings: [{ containerPort: 4000 }],
    });

    new ecs.FargateService(this, 'LitellmService', {
      cluster: ecsCluster,
      taskDefinition,
      desiredCount: 1,
      assignPublicIp: true,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      securityGroups: [securityGroup], 
    });

    const regionMapping = new cdk.CfnMapping(this, 'regionMapping', {
      mapping: {
        'cn-north-1': {
          lwaLayerArn: 'arn:aws-cn:lambda:cn-north-1:041581134020:layer:LambdaAdapterLayerX86:24',
        },
        'cn-northwest-1': {
          lwaLayerArn: 'arn:aws-cn:lambda:cn-northwest-1:069767869989:layer:LambdaAdapterLayerX86:24',
        },
      }
    });
    const frontendFn = new lambda.Function(this, "frontend", {
      runtime: lambda.Runtime.PROVIDED_AL2,
      handler: "bootstrap",
      memorySize: 2048,
      code: lambda.Code.fromAsset("../../../frontend", {
        bundling: {
          image: lambda.Runtime.NODEJS_22_X.bundlingImage,
          command: [
            "bash",
            "-c",
            [
              "npm install",
              "npm run build",
              "cp -au ./out/* /asset-output",
              "cp misc/bootstrap /asset-output",
              "cp misc/nginx.conf /asset-output",
              "chmod +x /asset-output/bootstrap",
            ].join(" && "),
          ],
          user: "root",
        },
      }),
      environment: {
        PORT: "8080",
      },
      layers: [
        lambda.LayerVersion.fromLayerVersionArn(
          this,
          "LWALayer",
          regionMapping.findInMap(this.region, 'lwaLayerArn', `arn:aws:lambda:${this.region}:753240598075:layer:LambdaAdapterLayerX86:24`)
        ),
        new lambda.LayerVersion(this, "NginxLayer", {
          code: lambda.Code.fromAsset("../../../frontend/misc/Nginx123X86.zip"),
        }),
      ],
    });
    const http = new apigw.HttpApi(this, "PortalApi");
    http.addRoutes({
      path: "/{proxy+}",
      methods: [apigw.HttpMethod.GET],
      integration: new HttpLambdaIntegration(
        "frontendFnIntegration",
        frontendFn
      ),
    });
    new cdk.CfnOutput(this, "Web Portal URL", {
      value: http.url!,
      description: "Web portal url",
    });
  }
}

new LitellmStack(app, 'BackLlm', {
});
