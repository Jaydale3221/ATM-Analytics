# -*- coding: utf-8 -*-
"""BDT_project.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1XQLLoXBo3hsZuTT6BqBSZ2Wq3iUkDXhz
"""

from google.colab import drive
drive.mount('/content/drive')

"""## **Importing Libraries and setting environment variables**"""

!apt-get install openjdk-8-jdk-headless -qq > /dev/null

!tar xf /content/drive/MyDrive/something/spark-3.4.0-bin-hadoop3.tgz

!pip install -q findspark

import os
import sys
#os.environ["PYSPARK_PYTHON"] = "/Users/saavnbeli/opt/anaconda3/bin/python3"
os.environ['PYSPARK_SUBMIT_ARGS'] = '--jars aws-java-sdk-1.11.1010.jar,aws-java-sdk-s3-1.11.1034.jar pyspark-shell'
#os.environ['PYSPARK_SUBMIT_ARGS'] = '--driver-class-path hadoop-aws-3.3.4.jar --jars hadoop-aws-3.3.4.jar pyspark-shell'
os.environ["JAVA_HOME"] = "/usr/lib/jvm/java-8-openjdk-amd64"
os.environ["SPARK_HOME"] = "/content/spark-3.4.0-bin-hadoop3"
os.environ["PYLIB"] = os.environ["SPARK_HOME"] + "/python/lib"
sys.path.insert(0, os.environ["PYLIB"] +"/py4j-0.10.6-src.zip")
sys.path.insert(0, os.environ["PYLIB"] +"/pyspark.zip")

from pyspark.sql.types import StructType, StructField, IntegerType, StringType, BooleanType, DoubleType, LongType, FloatType
from pyspark.sql.functions import col,lit
from pyspark.sql.window import Window
from pyspark.sql.functions import row_number
from pyspark.sql.functions import from_unixtime
from pyspark.sql.functions import unix_timestamp
from pyspark.sql.functions import concat
from pyspark.sql.functions import lpad
import pyspark as pyspark
from pyspark import SparkContext

import findspark
findspark.init()
findspark.find()

from pyspark.sql import SparkSession
spark = SparkSession.builder\
        .master("local")\
        .appName("Colab")\
        .getOrCreate()

"""## **Creating schema**"""

dfschema = StructType([StructField('year', IntegerType(),True),
                                    StructField('month', StringType(),True),
                                    StructField('day', IntegerType(),True),
                                    StructField('weekday', StringType(),True),
                                    StructField('hour', IntegerType(),True),
                                    StructField('atm_status', StringType(),True),
                                    StructField('atm_id', StringType(),True),
                                    StructField('atm_manufacturer', StringType(),True),
                                    StructField('atm_location', StringType(),True),
                                    StructField('atm_streetname', StringType(),True),
                                    StructField('atm_street_number', IntegerType(),True),
                                    StructField('atm_zipcode', IntegerType(),True),
                                    StructField('atm_lat', FloatType(),True),
                                    StructField('atm_lon', FloatType(),True),
                                    StructField('currency', StringType(),True),
                                    StructField('card_type', StringType(),True),
                                    StructField('transaction_amount', IntegerType(),True),
                                    StructField('service', StringType(),True),
                                    StructField('message_code', StringType(),True),
                                    StructField('message_text', StringType(),True),
                                    StructField('weather_lat', FloatType(),True),
                                    StructField('weather_lon', FloatType(),True),
                                    StructField('weather_city_id', IntegerType(),True),
                                    StructField('weather_city_name', StringType(),True),
                                    StructField('temp', FloatType(),True),
                                    StructField('pressure', IntegerType(),True),
                                    StructField('humidity', IntegerType(),True),
                                    StructField('wind_speed', IntegerType(),True),
                                    StructField('wind_deg', IntegerType(),True),
                                    StructField('rain_3h', FloatType(),True),
                                    StructField('clouds_all', IntegerType(),True),
                                    StructField('weather_id', IntegerType(),True),
                                    StructField('weather_main', StringType(),True),
                                    StructField('weather_description', StringType(),True),])

"""## **Importing data**"""

df = spark.read.csv("/content/drive/MyDrive/BDT_dataset/atm_data_part1.csv", header=True, inferSchema = True, schema = dfschema)

df.head()

df1 = spark.read.csv("/content/drive/MyDrive/BDT_dataset/atm_data_part2.csv", header=True, inferSchema = True, schema = dfschema)

df.head()

spar_df = df.union(df1)

spar_df.printSchema()

spar_df.count()

spar_df.columns

"""### **Checking for null values**"""

# craeting a function to check null values in dataframe
import pyspark.sql.functions as F
def count_missings(spark_df,sort=True):
    """
    Counts number of nulls and nans in each column
    """
    df = spark_df.select([F.count(F.when(F.isnan(c) | F.isnull(c), c)).alias(c) for (c,c_type) in spark_df.dtypes if c_type not in ('timestamp', 'date')]).toPandas()

    if len(df) == 0:
        print("There are no any missing values!")
        return None

    if sort:
        return df.rename(index={0: 'count'}).T.sort_values("count",ascending=False)

    return df

# checking null values
count_missings(spar_df)

"""## **Creating `Location` dimension**"""

# Reading respective columns for location dimension from spar_df
dim_location = spar_df.select([spar_df.atm_location.alias("location"),
                                spar_df.atm_streetname.alias("streetname"),
                                spar_df.atm_street_number.alias("street_number"),
                                spar_df.atm_zipcode.alias("zipcode"),
                                spar_df.atm_lat.alias("lat"),
                                spar_df.atm_lon.alias("lon")]).distinct()

dim_location.show(5, truncate=False)

dim_location.count()

# adding column for primary key
dim_location= dim_location.withColumn("new_column",lit("ABC"))
# creating primary key
w = Window().partitionBy('new_column').orderBy(lit('A'))
dim_location= dim_location.withColumn("atm_location_id", row_number().over(w)).drop("new_column")
dim_location.printSchema()

dim_location.filter(dim_location['atm_location_id'] > 106).collect()

# Rearrange dim_location
location = dim_location.select("atm_location_id","location","streetname","street_number","zipcode","lat","lon")

"""## **Creating `Card Type`**"""

# creating card_type dimension
dim_card_type = spar_df.select([spar_df.card_type.alias("card_type")]).distinct()

#checking count for validation hence verified
dim_card_type.count()

# creating primary key or card_type_id column
dim_card_type= dim_card_type.withColumn("new_column",lit("ABC"))
w = Window().partitionBy('new_column').orderBy(lit('A'))
dim_card_type= dim_card_type.withColumn("card_type_id", row_number().over(w)).drop("new_column")

# Checking dataframe's top 5 rows
dim_card_type.show(5)

card_type = dim_card_type.select("card_type_id","card_type")

"""## **Creating `Date` dimension**"""

# Creating date data fame
dim_date = spar_df.select([spar_df.year.alias("year"),spar_df.month.alias("month"),spar_df.day.alias("day"),spar_df.hour.alias("hour"),spar_df.weekday.alias("weekday")]).distinct()

# Checking top 20 rows
dim_date.show()

from pyspark.sql.functions  import date_format
from pyspark.sql.functions import to_timestamp
from pyspark.sql.functions import to_date

# Creating New Month column with Integer value.
dim_date=dim_date.withColumn('month_new', date_format(to_date(col('month'),'MMMM'),'MM').cast(IntegerType()))

## adding new Month, day and hours columns with Zeroes
dim_date=dim_date.withColumn('month_new', lpad(col('month_new'),2,'0')).withColumn('day_new', lpad(col('day'),2,'0')).withColumn('hour_new', lpad(col('hour'),2,'0'))

# Create a new column Full_Date_time by combining Year, new month, day, hour and "00" value to create timestamp in YYYYMMDDMI24HHMI format.
dim_date_final=dim_date.withColumn("full_date_time",concat(col('year'),col('month_new'),col('day_new'),col('hour_new'),lit('00')))

# checking newly created columns
dim_date_final.show(10)

# Creating primary key for the dimension with name date_id
dim_date_final= dim_date_final.withColumn("new_column",lit("ABC"))
w = Window().partitionBy('new_column').orderBy(lit('A'))
dim_date_final= dim_date_final.withColumn("date_id", row_number().over(w)).drop("new_column")

# creating data from dim_date_final
date = dim_date_final.select("date_id","full_date_time","year","month","day","hour","weekday")

#Finding the count for validation
date.count()

date.show(10)

"""## **Creating `ATM` dimension**"""

#creating new data fame with atm related columns
dim_atm = spar_df.select([spar_df.atm_id.alias("atm_number"),spar_df.atm_manufacturer.alias("atm_manufacturer"),spar_df.atm_lat.alias("lat"),spar_df.atm_lon.alias("lon")])

# Checking top 3 rows
dim_atm.show(3)

#To add atm_location_id of dim_location df as a foreign key to the atm table, adding left join to the atm table and locatino table.
dim_atm = dim_atm.join(location, on = ["lat","lon"],how = "leftouter")

# Taking distinct values to avoid repeated values
atm_distinct =dim_atm.distinct()

#adding our primary key to the 156 sets of data
atm_distinct= atm_distinct.withColumn("new_column",lit("ABC"))
w = Window().partitionBy('new_column').orderBy(lit('A'))
atm_distinct= atm_distinct.withColumn("atm_id", row_number().over(w)).drop("new_column")

# creating atm from atm_distinct
atm = atm_distinct.select('atm_id','atm_number','atm_manufacturer','atm_location_id')

#Rechecking the count for validation
atm.count()

"""## **Creating `fact table`**"""

# Creating alias
spar_df = spar_df.alias('spar_df')
date = date.alias('date')
dim_card_type = dim_card_type.alias('dim_card_type')
dim_location = dim_location.alias('dim_location')
atm = atm.alias('atm')

"""##### Note: Creating fact table will take 4 steps by outer left joining the input table with dimension tables
##### Note: Dropping columns as required except primary keys of dimension table as they will act as foreign key

##### Creating first_df
"""

# Creating firts_df by left join of date dimension on input data frame and dropping columns
first_df =spar_df.join(date, on = ['year','month','day','hour','weekday'],how='left').select('spar_df.*','date.date_id').drop(*['year','month','day','hour','weekday'])

#  Creating alias for first
first_df = first_df.alias("first_df")

# Checking count for first step for validation
first_df.count()

"""##### Creating second_df"""

# Creating second_df by joining card_type dimension with first_df
second_df = first_df.join(dim_card_type, on = ['card_type'], how = 'left').select('first_df.*','dim_card_type.card_type_id').drop(*['card_type'])

# Checking schema
second_df.printSchema()

#  Creating alias
second_df = second_df.alias('second_df')

"""##### Creating third_df"""

# Creating third_df by joining location dimension with second_df by performing outer join
third_df = second_df.withColumnRenamed('atm_location','location').withColumnRenamed('atm_lat','lat').withColumnRenamed('atm_lon','lon').withColumnRenamed('atm_streetname','streetname').withColumnRenamed('atm_street_number','street_number').withColumnRenamed('atm_zipcode','zipcode').join(dim_location, on = ['location','lat','lon','streetname','street_number','zipcode'],how = 'left').select('second_df.*','dim_location.atm_location_id').drop(*['location','lat','lon','streetname','street_number','zipcode'])

# checking count again
third_df.count()

# Creating alias
third_df= third_df.alias('third_df')

# Checking schema
third_df.printSchema()

# Renaming atm_id as atm_number as atm_id imported from input df
third_df = third_df.withColumnRenamed('atm_id',"atm_number")

# Checking schema
third_df.printSchema()

"""##### Creating fourth_df"""

# Craeting fourth_df by left joining of third with atm dimension
fourth_df= third_df.join(atm,on =['atm_number','atm_manufacturer','atm_location_id'],how ='left').select('third_df.*','atm.atm_id').drop(*['atm_manufacturer','atm_nummber'])

# Checking count for validation hence verifed
fourth_df.count()

# Checking schema
fourth_df.printSchema()

# top 3 rows
fourth_df.show(3)

# Rechecking count
fourth_df.count()

"""##### Final step creating fact table fact_atm_trans"""

# creating fact table from fourth_df
fact_atm_trans = fourth_df.alias("fact_atm_trans")

#adding our primary key to fact table
fact_atm_trans= fact_atm_trans.withColumn("new_column",lit("ABC"))
w = Window().partitionBy('new_column').orderBy(lit('A'))
fact_atm_trans= fact_atm_trans.withColumn("trans_id", row_number().over(w)).drop("new_column")

# checking schema of fact table
fact_atm_trans.printSchema()

# dropping irrelevant columns as per schema
fact_atm_trans = fact_atm_trans.drop('weather_lat','weather_lon','weather_city_id','weather_city_name','temp','pressure','humidity','wind_speed','wind_deg')

# Renaming atm_location_id as weather_loaction_id as per schema
fact_atm_trans = fact_atm_trans.withColumnRenamed("atm_location_id","weather_loc_id")

# Checking final schema
fact_atm_trans.printSchema()

fact_atm_trans1 = fact_atm_trans.select('trans_id','atm_id','weather_loc_id','date_id','card_type_id','atm_status','currency','service','transaction_amount','message_code','message_text','rain_3h','clouds_all','weather_id','weather_main','weather_description')

fact_atm_trans1 = fact_atm_trans1.alias('fact_atm_trans1')

fact_atm_trans1.show(2)

fact_atm_trans1.printSchema()

"""## **Writing csv**

##### **Saving fact table as csv**
"""

fact_atm_trans1.coalesce(1).write.mode("overwrite").option("header", "true").csv("/content/drive/MyDrive/BDT_dataset/Cleaned dataset/fact.csv")

"""##### **Dimension tables**"""

#dim-atm/
atm.coalesce(1).write.mode("overwrite").option("header", "true").csv("/content/drive/MyDrive/BDT_dataset/Cleaned dataset/atm.csv")

### dim-card-type/
card_type.coalesce(1).write.mode("overwrite").option("header", "true").csv("/content/drive/MyDrive/BDT_dataset/Cleaned dataset/card_type.csv")

#dim-date
date.coalesce(1).write.mode("overwrite").option("header", "true").csv("/content/drive/MyDrive/BDT_dataset/Cleaned dataset/data.csv")

#dim-location
location.coalesce(1).write.mode("overwrite").option("header", "true").csv("/content/drive/MyDrive/BDT_dataset/Cleaned dataset/location.csv")