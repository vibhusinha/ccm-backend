#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VpcStack } from '../lib/stacks/vpc-stack';
import { BackendStack } from '../lib/stacks/backend-stack';
import { DatabaseStack } from '../lib/stacks/database-stack';
import { V2FrontendStack } from '../lib/stacks/v2-frontend-stack';

const app = new cdk.App();

const env = app.node.tryGetContext('env') || 'staging';
const envConfig = app.node.tryGetContext(env);

if (!envConfig) {
  throw new Error(`Unknown environment: ${env}. Use --context env=staging or --context env=production`);
}

const awsEnv: cdk.Environment = {
  account: process.env.CDK_DEFAULT_ACCOUNT,
  region: 'eu-west-2',
};

// VPC (shared networking)
const vpcStack = new VpcStack(app, `ccm-backend-${env}-vpc`, {
  env: awsEnv,
  envName: env,
});

// Backend (EC2 + ECR + Nginx)
new BackendStack(app, `ccm-backend-${env}-compute`, {
  env: awsEnv,
  envName: env,
  vpc: vpcStack.vpc,
  ec2SecurityGroup: vpcStack.ec2SecurityGroup,
  backendDomainName: envConfig.backendDomainName,
});

// Database (RDS PostgreSQL 16)
new DatabaseStack(app, `ccm-backend-${env}-database`, {
  env: awsEnv,
  envName: env,
  vpc: vpcStack.vpc,
  backendSecurityGroup: vpcStack.ec2SecurityGroup,
  dbInstanceClass: envConfig.dbInstanceClass,
  dbAllocatedStorage: envConfig.dbAllocatedStorage,
  dbName: envConfig.dbName,
  dbUsername: envConfig.dbUsername,
});

// V2 Frontend (S3 + CloudFront)
new V2FrontendStack(app, `ccm-backend-${env}-frontend`, {
  env: awsEnv,
  envName: env,
  s3BucketName: envConfig.v2S3BucketName,
  domainName: envConfig.v2DomainName,
  certificateArn: envConfig.certificateArn,
  apiDomainName: envConfig.backendDomainName,
});
