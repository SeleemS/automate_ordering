# automate_ordering

**Made to work with Marketman**

This code is setup to work with AWS. Hosted on AWS Lambda, and invoked on a schedule via AWS Eventbridge.

***How to Setup:***

1. Clone this directory on your machine
2. Unzip *dependencies.zip*
3. Define variables at the top of *lambda_function.py*
4. Compress *entire package* into one .zip file (unzipped dependencies + *lambda_function.py*)
5. Upload to a new *AWS Lambda* function, Python 3.12 runtime
6. Increase timeout to 2 minutes (just in case)
7. Create a schedule to invoke function in *AWS Eventbridge*

