
Zip up the Lambda function

```
# note to self: this needs to be done in a linux+x86 environment
# so we don't get the wrong binary dependencies
pip install -r requirements.txt --target ./package 


cd package ; zip -r ~/lambda-function.zip .


cd .. ; zip ~/lambda-function.zip lambda_function.py
```


Use the CLI to deploy the function

```
aws lambda create-function \
 --function-name grid-maker \
 --runtime python3.9 \
 --timeout 30 \
 --handler lambda_function.lambda_handler \
 --role arn:aws:iam::414514743156:role/lambda-basic-execution-role \
 --zip-file fileb://~/lambda-function.zip
```

Invoke the function

```
aws lambda invoke  --function-name grid-maker ~/output.txt
```