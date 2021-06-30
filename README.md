# coveo-devops-challenge

Welcome to the Coveo command line storage analysis tool!

# Motivation

This code was developed for the Coveo DevOps challenge, with the goal of creating a command line tool which can provide various statistics on AWS S3 buckets including size, storage cost, creation date, and last modified date of the most recent file in the bucket. It was developed with a large system in mind, keeping speed, cost, and simplicity at the forefront.

# Description

This project is a command line tool which returns analytics of Amazon S3 buckets from a given account, printing the bucket name, bucket creation date, last modified date of the bucket, bucket size (with the option to display in Bytes, Megabytes, Kilobytes, Gigabytes, or Terrabytes), number of files in the given bucket, and the bucket cost in USD. The total size and total cost of all buckets is given at the end, and there is an option to filter the buckets based on bucket name or prefix, region that the bucket is in, and by storage type of files. 

The project contains two versions of the tool. coveo-storage-tool-v2.py provides the last modified date of the most recent file, whike coveo-storage-tool.py does not. The reason for this is that in order to retrieve the last modified date of the bucket, the code must loop over all objects in the bucket, making a request per each file in the process - which can be both **lengthly and costly**, as AWS does charge per request. The program to run can be chosen based on the use case - if the goal is to get the total cost of all S3 buckets across the whole system fast, coveo-storage-tool.py would be a good fit, however if you need some more in-depth analytics on fewer buckets, coveo-storage-tool-v2.py may be the better choice.

The metrics for the bucket (with the exception of the last modified date of the bucket) are retrieved using Amazon CloudWatch, a monitoring and observability service integrated with Amazon S3. The reason for this choice is that CloudWatch pulls the metadata associated with the bucket (as opposed to each separate file in the bucket), which only requires one request. This greatly increases the speed and decreases the cost of running the tool. 

# Getting started

This code assumes that you already have the AWS SDK for Python, Boto3, installed and configured on your terminal. If not, please refer to the Boto3 Quickstart guide here (sections "Install Boto3" and "Configuration"): https://boto3.amazonaws.com/v1/documentation/api/latest/guide/quickstart.html. 

All of the other modules are built-in with Python 3.8.5, on which this code has been tested. 

# Usage

This tool supports four different parameters - prefix/bucket name, storage type, region, and storage size display, which are specified as command line arguments. The arguments can be used individually, together, or none at all.

The AWS S3 storage type can be specified via the -storage_type argument. This will return a bucket size which only takes into account files of the specified type. The default is StandardStorage, if no other value is specified. Valid storage type filters are (taken from https://docs.aws.amazon.com/AmazonS3/latest/userguide/metrics-dimensions.html):

StandardStorage, IntelligentTieringFAStorage, IntelligentTieringIAStorage, IntelligentTieringAAStorage, IntelligentTieringDAAStorage, StandardIAStorage, StandardIASizeOverhead, StandardIAObjectOverhead, OneZoneIAStorage, OneZoneIASizeOverhead, ReducedRedundancyStorage, GlacierStorage, GlacierStagingStorage, GlacierObjectOverhead, GlacierS3ObjectOverhead, DeepArchiveStorage, DeepArchiveObjectOverhead, DeepArchiveS3ObjectOverhead, DeepArchiveStagingStorage 

*Example*: coveo-storage-tool.py -storage_type StandardStorage

The storage size display can be specified via the -storage_size argument. This will display the bucket size in the metric of your choice. The default size is Bytes. Valid storage size displays are:

Bytes, Kilobytes, Megabytes, Gigabytes, Terrabytes 

*Example*: coveo-storage-tool.py -storage_size Gigabytes 

The region can be specified via the -region argument. If using this argument, only the buckets within the specified region will be returned. If none is specified, the default region associated with the Amazon account will be used.

*Example*: coveo-storage-tool.py -region eu-central-1

If you would like to search for only a specific bucket, or all buckets starting with the same prefix, the -prefix argument can be used. 

*Example*: coveo-storage-tool.py -prefix my-bucket-prefix

# coveo-challenge
