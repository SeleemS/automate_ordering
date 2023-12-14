# automate_ordering

**Made to work with Marketman**

This code is setup to work with AWS. Hosted on AWS Lambda, and invoked on a schedule via AWS Eventbridge.

***How to Setup:***

1. Clone this directory on your machine
2. Unzip **dependencies.zip**
3. Define variables at the top of **lambda_function.py**
4. Compress *entire package* into one .zip file (unzipped dependencies + **lambda_function.py**)
5. Upload to a new **AWS Lambda** function, Python 3.12 runtime
6. Increase timeout to 2 minutes (just in case)
7. Create a schedule to invoke function in **AWS Eventbridge**


***How it Works:***

1. Get MarketMan auth token (expires weekly)
2. Pull **GetItems** report, extract data by key **InventoryItems** and transform into Pandas df
3. Define a function to convert UOM where needed
4. Check for all items in **InventoryItems** where **OnHand** < **MinOnHand**, and **MainPurchaseOption** = "Vendor of Choice"
5. Calculate restock qty based on **OnHand** value, **Par Level**, and **UOM**
6. Add all relevant items to dictionary **filtered_items** and convert into Pandas df
7. Place order using the **filtered_items** df as a config file

**Should be setup to work in the background.**

Must ensure that Inventory Counts are accurate, and MinOnHand + Par Levels are updated regularly throughout the year.

