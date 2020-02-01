
#Internship Project v1.0

#Objective: Launch, Stop, and Terminate Instances using AWS, GCP, and Azure

#----------------------------------------------------------------------------------------

#CONFIGURATION:

mySpecs = [
    
    #Specifications for creating AWS instance
    
    {
        
        "KEY_NAME" : "myKey",
        
        "IMAGE_ID" : "ami-0f2176987ee50226e",
        "INSTANCE_TYPE" : "t2.micro",
        
        "MIN_COUNT" : 1,
        "MAX_COUNT" : 1,
        
        "DEVICE_NAME" : "/dev/xvda",
        
        "VOLUME_TYPE" : "gp2",
        "VOLUME_SIZE" : 8, #in GiB
        
        "BLOCK_DELETE_ON_TERMINATION" : True,
        "ENCRYPTED" : True,
        
        "ASSOCIATE_PUBLIC_IP_ADDRESS" : True,
        "NETWORK_DELETE_ON_TERMINATION" : True,
        
        "DEVICE_INDEX" : 0
        
    },
    
    #Specifications for creating GCP instance
    
    {
        
        "PROJECT" : "graphic-boulder-247700",
        "ZONE" : "us-west1-a",
        
        "INSTANCE_NAME" : "instance-1",
        
        "MACHINE_TYPE" : "zones/us-west1-a/machineTypes/f1-micro",
        
        "DISK_SOURCE_IMAGE" : "projects/debian-cloud/global/images/family/debian-9",
        "DISK_SIZE" : 10, #in GiB
        
        "NETWORK" : "global/networks/default",
        "NETWORK_TYPE" : "ONE_TO_ONE_NAT"
        
    },
    
    #Specifications for creating Azure instance
    
    {
        
        #MUST CONFIGURE DIFFERENTLY EVERY TIME
        
        "VM_NAME" : "instance-1",
        
        "IP_ADDRESS_NAME" : "instance-1-ip",
        
        "NIC_NAME" : "instance-1-nic",
        
        #-------------------------------------
        
        "PUBLIC_KEY_NAME" : "instance-1-key",
        
        "GROUP_NAME" : "TestResourceGroup",
        
        "LOCATION" : "westus",
        
        "VNET_NAME" : "TestResourceGroup-vnet",
        "SUBNET_NAME" : "default",
        
        "NIC_IP_CONFIG" : "ipconfig",
        
        "VM_SIZE" : "Standard_DS1_v2",
        
        "IMAGE_PUBLISHER" : "Canonical",
        
        "IMAGE_OFFER" : "UbuntuServer",
        
        "IMAGE_SKU" : "16.04.0-LTS",
        
        "IMAGE_VERSION" : "latest"
        
    }
    
]

#----------------------------------------------------------------------------------------

import os
from Crypto.PublicKey import RSA
import sys

#SDK for AWS:

import boto3

#SDK for GCP:

from googleapiclient import discovery

#SDKs For Azure:

from azure.common.client_factory import get_client_from_cli_profile
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient

#----------------------------------------------------------------------------------------

class Cloud(object):
    
    def __init__(self, platform = ""):
        
        self.platform = platform
        

    def create_key(self, key_name):
        
        if self.platform == "aws":
            
            client = boto3.client("ec2")
            
            keypair = client.create_key_pair(KeyName = key_name)
            
            return keypair["KeyMaterial"]
            
        if self.platform == "azu":
                
            key = RSA.generate(2048)
                
            public_file = open(".ssh/authorized_keys/{}.pem".format(key_name), "wb+")

            pubkey = key.publickey()
            key_data = pubkey.exportKey("OpenSSH")
            public_file.write(key_data)
            public_file.close()
                
            return key.exportKey("PEM").decode("UTF-8")
                
            
        

    def launch_instance(self, specifications = []):
        
        if self.platform == "aws":
            
            ec2 = boto3.resource("ec2")
            client = boto3.client("ec2")
            
            response = ec2.create_instances(
                
                ImageId = specifications["IMAGE_ID"],
                InstanceType = specifications["INSTANCE_TYPE"],
                
                MinCount = specifications["MIN_COUNT"],
                MaxCount = specifications["MAX_COUNT"],
                
                KeyName = specifications["KEY_NAME"],
                
                BlockDeviceMappings = [
                    
                    {
                        
                        "DeviceName" : specifications["DEVICE_NAME"],
                        
                        "Ebs" : {
                            
                            "VolumeType" : specifications["VOLUME_TYPE"],
                            "VolumeSize" : specifications["VOLUME_SIZE"],
                            
                            "DeleteOnTermination" : specifications["BLOCK_DELETE_ON_TERMINATION"],
                            "Encrypted" : specifications["ENCRYPTED"]
                            
                        }
                        
                    }
                    
                ],
                
                NetworkInterfaces = [
                    
                    {
                        
                        "AssociatePublicIpAddress" : specifications["ASSOCIATE_PUBLIC_IP_ADDRESS"],
                        "DeleteOnTermination" : specifications["NETWORK_DELETE_ON_TERMINATION"],
                        
                        "DeviceIndex" : specifications["DEVICE_INDEX"]
                        
                    }
                    
                ]
                
            )
            
            instance = client.describe_instances(
                
                InstanceIds = [
                    
                    response[0].id
                    
                ]
                
            )
            
            return instance
            
        
        if self.platform == "gcp":
            
            compute = discovery.build("compute","v1")
            
            config = {
                
                "name" : specifications["INSTANCE_NAME"],
                
                "machineType" : specifications["MACHINE_TYPE"],
                
                "disks" : [
                    {
                        'boot': True,
                        'autoDelete': True,
                        'initializeParams': {
                            'sourceImage': specifications["DISK_SOURCE_IMAGE"],
                            'diskSizeGb' : specifications["DISK_SIZE"]
                        }
                    }
                ],
                
                "networkInterfaces": [
                    {
                        "network" : specifications["NETWORK"],
                        "accessConfigs" : [
                            {"type" : specifications["NETWORK_TYPE"]}
                        ]
                    }
                ]
            
            }
            
            return compute.instances().insert(project=specifications["PROJECT"],zone=specifications["ZONE"],body=config).execute()
         
        
        if self.platform == "azu":
            
            compute_client = get_client_from_cli_profile(ComputeManagementClient)
            network_client = get_client_from_cli_profile(NetworkManagementClient)
            
            ip = network_client.public_ip_addresses.create_or_update(specifications["GROUP_NAME"], specifications["IP_ADDRESS_NAME"], {
                
                "location" : specifications["LOCATION"],
                "public_ip_allocation_method" : "Dynamic"
                
            })
            
            nic_create = network_client.network_interfaces.create_or_update(specifications["GROUP_NAME"], specifications["NIC_NAME"], {
                
                "location" : specifications["LOCATION"],
                "ip_configurations" : [{
                    
                    "name" : specifications["NIC_IP_CONFIG"],
                    
                    "public_ip_address" : network_client.public_ip_addresses.get(
                        
                        specifications["GROUP_NAME"],
                        specifications["IP_ADDRESS_NAME"]
                        
                    ),
                    
                    "subnet" : {
                        
                        "id" : network_client.subnets.get(
                        
                            specifications["GROUP_NAME"],
                            specifications["VNET_NAME"],
                            specifications["SUBNET_NAME"]
                        
                        ).id
                        
                    }
                    
                }]
                
            })
            
            vm_parameters = {
                
                "location": specifications["LOCATION"],
                
                "os_profile": {
                    
                    "computer_name": specifications["VM_NAME"],
                    
                    "admin_username": "userlogin",
                    
                    "linux_configuration": {
                        
                        "disable_password_authentication": True,
                        
                        "ssh": {
                            
                            "public_keys": [{
                                
                                "path": "/home/userlogin/.ssh/authorized_keys",
                                "key_data": open(".ssh/authorized_keys/{}.pem".format(specifications["PUBLIC_KEY_NAME"]),"r").read()
                                
                            }]
                            
                        }
                        
                    }
                    
                },
                
                "hardware_profile": {
                    
                    "vm_size": specifications["VM_SIZE"]
                    
                },
                
                "storage_profile": {
                    
                    "image_reference": {
                        
                        "publisher": specifications["IMAGE_PUBLISHER"],
                        "offer": specifications["IMAGE_OFFER"],
                        "sku": specifications["IMAGE_SKU"],
                        "version": specifications["IMAGE_VERSION"]
                        
                    },
                    
                },
                
                "network_profile": {
                
                    "network_interfaces": [{
                        
                        "id": network_client.network_interfaces.get(specifications["GROUP_NAME"], specifications["NIC_NAME"]).id,
                        
                    }]
                    
                },
                
            }
            
            build = compute_client.virtual_machines.create_or_update(specifications["GROUP_NAME"], specifications["VM_NAME"], vm_parameters)
            
            return build.result()
            

    def stop_instance(self, instanceId, group = "", area = ""):
        
        if self.platform == "aws":
            
            client = boto3.client("ec2")
            
            client.stop_instances(
                
                InstanceIds = [
                    
                    instanceId
                    
                ],
                
            )
          
        
        if self.platform == "gcp":
            
            compute = discovery.build("compute","v1")
            
            compute.instances().stop(
                
                project = group,
                
                zone = area,
                
                instance = instanceId
                
            ).execute()
            
        
        if self.platform == "azu":
            
            compute_client = get_client_from_cli_profile(ComputeManagementClient)
            
            compute_client.virtual_machines.power_off(group, instanceId)
            
        
    
    def start_instance(self, instanceId, group = "", area = ""):
        
        if self.platform == "aws":
            
            client = boto3.client("ec2")
            
            client.start_instances(
                
                InstanceIds = [
                    
                    instanceId
                    
                ]
                
            )
            
        
        if self.platform == "gcp":
            
            compute = discovery.build("compute","v1")
            
            compute.instances().start(
                
                project = group,
                
                zone = area,
                
                instance = instanceId
                
            ).execute()
            
        
        if self.platform == "azu":
            
            compute_client = get_client_from_cli_profile(ComputeManagementClient)
            
            compute_client.virtual_machines.start(group, instanceId)
            
        

    def terminate_instance(self, instanceId = "", group = "", area = "", nic_name = "" , ip_name = "", key_name = ""):
        
        if self.platform == "aws":
            
            client = boto3.client("ec2")
            
            client.terminate_instances(
                
                InstanceIds = [
                    
                    instanceId
                    
                ],
                
            )

            if key_name != "":

                client.delete_key_pair(KeyName=key_name)
            
        
        if self.platform == "gcp":
            
            compute = discovery.build("compute","v1")
            
            compute.instances().delete(
                
                project = group,
                
                zone = area,
                
                instance = instanceId
                
            ).execute()
            
        
        if self.platform == "azu":
            
            compute_client = get_client_from_cli_profile(ComputeManagementClient)
            network_client = get_client_from_cli_profile(NetworkManagementClient)
            
            print("\nDeleting VM...")
            compute_client.virtual_machines.delete(group, instanceId).wait()
            
            print("Deleting NIC...")
            network_client.network_interfaces.delete(group, nic_name).wait()
            
            print("Deleting Public IP...")
            network_client.public_ip_addresses.delete(group, ip_name).wait()
            
            if key_name != "":
            
                os.remove(".ssh/authorized_keys/{}.pem".format(key_name))
            
        

#-----------------------------------------------#
#              ______   __  __    ____          #
#             / ____/  / / / /   /  _/          #
#            / / __   / / / /    / /            #
#           / /_/ /  / /_/ /   _/ /             #
#           \____/   \____/   /___/             #
#                                               #
#-----------------------------------------------#

dictionary_one = {"1" : "aws", "2" : "gcp", "3" : "azu"}
dictionary_two = {"aws" : "Amazon Web Services", "gcp" : "Google Cloud Platform", "azu" : "Microsoft Azure"}
dictionary_three = {"1" : "launch", "2" : "stop", "3" : "start", "4" : "terminate", "5" : "back"}
dictionary_four = {"1" : "list", "2" : "change", "3" : "back"}
    
print("\033c", end = "")

while True:
    
    print("\nSelect a Cloud Service Provider:\n")
    print("\t1: Amazon Web Services\n")
    print("\t2: Google Cloud Platform\n")
    print("\t3: Microsoft Azure\n")
    print("\t4: Specifications\n")
    print("\t5: Exit\n")
    
    provider = input(" :")
    
    try:
        
        if provider == "4":
            
            print("\033c", end = "Specifications\n")
            
            while True:
                
                print("\nChoose an Option:\n")
                print("\t1: List Specifications\n")
                print("\t2: Change Specifications\n")
                print("\t3: Back\n")
                
                selection = input(" :")
                
                if dictionary_four[selection] == "list":
                    
                    for i in range(len(mySpecs)):
                        
                        print("\033c", end = dictionary_two[dictionary_one[str(i+1)]] + "\n\n\n")
                        
                        for keys, values in mySpecs[i].items():
                            
                            print(str(keys) + " : " + str(values))
                            
                        
                        input("\n\nPress 'Enter' to Continue...")
                        
                        print("\033c", end = "")
                        
                    
                    print("\033c", end = "Specifications\n")
                    
                
                elif dictionary_four[selection] == "change":
                    
                    print("\033c", end = "Specifications\n")
                    
                    print("\nChoose a Cloud Provider:\n")
                    print("\t1: Amazon Web Services\n")
                    print("\t2: Google Cloud Platform\n")
                    print("\t3: Microsoft Azure\n")
                    print("\t4: Back\n")
                    
                    choice = input(" :")
                    
                    print("\033c", end = dictionary_two[dictionary_one[choice]] + "\n\n\n")
                    
                    if dictionary_one[choice] == "aws":
                        
                        while True:
                        
                            for keys, values in mySpecs[0].items():
                                
                                print(str(keys) + " : " + str(values))
                                
                            
                            change = input("\n\nChange a value? (y/n): ")
                            
                            if change == "y":
                                
                                name_of_key = input("\nName of Key: ")
                                name_of_value = input("New Value: ")
                                
                                mySpecs[0][name_of_key] = name_of_value
                                
                                print("\033c", end = dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                            elif change == "n":
                                
                                print("\033c", end = "Specifications\n")
                                
                                break
                                
                            
                            else:
                                
                                print("\033c", end = "Please type valid input\n\n" + dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                        
                    
                    elif dictionary_one[choice] == "gcp":
                        
                        while True:
                        
                            for keys, values in mySpecs[1].items():
                                
                                print(str(keys) + " : " + str(values))
                                
                            
                            change = input("\n\nChange a value? (y/n): ")
                            
                            if change == "y":
                                
                                name_of_key = input("\nName of Key: ")
                                name_of_value = input("New Value: ")
                                
                                mySpecs[1][name_of_key] = name_of_value
                                
                                print("\033c", end = dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                            elif change == "n":
                                
                                print("\033c", end = "Specifications\n")
                                
                                break
                                
                            
                            else:
                                
                                print("\033c", end = "Please type valid input\n\n" + dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                        
                    
                    elif dictionary_one[choice] == "azu":
                        
                        while True:
                        
                            for keys, values in mySpecs[2].items():
                                
                                print(str(keys) + " : " + str(values))
                                
                            
                            change = input("\n\nChange a value? (y/n): ")
                            
                            if change == "y":
                                
                                name_of_key = input("\nName of Key: ")
                                name_of_value = input("New Value: ")
                                
                                mySpecs[2][name_of_key] = name_of_value
                                
                                print("\033c", end = dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                            elif change == "n":
                                
                                print("\033c", end = "Specifications\n")
                                
                                break
                                
                            
                            else:
                                
                                print("\033c", end = "Please type valid input\n\n" + dictionary_two[dictionary_one[choice]] + "\n\n\n")
                                
                            
                        
                    
                    elif dictionary_one[choice] == "back":
                        
                        pass
                        
                    
                
                elif dictionary_four[selection] == "back":
                    
                    print("\033c", end = "")
                    
                    break
                    
                
            
        
        elif provider == "5":
            
            print("\033c", end = "")
            
            break
            
        
        else:
            
            cloud = Cloud(dictionary_one[provider])
            
            print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
            
            while True:
                
                print("\nChoose an Option:\n")
                print("\t1: Launch Instance\n")
                print("\t2: Stop Instance\n")
                print("\t3: Start Instance\n")
                print("\t4: Terminate Instance\n")
                print("\t5: Back\n")
                
                selection = input(" :")
                
                if dictionary_three[selection] == "launch":
                    
                    print("\033c", end = "")
                    
                    while True:
                        
                        new_key = input("\nCreate New Key? (y/n): ")
                        
                        if new_key == "y":
                            
                            response = cloud.create_key(input("\nEnter Key Name: "))
                            
                            print("\033c", end = "")
                            
                            print(response)
                            
                            input("\n\nPress 'Enter' to Continue...")
                            
                            print("\033c", end = "")
                            
                            cloud.launch_instance(mySpecs[int(provider)-1])
                            
                            print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                            
                            break
                            
                        
                        elif new_key == "n":
                            
                            if provider == 3:
                                
                                try:
                                    
                                    file = open(".ssh/authorized_keys/{}.pem".format(specifications["PUBLIC_KEY_NAME"]),"r")
                                    file.close()
                                    
                                    cloud.launch_instance(mySpecs[int(provider)-1])
                                    
                                    print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                                    
                                    break
                                    
                                
                                except FileNotFoundError:
                                    
                                    print("\033c", end = "Error: no public key found... Closing...")
                                    
                                    sys.exit(0)
                                    
                                
                            
                            else:
                                
                                cloud.launch_instance(mySpecs[int(provider)-1])
                                
                                print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                                
                                break
                                
                            
                        
                        else:
                            
                            print("\033c", end = "Try again...")
                            
                        
                    
                
                elif dictionary_three[selection] == "stop":
                    
                    print("\033c", end = "")
                    
                    instance = input("\nEnter Instance ID: ")
                    project = input("\nEnter Group/Project (Press 'Enter' if N/A): ")
                    zone = input("\nEnter Zone (Press 'Enter' if N/A): ")
                    
                    cloud.stop_instance(instanceId = instance, group = project, area = zone)
                    
                    print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                   
                
                elif dictionary_three[selection] == "start":
                    
                    print("\033c", end = "")
                    
                    instance = input("\nEnter Instance ID: ")
                    project = input("\nEnter Group/Project (Press 'Enter' if N/A): ")
                    zone = input("\nEnter Zone (Press 'Enter' if N/A): ")
                    
                    cloud.start_instance(instanceId = instance, group = project, area = zone)
                    
                    print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                    
                
                elif dictionary_three[selection] == "terminate":
                    
                    print("\033c", end = "")
                    
                    instance = input("\nEnter Instance ID: ")
                    project = input("\nEnter Group/Project (Press 'Enter' if N/A): ")
                    zone = input("\nEnter Zone (Press 'Enter' if N/A): ")
                    nic = input("\nEnter NIC Name (Press 'Enter' if N/A): ")
                    ip = input("\nEnter IP Name (Press 'Enter' if N/A): ")
                    key = input("\nEnter Key Name (Press 'Enter' if N/A): ")
                    
                    cloud.terminate_instance(instanceId=instance, group=project, area=zone, nic_name=nic, ip_name=ip, key_name=key)
                    
                    print("\033c", end = dictionary_two[dictionary_one[provider]] + "\n")
                   
                
                elif dictionary_three[selection] == "back":
                    
                    print("\033c", end = "")
                    
                    break
                    
                
                
            
        
    
    except KeyError:
        
        print("\033c", end = "")
        
        print("Error: Invalid Option")
        
