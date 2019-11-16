import json
import boto3
import secrets
import string
import time

dynamodb = boto3.resource('dynamodb')
client = boto3.client('rekognition')

def lambda_handler(event, context):
    # TODO implement
    print(event)
    imgKey = event['faceId']
    name = event['name']
    phoneNumber = event['phoneNumber']
    faceId = getfaceId(imgKey, name)
    
    if (name != 'N/A' and phoneNumber != 'N/A'):
        response = storeUserInfo(faceId, name, '+1'+phoneNumber, imgKey)
        return {
            'message': json.dumps(response)
        }
    else:
        return {
            'message': json.dumps('Alright, we got it, thank you for your time!')
        }


def getfaceId(imgKey, name):
    
    response = client.index_faces(
    CollectionId='hw2collection',
    Image={
        'S3Object': {
            'Bucket': 'hw2face',
            'Name': imgKey
        }
    },
    ExternalImageId = name,
    DetectionAttributes = [
        'DEFAULT',
    ],
    MaxFaces = 1,
    QualityFilter = 'AUTO'
    )

    return response['FaceRecords'][0]['Face']['FaceId']
    
    
def storeUserInfo(faceId, name, phone_number, imgKey):
    # put in db2
    db2_table = dynamodb.Table('visitors')
    photo_info = {
        'objectKey': imgKey,
        'bucket': 'hw2face',
        'createdTimestamp': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }
    try:
        db2_table.put_item(
            Item = {
                'faceId': faceId,
                'name': name,
                'phoneNumber': phone_number,
                'photos': [photo_info]
                }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    return "Ok, We have stored the visitor's information, thank you!"
    
def generateOTP(faceId, phone_number):
    if (phone_number != 'N/A'):
        alphabet = string.ascii_letters + string.digits
        otp = ''.join(secrets.choice(alphabet) for i in range(9))
        expiryTimestamp = int(time.time() + 60*5)
        
        # put in db1
        db1_table = dynamodb.Table('otp')
        try:
            db1_table.put_item(
                Item = {
                    'faceId': faceId,
                    'otp': otp,
                    'TTL': {
                      'N': str(expiryTimestamp) 
                        }
                    }
            )
        except Exception as e:
            print('Exception: ', e)
            return False
        
        # Send to SNS
        msg = 'OTP: ' + otp
        client = boto3.client('sns')
        response = client.publish(
            PhoneNumber='+1' + phone_number,
            Message=msg
        )
    
    
    return True