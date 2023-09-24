import math
import os
import json
import boto3
import io
import tempfile
from PIL import Image

source_bucket = os.getenv('SOURCE_BUCKET')
destination_bucket = os.getenv('DESTINATION_BUCKET')
s3 = boto3.client("s3")
dynamodb = boto3.client("dynamodb")
table_name = "GridBuilder"
tile_size = 100

def lambda_handler(event, context):
    uniqueGridId =  event["queryStringParameters"]["uniqueGridId"]

    # ask dynamo db for the list of images
    response = dynamodb.query(
        TableName=table_name,
        KeyConditions={
            "uniqueGridId" : { "AttributeValueList" : [{"S" : uniqueGridId}], 'ComparisonOperator': 'EQ'}
        }
    )

    source_images = [ item["s3Key"]["S"] for item in response["Items"] ]
    image_count = len(source_images)
    print(f"Converting: {image_count} source images.")

    # calc the height, width of the grid
    tiles_width = math.floor(math.sqrt(image_count))
    tiles_height = math.ceil(image_count / tiles_width)

    print(f"Creating: {tiles_width} x {tiles_height} grid.")

    destination_image = Image.new(mode="RGB", size=(tiles_width * tile_size, tiles_height * tile_size))
    for y in range(tiles_height):
        for x in range(tiles_width):
            if source_images:
                filename = source_images.pop()
                response = s3.get_object(Bucket=source_bucket,
                            Key=filename)
                image_data = response['Body'].read()

                img = Image.open(io.BytesIO(image_data))
                img_width = img.size[0]
                img_height = img.size[1]
                # crop the image to a square the length of
                # the shorted side
                crop_square = min(img.size)
                img = img.crop(((img_width - crop_square) // 2,
                                (img_height - crop_square) // 2,
                                (img_width + crop_square) // 2,
                                (img_height + crop_square) // 2))
                img = img.resize((tile_size, tile_size))
                # draw the image onto the destination grid
                destination_image.paste(img, (x*tile_size, y*tile_size))

    # save the output image to a temp file
    temp_file = tempfile.NamedTemporaryFile(suffix='.jpg').name
    destination_image.save(temp_file)
    print(f"Creating temp file {temp_file}")

    # copy the grid to a randomly named object in the destination bucket
    destination_key = os.urandom(16).hex() + ".jpg"
    with open(temp_file, 'rb') as data:
        s3.put_object(
            Bucket=destination_bucket,
            Key=destination_key,
            Body=data,
            ContentType='image/jpg'
        )

    print(f"Saved file to s3 bucket: {destination_bucket}, key: {destination_key}")

    presigned_url = s3.generate_presigned_url("get_object", Params={"Bucket": destination_bucket, "Key": destination_key}, ExpiresIn=5 * 60)


    return {
        "statusCode": 200,
        "headers": { "access-control-allow-origin": "*" },
        "body": json.dumps({
            "message": "built grid",
            "presigned_url": presigned_url
        }),
    }
