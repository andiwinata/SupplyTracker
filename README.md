# SupplyTracker
This is Supply Tracker, a website application designed to help small business to track their supply, stock, income and outcome.

### Showcase
<a href="https://www.youtube.com/watch?v=eGryu3QppGw"><img src="http://img.youtube.com/vi/eGryu3QppGw/0.jpg" 
alt="Supply Tracker showcase" width="240" height="180" border="10" /></a> overview showing what the applications can do

### How to use
* Make sure python 3.5.x installed
* Run command `pip install -r PackageRequirements.txt`, the text file is in the root of this repository
* Run command `python run.py` to start the server
* Open `localhost:5000` or `127.0.0.1:5000` to open the web application (if you are accessing the website from other device in the local area network simply open the local ip address where the server runs on
* Now you can use the app!

Note: If you are a windows user there is a `.zip` file which contains `.exe` to start the server, which I made using <a href="http://www.pyinstaller.org/">PyInstaller<a>. You can download the `.exe` from <a href="https://drive.google.com/file/d/0BwsV72mbL8gYYVNhMXNocFg1S0E/view?usp=sharing">here </a>. After extracting the file, just run `run.exe` to start the server, and open the address `localhost:5000` as mentioned above

### Packages used:
* Flask
* WTForm
* SQLAlchemy
* Bootstrap

Database used:
* SQLite

---

### A bit of information about the app structure:

* To <b>populate</b> data use the forms in the `Add` sections
* `ItemType` is defining the type of item, e.g. book, table, chair, pencil, pen, laptop, etc
* `Supplier` is contact information of where user gets the item from
* `Customer` is contact information about people whom purchase the user's items
* `Courier` is list of parties which do the delivery to user's customers
* `TransactionMedium` is how the transaction takes place, e.g. through chat from facebook, message, phone call, face to face, etc
* `PurchaseTransaction` is record of what involves in the transaction between user and the supplier. There are entries for transaction date, supplier, transaction items (with price, item type, and quantity), and finally note. This is the main entry where user registers their stock or items in their supply storage.
* `SaleTransaction` is record of transaction between user and the customer. There are entries for transaction date, delivery fee*, customer, courier*, transaction medium*, transaction items (with price, item type, and quantity; <b>Be aware that the total quantity of sold items cannot exceed the total of the item in stock or storage</b> and that's why the drop down for sale items have listed total storage so the user will know how much they can sell). The picked item will always be chosen using FIFO method (First in first out) which means the unsold items will be sorted by date in ascending order and the first ones will be put to sale first. *Optional field
* To <b>view</b> of records in the database, click the relevant sections from `View` tab
* `ItemList` is a read-only and prepopulated table, these are all the items which the user has bought from suppliers. They come from `PurchaseTransaction` and each of the item marked individually with unique ID (even though it may not the case for the real item), to ease in the income/outcome/profit calculations.
* `ItemTypeList` is a list of item type registered in database, they are editable and deletable. <b>Note:</b> If you delete one of the record it will <b>also</b> delete all the `Item` related to this item type
* `ItemStock` is a read-only and prepopulated table containing all items categorized by the `ItemType` and summary of total item in the storage, total sold, and profit for each type
* `Supplier` is a list of suppliers and their information, they are associated to `PurchaseTransaction`. <b>Note:</b> If you delete one of the record it will <b>also</b> delete all the `PurchaseTransaction` related to this supplier, which will <b>chain</b> delete the `Item` related to the transaction
* `Customer` is a list of customers and their information, they are associated to `SaleTransaction`. <b>Note:</b> If you delete one of the record it will <b>also</b> delete all the `SaleTransaction` related to this customer, which will affect the record of associated `Item` as in they will be losing <i>sold</i> status.
* `Courier` is a list of courier used to deliver item to `Customer`, they are optional field in `SaleTransaction`
* `TransactionMedium` is a list of how the transaction happens, they are optional field in `SaleTransaction`
* `PurchaseTransaction` is a list of items purchased from `Supplier` with relevant information about the transaction, and this is the gateway for user to enter `Item` to database. If one record of this transaction is deleted, it will also delete the `Item` in the database which will affect record of `SaleTransaction` too. User can edit the record to remove and adding items or edit the transaction record itself, such as date, supplier and notes.
* `SaleTransaction` is a list of items sold to the `Customer` with relevant information about the transaction. Once `Item` is sold or registered in one of this record, the profit will be calculated by substracting sale price with selected item purchase price (chosen by FIFO method). If you delete one of this record, it will only affect the status of `Item`, it will be marked back as 'unsold' item (or going back to storage), just be careful if the `SaleTransaction` is kind of old, you will be returning 'old sold' items back to the storage with its original purchased price, and pretty sure the next sale transaction of same item type will pick these items (because FIFO) system
