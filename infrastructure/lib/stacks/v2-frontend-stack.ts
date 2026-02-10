import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';
import * as route53 from 'aws-cdk-lib/aws-route53';
import * as route53Targets from 'aws-cdk-lib/aws-route53-targets';
import { Construct } from 'constructs';

export interface V2FrontendStackProps extends cdk.StackProps {
  envName: string;
  s3BucketName: string;
  domainName?: string;
  certificateArn?: string;
  apiDomainName: string; // For CSP headers
}

export class V2FrontendStack extends cdk.Stack {
  public readonly distribution: cloudfront.Distribution;
  public readonly bucket: s3.Bucket;

  constructor(scope: Construct, id: string, props: V2FrontendStackProps) {
    super(scope, id, props);

    // S3 bucket for static web files (private -- accessed only via CloudFront)
    this.bucket = new s3.Bucket(this, 'WebBucket', {
      bucketName: props.s3BucketName,
      removalPolicy: props.envName === 'production'
        ? cdk.RemovalPolicy.RETAIN
        : cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: props.envName !== 'production',
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
    });

    // Response headers policy with security headers
    const responseHeadersPolicy = new cloudfront.ResponseHeadersPolicy(this, 'SecurityHeaders', {
      responseHeadersPolicyName: `ccm-v2-${props.envName}-security-headers`,
      securityHeadersBehavior: {
        strictTransportSecurity: {
          accessControlMaxAge: cdk.Duration.days(365),
          includeSubdomains: true,
          override: true,
        },
        contentTypeOptions: { override: true },
        frameOptions: {
          frameOption: cloudfront.HeadersFrameOption.DENY,
          override: true,
        },
        xssProtection: {
          protection: true,
          modeBlock: true,
          override: true,
        },
        referrerPolicy: {
          referrerPolicy: cloudfront.HeadersReferrerPolicy.STRICT_ORIGIN_WHEN_CROSS_ORIGIN,
          override: true,
        },
        contentSecurityPolicy: {
          contentSecurityPolicy: [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://js.stripe.com https://maps.googleapis.com",
            "style-src 'self' 'unsafe-inline'",
            `connect-src 'self' https://${props.apiDomainName} https://api.stripe.com https://maps.googleapis.com https://*.google.com https://*.gstatic.com`,
            "img-src 'self' data: blob: https://*.amazonaws.com https://*.googleapis.com https://*.gstatic.com https://*.google.com https://*.ggpht.com",
            "font-src 'self' data: https://fonts.gstatic.com",
            "frame-src https://js.stripe.com https://hooks.stripe.com https://maps.googleapis.com https://*.google.com",
            "media-src 'self' blob:",
          ].join('; '),
          override: true,
        },
      },
    });

    // Optional: ACM certificate for custom domain
    const certificate = props.certificateArn
      ? acm.Certificate.fromCertificateArn(this, 'Certificate', props.certificateArn)
      : undefined;

    // CloudFront distribution
    this.distribution = new cloudfront.Distribution(this, 'WebDistribution', {
      comment: `Cricket Club Manager V2 - ${props.envName}`,
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(this.bucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        responseHeadersPolicy,
        compress: true,
      },
      defaultRootObject: 'index.html',
      // SPA routing: return index.html for all 404/403 errors
      errorResponses: [
        {
          httpStatus: 404,
          responsePagePath: '/index.html',
          responseHttpStatus: 200,
          ttl: cdk.Duration.seconds(0),
        },
        {
          httpStatus: 403,
          responsePagePath: '/index.html',
          responseHttpStatus: 200,
          ttl: cdk.Duration.seconds(0),
        },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // US + Europe
      httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      ...(props.domainName && certificate ? {
        domainNames: [props.domainName],
        certificate,
      } : {}),
    });

    // Route 53 record pointing to CloudFront distribution
    if (props.domainName) {
      const hostedZone = route53.HostedZone.fromLookup(this, 'HostedZone', {
        domainName: 'crickitup.com',
      });

      new route53.ARecord(this, 'AliasRecord', {
        zone: hostedZone,
        recordName: props.domainName,
        target: route53.RecordTarget.fromAlias(
          new route53Targets.CloudFrontTarget(this.distribution)
        ),
      });
    }

    // Outputs
    new cdk.CfnOutput(this, 'BucketName', {
      value: this.bucket.bucketName,
      description: 'S3 bucket for V2 web files',
    });

    new cdk.CfnOutput(this, 'DistributionId', {
      value: this.distribution.distributionId,
      description: 'CloudFront distribution ID',
    });

    new cdk.CfnOutput(this, 'DistributionDomainName', {
      value: this.distribution.distributionDomainName,
      description: 'CloudFront domain name',
    });
  }
}
