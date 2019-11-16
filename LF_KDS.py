import datetime
import time
import boto3
import secrets
import string
import json
import base64
import cv2
from boto3.dynamodb.conditions import Key, Attr


dynamodb = boto3.resource('dynamodb')
db1_table = dynamodb.Table('otp')
db2_table = dynamodb.Table('visitors')

def ifknownface(event):
    for record in event['Records']:
        #Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record["kinesis"]["data"])
        data_json = payload.decode('utf8')
        data_json = json.loads(data_json)
        print(data_json)
        face_id = ""
        face_ok = False
        fnumber = data_json['InputInformation']['KinesisVideo']['FragmentNumber']
        stemp = data_json['InputInformation']['KinesisVideo']['ServerTimestamp']
        
        for face in data_json['FaceSearchResponse']:
            print(face)
            face_ok = True
            for matchedface in face['MatchedFaces']:
                print(matchedface)
                face_id = matchedface['Face']['FaceId']
        
        print("face_id:"+face_id+" fnumber:"+fnumber)
        
        if face_id != "" and face_ok:
            return True, face_id, getpicture(fnumber)
        else:
            return False, face_id, getpicture(fnumber)

def trigger():
    response = db2_table.query(
            KeyConditionExpression=Key('faceId').eq("triggerstemp")
        )
    oldtime = response['Items'][0]['senttime']
    ts = time.time()
    
    if oldtime+120>= ts:
        print("oldtime:"+str(oldtime) + " now:" + str(ts))
        return False
    else:
        print("oldtime:"+str(oldtime) + " now:" + str(ts))
        print("Trigger")
        try:
            response = db2_table.update_item(
                    Key = {
                        'faceId': "triggerstemp"
                    },
                    UpdateExpression = "set #senttime = :senttime",
                    ExpressionAttributeValues = {
                        ':senttime': int(ts),
                    },
                    ExpressionAttributeNames={
                        "#senttime": "senttime",
                    }
                )
        except Exception as e:
            print('Exception: ', e)
        return True

def lambda_handler(event, context):
    
    if not trigger():
        return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
    known, face_id, photo_info = ifknownface(event)
    print(known, face_id, photo_info)

    if known:
        print("A Known Face")
        response = db2_table.query(
            KeyConditionExpression=Key('faceId').eq(face_id)
        )
        visitor = response['Items'][0]
        phone_number = visitor['phoneNumber']
        photos = visitor['photos']
        updateVisitorPhoto(photos, face_id, photo_info)
        generateOTP(face_id, phone_number)
    else:
        print("An Unknown Face")
        requestPermission(photo_info)
    

    
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }
    
def getpicture(ids):
    
    hls_stream_ARN = "arn:aws:kinesisvideo:us-east-1:585623052567:stream/hw2video/1572992865189"
    STREAM_NAME = "hw2video"
    kvs = boto3.client("kinesisvideo")
    
    response = kvs.get_data_endpoint(
        StreamARN=hls_stream_ARN,
        APIName='GET_MEDIA'
        )
        
    endpoint_url_string = response['DataEndpoint']
    
    print("get endpoint:"+endpoint_url_string)
    
    streaming_client = boto3.client(
        'kinesis-video-media',
        endpoint_url=endpoint_url_string,
        )
        
    kinesis_stream = streaming_client.get_media(
        StreamARN=hls_stream_ARN,
        StartSelector={'StartSelectorType':'NOW'},
        )
        
    stream_payload = kinesis_stream['Payload']
    print("get video")

    s3 = boto3.resource("s3")
    print("start reading video")
    data = stream_payload.read(512*1024)
    print("end reading video")
    
    f = open("/tmp/temp.mp4","wb+")
    f.write(data)
    f.close()
    print("write video")
    
    cap= cv2.VideoCapture('/tmp/temp.mp4')
    print("open video")
    
    i=0
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == False:
            break
        i+=1
        if i == 10:
            cv2.imwrite('/tmp/temp.jpg',frame)
            print("write picture")
            s3.Bucket("hw2face").upload_file("/tmp/temp.jpg",ids+".jpg")
            print("send pictrue")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    print("freeing")
    return ids+".jpg"

def storeNewVisitor(face_id, photo_info):
    try:
        db2_table.put_item(
            Item = {
                'faceId': face_id,
                'name': 'None',
                'phoneNumber': 'None',
                'photos': [photo_info]
                }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    return True
    
def updateVisitorPhoto(photos, face_id, photo_info):
    
    try:
        response = db2_table.update_item(
            Key = {
                'faceId': face_id
                },
            UpdateExpression = "set #photos = :photos",
            ExpressionAttributeValues = {
                ':photos': photos + [photo_info]

                },
            ExpressionAttributeNames={
                "#photos": "photos"
                }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    return True
       
def generateOTP(face_id, phone_number):
    # generate OTP
    alphabet = string.ascii_letters + string.digits
    otp = ''.join(secrets.choice(alphabet) for i in range(9))
    ttl = int(time.time() + 60*5)
    
    # put OTP into db1
    try:
        db1_table.put_item(
            Item = {
                'faceId': face_id,
                'otp': otp,
                'TTL': ttl
                }
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    
    # Send OPT to user through SNS
    msg = 'OTP: ' + otp
    client = boto3.client('sns')
    try:
        client.publish(
            PhoneNumber=phone_number,
            Message=msg
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    
    return True
    
def requestPermission(photo_info):
    
    # Send to the photo and the comfirmation link to the owner through SNS
    photo_link = 'https://hw2face.s3.amazonaws.com/' + photo_info
    confirmation_link = 'https://smartdoor-assignment2.s3.amazonaws.com/WP1/webPage_1.html?faceId=' + photo_info
    client = boto3.client('sns')
    try:
        client.publish(
            #PhoneNumber='+19293436889',
            PhoneNumber='+12123806196',
            Message='photo link: ' + photo_link + '\nconfirmation link: ' + confirmation_link
        )
    except Exception as e:
        print('Exception: ', e)
        return False
    
    return True