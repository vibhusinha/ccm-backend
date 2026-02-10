import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as rds from 'aws-cdk-lib/aws-rds';
import { Construct } from 'constructs';

export interface DatabaseStackProps extends cdk.StackProps {
  envName: string;
  vpc: ec2.Vpc;
  backendSecurityGroup: ec2.SecurityGroup;
  dbInstanceClass: string;
  dbAllocatedStorage: number;
  dbName: string;
  dbUsername: string;
}

export class DatabaseStack extends cdk.Stack {
  public readonly dbInstance: rds.DatabaseInstance;
  public readonly dbSecret: cdk.aws_secretsmanager.ISecret;
  public readonly dbSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    // Security group for RDS
    this.dbSecurityGroup = new ec2.SecurityGroup(this, 'DbSecurityGroup', {
      vpc: props.vpc,
      securityGroupName: `ccm-${props.envName}-rds-sg`,
      description: 'Security group for RDS PostgreSQL',
      allowAllOutbound: false,
    });

    // Allow inbound from backend EC2 security group
    this.dbSecurityGroup.addIngressRule(
      props.backendSecurityGroup,
      ec2.Port.tcp(5432),
      'Allow PostgreSQL from backend EC2'
    );

    // Parse instance class
    const instanceClass = props.dbInstanceClass.includes('t4g')
      ? ec2.InstanceClass.T4G
      : ec2.InstanceClass.T3;
    const instanceSize = props.dbInstanceClass.includes('micro')
      ? ec2.InstanceSize.MICRO
      : ec2.InstanceSize.SMALL;

    // RDS PostgreSQL instance
    this.dbInstance = new rds.DatabaseInstance(this, 'Database', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),
      instanceType: ec2.InstanceType.of(instanceClass, instanceSize),
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      securityGroups: [this.dbSecurityGroup],
      databaseName: props.dbName,
      credentials: rds.Credentials.fromGeneratedSecret(props.dbUsername, {
        secretName: `ccm-${props.envName}-db-credentials`,
      }),
      allocatedStorage: props.dbAllocatedStorage,
      storageType: rds.StorageType.GP3,
      storageEncrypted: true,
      multiAz: false,
      backupRetention: cdk.Duration.days(props.envName === 'production' ? 14 : 7),
      deletionProtection: props.envName === 'production',
      removalPolicy: props.envName === 'production'
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
      instanceIdentifier: `ccm-${props.envName}-db`,
    });

    this.dbSecret = this.dbInstance.secret!;

    // Outputs
    new cdk.CfnOutput(this, 'DbEndpoint', {
      value: this.dbInstance.instanceEndpoint.hostname,
      description: 'RDS endpoint hostname',
    });

    new cdk.CfnOutput(this, 'DbSecretArn', {
      value: this.dbSecret.secretArn,
      description: 'Secret ARN for DB credentials',
    });
  }
}
