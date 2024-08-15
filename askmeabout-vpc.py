import boto3

def get_regions():
    ec2_client = boto3.client('ec2')
    return [region['RegionName'] for region in ec2_client.describe_regions()['Regions']]

def get_vpcs(ec2):
    return ec2.describe_vpcs()['Vpcs']

def get_subnets(ec2, vpc_id):
    return ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['Subnets']

def get_route_tables(ec2, vpc_id):
    return ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['RouteTables']

def get_vpc_endpoints(ec2, vpc_id):
    return ec2.describe_vpc_endpoints(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])['VpcEndpoints']

def scan_vpcs():
    regions = get_regions()

    for region in regions:
        print(f"Scanning region: {region}")
        ec2 = boto3.client('ec2', region_name=region)
        vpcs = get_vpcs(ec2)

        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            cidr_block = vpc['CidrBlock']
            is_default = vpc['IsDefault']
            print(f"VPC ID: {vpc_id}")
            print(f"IPv4 CIDR: {cidr_block}")
            print(f"Is Default VPC: {'Yes' if is_default else 'No'}")

            subnets = get_subnets(ec2, vpc_id)
            for subnet in subnets:
                subnet_id = subnet['SubnetId']
                az = subnet['AvailabilityZone']
                print(f"  Subnet ID: {subnet_id}, Availability Zone: {az}")

                route_tables = ec2.describe_route_tables(
                    Filters=[{'Name': 'association.subnet-id', 'Values': [subnet_id]}]
                )['RouteTables']

                if route_tables:
                    for rt in route_tables:
                        print(f"    Route Table ID: {rt['RouteTableId']}")
                        for route in rt['Routes']:
                            destination_cidr_block = route.get('DestinationCidrBlock', 'N/A')
                            target = 'Local'
                            if 'GatewayId' in route:
                                target = f"Internet Gateway ({route['GatewayId']})" if route['GatewayId'].startswith('igw-') else route['GatewayId']
                            elif 'NatGatewayId' in route:
                                target = f"NAT Gateway ({route['NatGatewayId']})"
                            print(f"      Destination: {destination_cidr_block}, Target: {target}")
                else:
                    print(f"    No Route Table associated with Subnet ID: {subnet_id}")

            route_tables = get_route_tables(ec2, vpc_id)
            for rt in route_tables:
                if not rt.get('Associations'):
                    print(f"  Route Table ID: {rt['RouteTableId']} has no subnet associations")

            vpc_endpoints = get_vpc_endpoints(ec2, vpc_id)
            s3_endpoint = any(vpce['ServiceName'].endswith('s3') for vpce in vpc_endpoints)
            dynamodb_endpoint = any(vpce['ServiceName'].endswith('dynamodb') for vpce in vpc_endpoints)

            print(f"  VPC Endpoint for S3: {'Yes' if s3_endpoint else 'No'}")
            print(f"  VPC Endpoint for DynamoDB: {'Yes' if dynamodb_endpoint else 'No'}")
            print("-" * 60)

if __name__ == "__main__":
    scan_vpcs()