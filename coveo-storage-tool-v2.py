# Import modules
import boto3
import sys
from datetime import datetime, timedelta
import argparse
import math
import subprocess

# Print welcome message

print("\n/////////////////////////////////////////////////")
print(" Welcome to the Coveo command line storage tool! ")
print("/////////////////////////////////////////////////\n")

# Configure resource and client
resource = boto3.resource('s3')
client = boto3.client('s3')

# Configure the default region using region associated with the account
default_region = client.meta.region_name

# Create the parser and define the parser variables

parser = argparse.ArgumentParser(description="Command line tool for fetching information on Amazon S3 buckets")
parser.add_argument('-prefix', action='store', help='The prefix for the bucket')
parser.add_argument('-storage_type', action='store', help='The storage type of the objects in the bucket')
parser.add_argument('-region', action='store', help='The region for the bucket. If none specified, the default region of the Amazon account will be used')
parser.add_argument('-storage_size', action='store', help='The size of the storage. Options are Bytes, Kilobytes, Megabytes, Gigabytes, Terrabytes')
args = parser.parse_args()
prefix = args.prefix
storage_type = args.storage_type
region = args.region
storage_size = args.storage_size

# Use default region of the Amazon account if no other region is specified

if region is None:
    region = default_region
else:
    pass

# Use a default storage size if no storage size is specified

if storage_size is None:
    storage_size = 'Bytes'
else:
    pass

# Use a default storage type if no storage type is specified

if storage_type is None:
    storage_type = 'StandardStorage'
else:
    pass

print("Parameters")
print("-----------")
print("Prefix:",prefix)
print("Region:",region)
print("Storage size:",storage_size)
print("Storage type:",storage_type)
print("(Hint: Specify parameters using arguments -prefix, -region, -storage_type and -storage_size. If nothing is specified, default will be used)")

# Create CloudWatch client and configure region
cloudwatch = boto3.client('cloudwatch', region_name=region)

total_size = [] # Define empty list

def convert_size(size,storage_size): # Conversions taken from official Google calculator
    B = float(size)
    KB = size / (1000)
    MB = KB / (1000)
    GB = MB / (1000)
    TB = GB / (1000)

    if (storage_size == 'Bytes'):
        return(B)
    if (storage_size == 'Kilobytes'):
        return(KB)
    if (storage_size == 'Megabytes'):
        return(MB)
    if (storage_size == 'Gigabytes'):
        return(GB)
    if (storage_size == 'Terrabytes'):
        return(TB)

def calculate_cost(gb_size): # Prices taken from S3 standard account storage prices https://aws.amazon.com/s3/pricing/
    price_50TB = 0.023 * 51200
    price_450TB = 0.022 * 460800
    if gb_size < 51200:
        price_t1 = 0.023 * gb_size
        price_t1_rounded = round(price_t1,2)
        return price_t1_rounded
    if gb_size > 51200 and gb_size < 460800:
        price_T2 = (gb_size - 51200) * 0.022
        price_t2 = price_50TB + price_T2
        price_t2_rounded = round(price_t2,2)
        return price_t2_rounded
    if gb_size > 460800:
        price_T3 = (gb_size - 51200 - 460800) * 0.021
        price_t3 = price_T3 + price_50TB + price_450TB
        price_t3_rounded = round(price_t3,2)
        return price_t3_rounded

def latest_file(name):
    paginator = client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=name)
    last_modified = lambda obj: int(obj['LastModified'].strftime('%s'))
    for page in pages:
        if "Contents" in page:
            last_added = [obj['LastModified'] for obj in sorted(page["Contents"], key=last_modified)][-1]
            time_last_added = last_added.strftime('%Y-%m-%d %H:%M:%S')
            return time_last_added


def get_bucket():
    for bucket in resource.buckets.all(): # Loop through all buckets
        name = bucket.name # Set bucket name variable
        creation_date = bucket.creation_date.strftime('%Y-%m-%d %H:%M:%S') # Set creation date variable

        # Pass bucket if doesn't match prefix
        if prefix is None:
            pass
        elif name.startswith(prefix):
            pass
        else:
            continue

        response_size = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='BucketSizeBytes',
            Dimensions=[
                {
                    'Name' : 'BucketName',
                    'Value' : name
                },
            {
                    'Name': 'StorageType',
                    'Value': storage_type
                }
            ],
            StartTime=datetime.utcnow() - timedelta(days=2),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=[
                'Average'
            ]
        )

        output = (response_size['Datapoints'])

        if len(output) != 0:
                output_string = str(output)
                output_list = output_string.split()
                size_comma = output_list[-3]
                size_bytes = size_comma[:-1]
                size = convert_size(float(size_bytes),storage_size)
                total_size.append(size)
        else:
            continue


        response_file_number = cloudwatch.get_metric_statistics(
            Namespace='AWS/S3',
            MetricName='NumberOfObjects',
            Dimensions=[
                {
                    'Name' : 'BucketName',
                    'Value' : name
                },
            {
                    'Name': 'StorageType',
                    'Value': 'AllStorageTypes' # Only valid for AllStorageTypes dimension https://docs.aws.amazon.com/AmazonS3/latest/userguide/metrics-dimensions.html
                }
            ],
            StartTime=datetime.utcnow() - timedelta(days=2),
            EndTime=datetime.utcnow(),
            Period=300,
            Statistics=[
                'Average'
            ]
        )

        output = (response_file_number['Datapoints'])

        if len(output) != 0:
                output_string = str(output)
                output_list = output_string.split()
                file_count_comma = output_list[-3]
                file_count = file_count_comma[:-1]
        else:
            pass

        bucket_gb = convert_size(float(size), 'Gigabytes')
        bucket_cost = calculate_cost(bucket_gb)

        # Print all the variables

        print("\n----------------------------------------------------------------------------------------------------\n")
        print("Bucket name:", name)
        print("Creation date:", creation_date)
        print("Last modified date:", latest_file(name))
        print("Bucket size: {} {}".format(size, storage_size))
        print("File count: {}".format(file_count))
        print("Bucket cost: ${} USD".format(bucket_cost))


    total_size_sum = 0
    for i in total_size:
        total_size_sum += float(i)

    # Print out the total calculations
    print("\n========================================================================================================\n")
    print("Total size:",total_size_sum,storage_size)
    gb_size = convert_size(total_size_sum, 'Gigabytes')
    total_price = calculate_cost(gb_size)
    print("Total cost: ${} USD".format(total_price))

get_bucket()

print("\nExiting script... Goodbye!")
