#!/usr/bin/env python3

# Save script on each RPI0W
# This script contain two part
#   1. Will create table if device/table_name not in database
#   2. Insert value to database
# --------------------------------------------------------------------------------------------------------------------------

import mysql.connector
import logging

logging.basicConfig(filename='/home/pi/Fridge-to-Incubator/fridge.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s:%(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

class Chamber(object):
    # global variable
    host = "192.168.0.100"  # IP address hosting the MySQL  #TODO CHANGE IP
    user = "smartfarming"  # MySQL username
    password = "smartfarming"  # MySQL password
    database = "SucculentFarm"  # MySQL database name

    # establish connection (SmartFarming database/mysql)
    mydb = mysql.connector.connect(
        host=host,  # IP address hosting the MySQL
        user=user,  # MySQL username
        password=password  # MySQL pass
    )
    print("connect complete")


    def __init__(self, device):

        self.chamber = device  # will be used as table name

        # creating a cursor object using the cursor() method
        mycursor = self.mydb.cursor()

        print("before database")
        # create_database if not exist
        mycursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(self.database))
        print("Created database")

        mycursor.execute("USE {}".format(self.database))

        # preparing SQL query to CREATE TABLE into the database.
        sql = """CREATE TABLE IF NOT EXISTS `{}` (
            Device TEXT,
            DateTime DATETIME,
            Temperature FLOAT,
            Light_switch INT,
            Compressor_switch INT
            );
            """.format(self.chamber)

        # execute the SQL command
        mycursor.execute(sql)


    def insert_reading_values(self, sensors):
        """Insert values into SQL database table"""

        # SQL command
        sensor_sql = f"""INSERT INTO `{self.chamber}` VALUES {sensors};"""

        # creating a cursor object using the cursor() method
        mycursor = self.mydb.cursor()

        try:
            # execute the SQL command
            mycursor.execute(sensor_sql)

            # commit changes in database
            self.mydb.commit()
            print("Commit sensors reading {}".format(sensors))

        except Exception as e:
            print(e)
            logging.warning("Fail to write to database")
            # Rolling back in case of error
            self.mydb.rollback()
            print("error, rollback")

        # Do not close connection here. Will terminate other connection
        # self.mydb.close()
        # print("CLOSED")
