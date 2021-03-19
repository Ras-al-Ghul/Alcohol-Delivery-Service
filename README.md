# Group 6 Project Part 3

## Postgres Account
Database resides on FC2679

## Web application URL
http://35.185.33.140:8111/
(Will update with submission url when date nears)

source .virtualenvs/dbproj/bin/activate
psql -U fc2679 -h 34.73.36.248 -d project1
(can delete when submitting, just copying over from the previous readme)

## Login Credentials
1. Admin Credentials
    ```
        c.smith@booze.io
        Employee123
    ```
3. Customer Credentials
    ```
        stev_knoless98@yandex.com
        Customer123
    ```

A description of the parts of your original proposal in Part 1 that you implemented, the parts you did not (which hopefully is nothing or something very small), and possibly new features that were not included in the proposal and that you implemented anyway. If you did not implement some part of the proposal in Part 1, explain why.
## Application Implementation
1. Admin - Product Overview/Catalogue
2. Admin - Add new products
3. Admin - Delete products
4. Admin - Edit/Add Shipments
5. Admin - Order Overview
6. Customer - Product/Brand View with add to cart
7. Customer - Session support (retains cart/login info)
8. Customer - Choose/Edit/Add Shipping and Billing Addresses
9. Customer - Payment Page
10. Customer - Order History
11. Customer - Order Details 

__Extra Features__
1. Admin Edit Product Page
2. Customer Signup Page
3. Customer Edit Profile Page
4. Customer Cart view with discount

Briefly describe two of the web pages that require (what you consider) the most interesting database operations in terms of what the pages are used for, how the page is related to the database operations (e.g., inputs on the page are used in such and such way to produce database operations that do such and such), and why you think they are interesting.
## Two Interesting Web Pages

1. The first interesting database operation is not a single web page, but the workflow from the cart page to the order placement. Once the customer finalizes the cart, the information is stored in the session variables. Next, the address and the payment information are collected successively and stored in the session variables. Until this point, the database is not touched (except for Address edits). After the order is placed, we update all of the information related to the order i.e. the Order table, the OrderItems table, the Payment table, and the Customer Lives table as a single transaction - either everything gets updated or nothing happens. This is important to ensure consistency.