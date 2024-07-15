-- SQLite
--CREATE TABLE users(Id int PRIMARY KEY,Name varchar(100) UNIQUE,Password varchar(20),Recovery int UNIQUE);
--INSERT INTO users VALUES(1,"Admin","Admin","123");
--select * from users;
--drop table object;
--create table object(Object_ID int PRIMARY KEY,
--Object_Name varchar(100),
--Object_type varchar(20),
--listing varchar(2),
--rating varchar(1),
--price int,
--image_src varchar(1000));
--insert into object(Object_ID,Object_Name,Object_type,listing,rating,price) values
--create table object_user(Object_ID  int, Id int, PRIMARY KEY (Object_ID,Id));
--select * from object_user;

--drop TABLE cart;
--create table cart(Transaction_ID int PRIMARY KEY,
--Buyer_ID int,
--Seller_ID int,
--Object_ID int,
--Purchase_Status varchar(2));

--CREATE table user_gold(ID int Primary key,Gold int );
--CREATE table user_bank(Acc_ID varchar(20) PRIMARY KEY,Acc_Password varchar(20),USD int);

--INSERT into user_bank VALUES
--("1111-2222-3333-4444","Abcde",1000000),
--("2222-3333-4444-5555","12345",2000),
--("3333-4444-5555-6666","23232324",40000),
--("5434-3434-1111-4445","23123123",500);

--select * from user_bank;

--create table user_store(ID int PRIMARY KEY,Funds int,Gold int);
--insert into user_store VALUES
--(1,0,0),
--(2,0,0);
--select Object_ID from object_user where Id = 1 and Object_ID != (select Object_ID from cart where Seller_ID = 1 and Purchase_Status = "N")
--update object set listing = "UL" where Object_ID IN (1,5,10);
--create table object_user1(Object_ID int PRIMARY key,Id int);
--insert into object_user1(Object_ID,Id) select Object_ID,Id from object_user;
--drop TABLE object_user;
--ALTER TABLE object_user1
--RENAME TO object_user;
/* 
drop table transactions;
drop table content;
create table transactions(
    Transaction_ID int PRIMARY KEY,
    Purchase_Status varchar(2),
    Total_Price int
);
create table content(
    Content_ID int PRIMARY KEY,
    Object_ID int,
    Buyer_ID int,
    Seller_ID int,
    Transaction_ID int,
    Price int
); */

/* alter table transactions drop COLUMN Purchase_Status; */

/* alter table transactions add COLUMN Purchase_Date date; */

/* drop table content;
create table content(
    Object_ID int,
    Buyer_ID int,
    Seller_ID int,
    Transaction_ID int,
    Price int,
    PRIMARY key (Object_ID,Buyer_ID,Seller_ID,Transaction_ID)
); */

/* drop table user_spin; */
/* select * from object where listing = "UL"; */
/* 
ALTER TABLE users ADD COLUMN description TEXT;
ALTER TABLE users ADD COLUMN profile_pic TEXT; */

.schema