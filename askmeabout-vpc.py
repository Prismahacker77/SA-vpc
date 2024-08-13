import boto3

def scan_vpcs():
    ec2_client = boto3.client('ec2')
    regions = [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

    for region in regions:
        print(f"Scanning region: {region}")
        ec2 = boto3.client('ec2', region_name=region)
        vpcs = ec2.describe_vpcs()['Vpcs']

        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr_block = vpc['CidrBlock']
            is_default = vpc['IsDefault']
            print(f"VPC ID: {vpc_id}")
            print(f"IPv4 CIDR: {cidr_block}")
            print(f"Is Default VPC: {'Yes' if is_default else 'No'}")

            # Get Subnets and their Availability Zones
            subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']
            for subnet in subnets:
                subnet_id = subnet['SubnetId']
                az = subnet['AvailabilityZone']
                print(f"  Subnet ID: {subnet_id}, Availability Zone: {az}")

                # Get Route Tables associated with each Subnet
                route_tables = ec2.describe_route_tables(
                    Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
                )['RouteTables']

                if route_tables:
                    for rt in route_tables:
                        print(f"    Route Table ID: {rt['RouteTableId']}")
                        for route in rt['Routes']:
                            gateway_id = route.get('GatewayId', 'N/A')
                            nat_gateway_id = route.get('NatGatewayId', 'N/A')
                            destination_cidr_block = route.get('DestinationCidrBlock', 'N/A')
                            target = 'N/A'
                            if gateway_id.startswith('igw-'):
                                target = f"Internet Gateway ({gateway_id})"
                            elif nat_gateway_id.startswith('nat-'):
                                target = f"NAT Gateway ({nat_gateway_id})"
                            else:
                                target = gateway_id or nat_gateway_id or 'Local'

                            print(f"      Destination: {destination_cidr_block}, Target: {target}")
                else:
                    print(f"    No Route Table associated with Subnet ID: {subnet_id}")

            # Check for route tables with no subnet associations
            route_tables = ec2.describe_route_tables(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )['RouteTables']

            for rt in route_tables:
                if not rt['Associations']:
                    print(f"  Route Table ID: {rt['RouteTableId']} has no subnet associations")

            # Check for VPC Endpoints
            vpc_endpoints = ec2.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['VpcEndpoints']
            s3_endpoint = any(vpce['ServiceName'].endswith('s3') for vpce in vpc_endpoints)
            dynamodb_endpoint = any(vpce['ServiceName'].endswith('dynamodb') for vpce in vpc_endpoints)

            print(f"  VPC Endpoint for S3: {'Yes' if s3_endpoint else 'No'}")
            print(f"  VPC Endpoint for DynamoDB: {'Yes' if dynamodb_endpoint else 'No'}")
            print("-" * 60)

if __name__ == "__main__":
    scan_vpcs()