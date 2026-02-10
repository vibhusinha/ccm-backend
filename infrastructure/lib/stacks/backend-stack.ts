import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as route53 from 'aws-cdk-lib/aws-route53';
import { Construct } from 'constructs';

export interface BackendStackProps extends cdk.StackProps {
  envName: string;
  vpc: ec2.Vpc;
  ec2SecurityGroup: ec2.SecurityGroup;
  backendDomainName: string;
}

export class BackendStack extends cdk.Stack {
  public readonly instance: ec2.Instance;
  public readonly elasticIp: ec2.CfnEIP;

  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    // Single ECR repository for all microservice images
    // Images are tagged per service: auth-latest, clubs-latest, auth-<sha>, etc.
    const repository = new ecr.Repository(this, 'EcrRepo', {
      repositoryName: `ccm-backend-${props.envName}`,
      removalPolicy: props.envName === 'production'
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
      emptyOnDelete: props.envName !== 'production',
      lifecycleRules: [
        {
          maxImageCount: 60, // ~10 per service x 6 services
          description: 'Keep last 60 images',
        },
      ],
    });

    // IAM role for EC2 instance
    const instanceRole = new iam.Role(this, 'InstanceRole', {
      roleName: `ccm-${props.envName}-backend-role`,
      assumedBy: new iam.ServicePrincipal('ec2.amazonaws.com'),
      managedPolicies: [
        // SSM Session Manager access (no SSH needed)
        iam.ManagedPolicy.fromAwsManagedPolicyName('AmazonSSMManagedInstanceCore'),
      ],
    });

    // ECR pull permissions
    repository.grantPull(instanceRole);

    // Allow reading Secrets Manager (for DB credentials)
    instanceRole.addToPolicy(new iam.PolicyStatement({
      actions: [
        'secretsmanager:GetSecretValue',
        'secretsmanager:DescribeSecret',
      ],
      resources: [
        `arn:aws:secretsmanager:${this.region}:${this.account}:secret:ccm-${props.envName}-*`,
      ],
    }));

    // Amazon Linux 2023 ARM64 AMI
    const machineImage = ec2.MachineImage.latestAmazonLinux2023({
      cpuType: ec2.AmazonLinuxCpuType.ARM_64,
    });

    // User data script
    const userData = ec2.UserData.forLinux();
    userData.addCommands(
      '#!/bin/bash',
      'set -euxo pipefail',
      '',
      '# Install packages',
      'dnf update -y',
      'dnf install -y docker nginx certbot python3-certbot-nginx jq awscli',
      '',
      '# Enable and start services',
      'systemctl enable docker',
      'systemctl start docker',
      'systemctl enable nginx',
      'systemctl start nginx',
      '',
      '# Add ec2-user to docker group',
      'usermod -aG docker ec2-user',
      '',
      '# Create application directory',
      'mkdir -p /opt/ccm-backend',
      '',
      '# Write initial Nginx config (placeholder — full config deployed via CI/CD)',
      '# The detailed routing config (nginx/api.conf from ccm-backend repo) is',
      '# copied to /etc/nginx/conf.d/api.conf during each deployment.',
      `cat > /etc/nginx/conf.d/api.conf << 'NGINXEOF'`,
      'upstream auth_service { server 127.0.0.1:8001; }',
      'upstream clubs_service { server 127.0.0.1:8002; }',
      'upstream matches_service { server 127.0.0.1:8003; }',
      'upstream scoring_service { server 127.0.0.1:8004; }',
      'upstream communication_service { server 127.0.0.1:8005; }',
      'upstream commerce_service { server 127.0.0.1:8006; }',
      '',
      'server {',
      '    listen 80;',
      `    server_name ${props.backendDomainName};`,
      '',
      '    proxy_set_header Host $host;',
      '    proxy_set_header X-Real-IP $remote_addr;',
      '    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;',
      '    proxy_set_header X-Forwarded-Proto $scheme;',
      '    proxy_read_timeout 60s;',
      '    proxy_connect_timeout 10s;',
      '',
      '    location /api/v1/health { proxy_pass http://auth_service; }',
      '',
      '    # Auth service (:8001)',
      '    location /api/v1/auth { proxy_pass http://auth_service; }',
      '    location /api/v1/registration { proxy_pass http://auth_service; }',
      '    location /api/v1/profiles { proxy_pass http://auth_service; }',
      '    location /api/v1/roles { proxy_pass http://auth_service; }',
      '    location /api/v1/permissions { proxy_pass http://auth_service; }',
      '    location /api/v1/user-permissions { proxy_pass http://auth_service; }',
      '    location /api/v1/platform { proxy_pass http://auth_service; }',
      '    location /api/v1/navigation { proxy_pass http://auth_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/registrations { proxy_pass http://auth_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/roles { proxy_pass http://auth_service; }',
      '',
      '    # Clubs service (:8002)',
      '    location ~ ^/api/v1/clubs/[^/]+/members { proxy_pass http://clubs_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/teams { proxy_pass http://clubs_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/seasons { proxy_pass http://clubs_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/players { proxy_pass http://clubs_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/key-people { proxy_pass http://clubs_service; }',
      '    location /api/v1/clubs { proxy_pass http://clubs_service; }',
      '',
      '    # Matches service (:8003)',
      '    location ~ ^/api/v1/clubs/[^/]+/matches$ { proxy_pass http://matches_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/availability { proxy_pass http://matches_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/fixture-types { proxy_pass http://matches_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/fixture-series { proxy_pass http://matches_service; }',
      '    location /api/v1/fixtures { proxy_pass http://matches_service; }',
      '    location /api/v1/fixture-types { proxy_pass http://matches_service; }',
      '',
      '    # Scoring service (:8004)',
      '    location ~ ^/api/v1/matches/ { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/matches-for-scoring { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/match-statistics { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/deadline-alerts { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/team-selection-config { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/player-selection { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/simulation-status { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/reset-selections { proxy_pass http://scoring_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/recommend { proxy_pass http://scoring_service; }',
      '    location /api/v1/innings { proxy_pass http://scoring_service; }',
      '    location /api/v1/players { proxy_pass http://scoring_service; }',
      '    location /api/v1/player-selection-overrides { proxy_pass http://scoring_service; }',
      '',
      '    # Communication service (:8005)',
      '    location ~ ^/api/v1/clubs/[^/]+/channels { proxy_pass http://communication_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/announcements { proxy_pass http://communication_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/faqs { proxy_pass http://communication_service; }',
      '    location /api/v1/channels { proxy_pass http://communication_service; }',
      '    location /api/v1/messages { proxy_pass http://communication_service; }',
      '    location /api/v1/polls { proxy_pass http://communication_service; }',
      '    location /api/v1/poll-options { proxy_pass http://communication_service; }',
      '    location /api/v1/users { proxy_pass http://communication_service; }',
      '    location /api/v1/notifications { proxy_pass http://communication_service; }',
      '    location /api/v1/reminders { proxy_pass http://communication_service; }',
      '    location /api/v1/push-tokens { proxy_pass http://communication_service; }',
      '',
      '    # Commerce service (:8006)',
      '    location ~ ^/api/v1/clubs/[^/]+/payments { proxy_pass http://commerce_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/fee-config { proxy_pass http://commerce_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/finance { proxy_pass http://commerce_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/player-payment { proxy_pass http://commerce_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/merchandise { proxy_pass http://commerce_service; }',
      '    location ~ ^/api/v1/clubs/[^/]+/media { proxy_pass http://commerce_service; }',
      '    location /api/v1/payments { proxy_pass http://commerce_service; }',
      '    location /api/v1/merchandise { proxy_pass http://commerce_service; }',
      '    location /api/v1/media { proxy_pass http://commerce_service; }',
      '',
      '    location /api/ { return 404; }',
      '}',
      'NGINXEOF',
      '',
      '# Remove default nginx server block if it conflicts',
      'rm -f /etc/nginx/conf.d/default.conf',
      '',
      '# Test and reload nginx',
      'nginx -t && systemctl reload nginx',
      '',
      '# Create deploy script',
      `cat > /opt/ccm-backend/deploy.sh << 'DEPLOYEOF'`,
      '#!/bin/bash',
      'set -euxo pipefail',
      '',
      `REGION="${this.region}"`,
      `ACCOUNT="${this.account}"`,
      `ENV="${props.envName}"`,
      '',
      '# Login to ECR',
      'aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT.dkr.ecr.$REGION.amazonaws.com',
      '',
      '# Service mapping: name -> port',
      'declare -A SERVICES=(',
      '  ["ccm-auth"]=8001',
      '  ["ccm-clubs"]=8002',
      '  ["ccm-matches"]=8003',
      '  ["ccm-scoring"]=8004',
      '  ["ccm-communication"]=8005',
      '  ["ccm-commerce"]=8006',
      ')',
      '',
      '# Pull and restart each service',
      'for SERVICE in "${!SERVICES[@]}"; do',
      '  PORT=${SERVICES[$SERVICE]}',
      '  IMAGE="$ACCOUNT.dkr.ecr.$REGION.amazonaws.com/ccm-backend-$ENV:${SERVICE#ccm-}-latest"',
      '',
      '  echo "Deploying $SERVICE on port $PORT..."',
      '  docker pull $IMAGE',
      '',
      '  # Stop existing container if running',
      '  docker stop $SERVICE 2>/dev/null || true',
      '  docker rm $SERVICE 2>/dev/null || true',
      '',
      '  # Start new container',
      '  docker run -d \\',
      '    --name $SERVICE \\',
      '    --restart unless-stopped \\',
      '    -p $PORT:8000 \\',
      '    --env-file /opt/ccm-backend/$SERVICE.env \\',
      '    $IMAGE',
      'done',
      '',
      'echo "Deployment complete!"',
      'DEPLOYEOF',
      '',
      'chmod +x /opt/ccm-backend/deploy.sh',
    );

    // EC2 instance
    this.instance = new ec2.Instance(this, 'BackendInstance', {
      instanceName: `ccm-${props.envName}-backend`,
      vpc: props.vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PUBLIC },
      instanceType: new ec2.InstanceType(
        props.envName === 'production' ? 't4g.small' : 't4g.micro'
      ),
      machineImage,
      securityGroup: props.ec2SecurityGroup,
      role: instanceRole,
      userData,
      blockDevices: [
        {
          deviceName: '/dev/xvda',
          volume: ec2.BlockDeviceVolume.ebs(20, {
            volumeType: ec2.EbsDeviceVolumeType.GP3,
            encrypted: true,
          }),
        },
      ],
    });

    // Elastic IP
    this.elasticIp = new ec2.CfnEIP(this, 'ElasticIp', {
      tags: [{ key: 'Name', value: `ccm-${props.envName}-backend-eip` }],
    });

    // Associate EIP with EC2 instance
    new ec2.CfnEIPAssociation(this, 'EipAssociation', {
      eip: this.elasticIp.ref,
      instanceId: this.instance.instanceId,
    });

    // Route 53 A record for API domain
    const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
      domainName: 'crickitup.com',
    });

    new route53.ARecord(this, 'ApiARecord', {
      zone: hostedZone,
      recordName: props.backendDomainName,
      target: route53.RecordTarget.fromIpAddresses(this.elasticIp.ref),
      ttl: cdk.Duration.minutes(5),
    });

    // Outputs
    new cdk.CfnOutput(this, 'InstanceId', {
      value: this.instance.instanceId,
      description: 'EC2 instance ID',
    });

    new cdk.CfnOutput(this, 'ElasticIpAddress', {
      value: this.elasticIp.ref,
      description: 'Elastic IP address',
    });

    new cdk.CfnOutput(this, 'ApiDomainName', {
      value: props.backendDomainName,
      description: 'API domain name',
    });

    new cdk.CfnOutput(this, 'EcrRepoUri', {
      value: repository.repositoryUri,
      description: 'ECR repository URI for all service images',
    });
  }
}
