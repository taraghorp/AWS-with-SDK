"Build a grid from the files in a source folder"
import os
import io
import math
import tempfile
import sys
import boto3
from PIL import Image

if len(sys.argv) != 3:
    print(
        "This script takes 3 parameters: [source-bucket] [destination-bucket]")
    sys.exit()

s3 = boto3.client("s3")
source_bucket = sys.argv[1]
destination_bucket = sys.argv[2]

tile_size = 100

# get all the images from the s3 bucket
# CHALLENGE-B BEGIN
response = s3.list_objects_v2(Bucket=source_bucket)
# CHALLENGE-B END
source_images = [obj["Key"] for obj in response["Contents"]]
image_count = len(source_images)

# calc the height, width of the grid
tiles_width = math.floor(math.sqrt(image_count))
tiles_height = math.ceil(image_count / tiles_width)

print(
    f"Converting: {image_count} source images.\n\n Creating: {tiles_width} x {tiles_height} grid.\n\n")

destination_image = Image.new(mode="RGB", size=(
    tiles_width * tile_size, tiles_height * tile_size))
for y in range(tiles_height):
    for x in range(tiles_width):
        if source_images:
            filename = source_images.pop()

# get the contents of an image in the bucket
# CHALLENGE-C BEGIN
            response = s3.get_object(Bucket=source_bucket,
                                     Key=filename)
# CHALLENGE-C END
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

destination_key = os.urandom(16).hex() + ".jpg"
with open(temp_file, 'rb') as data:
    # copy the grid image to a randomly named object in the destination bucket
    # CHALLENGE-D BEGIN
    s3.put_object(
        Bucket=destination_bucket,
        Key=destination_key,
        Body=data,
        ContentType='image/jpg'
    )
# CHALLENGE-D END

print(
    f"Saved file to s3 bucket: {destination_bucket}, key: {destination_key}\n\n")

# build a presigned URL for the s3 bucket
# CHALLENGE-E BEGIN
presigned_url = s3.generate_presigned_url("get_object", Params={
                                          "Bucket": destination_bucket, "Key": destination_key}, ExpiresIn=5 * 60)
# CHALLENGE-E END
print(f"Presigned URL: {presigned_url}\n")
