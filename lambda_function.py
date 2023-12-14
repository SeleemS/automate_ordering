

def lambda_handler(event, context):

  import requests
  import json
  import pandas as pd
  import os
  import math
  from datetime import datetime, timedelta
  import pytz

  url = "https://api.marketman.com/v3/buyers/auth/GetToken"

  payload = json.dumps({
    "APIKey": "xyz",
    "APIPassword": "xyz"
  })
  headers = {
    'Content-Type': 'application/json'
  }
  6
  response = requests.request("POST", url, headers=headers, data=payload)

  # Parse the response JSON
  response_data = response.json()

  # Extract the token and store it in auth_token
  auth_token = response.json()["Token"]
  print(auth_token)


  #GetItems Report
  desired_buyer_guid = sq1_buyer_guid
  desired_store_guid = sq1_guid

  url = "https://api.marketman.com/v3/buyers/inventory/GetItems"

  payload = json.dumps({
    "itemIDs": None,
    "BuyerGuid": sq1_guid
  })
  headers = {
    'Content-Type': 'application/json',
    'AUTH_TOKEN': auth_token
  }

  response = requests.request("POST", url, headers=headers, data=payload)

  data = json.loads(response.text)


  # For demonstration, let's convert the data to a Pandas DataFrame.
  df = pd.DataFrame(data['InventoryItems'])

  # Now, you can process the DataFrame or return its contents as required.
  print(df.head())

  # If you want to return the data as a response from Lambda:
  lambda_response = {
      'statusCode': 200,
      'body': json.dumps(data)
  }

  import json

  def convert_uom(value, from_uom, to_uom):

      conversions = {
          ("Kg", "gr"): 1000,
          ("gr", "Kg"): 0.001,
          ("L", "ml"): 1000,
          ("ml", "L"): 0.001,
          ("lb", "oz"): 16,
          ("oz", "lb"): 0.0625,
          ("gal", "fl-oz"): 128,
          ("fl-oz", "gal"): 0.0078125
      }
      
      conversion_factor = conversions.get((from_uom, to_uom), 1)
      return value * conversion_factor

  def process_data(json_data):
      # Define the full path for the input file
      #input_json_path = os.path.join(os.getcwd(), input_json_filename)
      
      # Load the JSON data
      #with open(input_json_path, 'r') as file:
          #json_data = json.load(file)
      
      # Convert the list of dictionaries to a DataFrame using 'InventoryItems' key
      df = pd.DataFrame(json_data['InventoryItems'])
      
      # Filter items based on the specified conditions and adjust UOM if needed
      filtered_items = []

      for index, row in df.iterrows():
          if row['OnHand'] < row['MinOnHand']:
              for purchase_item in row['PurchaseItems']:
                  if (purchase_item['VendorName'] == "SYSCO" and purchase_item['IsMainPurchaseOption'] == True):
                      
                      # Adjust OnHand if UOMs don't match
                      adjusted_onhand = row['OnHand']
                      original_onhand = row['OnHand']

                      if row['UOMName'] != purchase_item['UOMName']:
                          adjusted_onhand = convert_uom(row['OnHand'], row['UOMName'], purchase_item['UOMName'])
                          
                      restock_qty_inventory_uom = row['ParLevel'] - original_onhand

                      # Calculate restock quantity in vendor's UOM
                      restock_qty_vendor_uom = convert_uom(restock_qty_inventory_uom, row['UOMName'], purchase_item['UOMName'])

                      units_per_pack = purchase_item.get('PackQty')
                      packs_per_case = purchase_item.get('PacksPerCase')

                      if units_per_pack is None or packs_per_case is None:
                          # Handle this case, maybe set them to 1 or skip the item
                          units_per_pack = 1 if units_per_pack is None else units_per_pack
                          packs_per_case = 1 if packs_per_case is None else packs_per_case

                      total_units_per_case = units_per_pack * packs_per_case
                      cases_to_order = restock_qty_vendor_uom // total_units_per_case
                      additional_packs_to_order = (restock_qty_vendor_uom % total_units_per_case) // units_per_pack

                      # Edge Case Handling: If no cases and no additional packs are ordered, but restock quantity is positive, 
                      # ensure at least one pack is ordered.
                      if cases_to_order == 0 and additional_packs_to_order == 0 and restock_qty_vendor_uom > 0:
                          additional_packs_to_order = 1

                      # Calculate the order quantity in vendor's UOM
                      order_qty = cases_to_order + (additional_packs_to_order / packs_per_case)
      
                      # Round order_qty up to the nearest whole number
                      order_qty = math.ceil(order_qty)
                      
                      filtered_items.append({
                          'ID': row['ID'],
                          'Name': row['Name'],
                          'OriginalOnHand': row['OnHand'],  # Original unadjusted OnHand
                          'AdjustedOnHand': adjusted_onhand,
                          'OriginalUOM': row['UOMName'],
                          'PurchaseUOM': purchase_item['UOMName'],
                          'MinOnHand': row['MinOnHand'],
                          'ParLevel': row['ParLevel'],
                          'VendorGuid': purchase_item['VendorGuid'],
                          'CatalogItemCode': purchase_item['CatalogItemCode'],
                          'OrderQuantity': order_qty
                      })

      # Convert filtered items to a DataFrame
      filtered_df = pd.DataFrame(filtered_items)
      
      # Save filtered_df to a CSV file in the same directory
      #output_csv_path = os.path.join(os.getcwd(), 'filtered_data.csv')
      #filtered_df.to_csv(output_csv_path, index=False)
      
      # Extract data to populate the config.json file
      config_data = {
          "items": []
      }

      for index, row in filtered_df.iterrows():
          config_data["items"].append({
              "ID": row['ID'],
              "Name": row['Name'],
              "OriginalOnHand": row['OriginalOnHand'],  # Added for review
              "AdjustedOnHand": row['AdjustedOnHand'],
              "OriginalUOM": row['OriginalUOM'],
              "PurchaseUOM": row['PurchaseUOM'],
              "MinOnHand": row['MinOnHand'],
              "ParLevel": row['ParLevel'],
              "VendorGuid": row['VendorGuid'],
              "CatalogItemCode": row['CatalogItemCode'],
              "OrderQuantity": row['OrderQuantity']
          })
      return config_data


  # You can call the function as follows
  config_data = process_data(data)



  catalog_items = []
  for item in config_data['items']:
      catalog_items.append({
          "CatalogItemCode": item["CatalogItemCode"],
          "Quantity": item["OrderQuantity"]
      })

  # Get the current time in UTC
  current_time_utc = datetime.utcnow().replace(tzinfo=pytz.utc)

  # Convert UTC to Toronto time
  toronto_timezone = pytz.timezone('America/Toronto')
  current_time_toronto = current_time_utc.astimezone(toronto_timezone)

  # Format the sent and delivery dates
  sent_date = current_time_toronto.strftime('%Y/%m/%d %H:%M:%S')
  delivery_date = (current_time_toronto + timedelta(days=1)).replace(hour=12, minute=0, second=0).strftime('%Y/%m/%d %H:%M:%S')

  # Format the payload for the API call
  payload = {
      "BuyerGuid": desired_store_guid,
      "VendorGuid": sysco_guid,
      "OrderStatus": "sent",
      "deliveryDateUTC": delivery_date,
      "sentDateUTC": sent_date,
      "BuyerUserGuid": desired_buyer_guid,
      "comments": None,
      "catalogItems": catalog_items
  }

  headers = {
      'AUTH_TOKEN': auth_token
  }

  # Make the API call
  url = "https://api.marketman.com/v3/buyers/orders/CreateOrder"
  response = requests.post(url, headers=headers, json=payload)

  # Print the API response

  data = json.loads(response.text)

  return {
        'statusCode': 200,
        'body': json.dumps(data, indent=2)
    }














