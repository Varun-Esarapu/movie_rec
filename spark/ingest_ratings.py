import os
import sys

# Ensure HADOOP_HOME is configured on Windows
hadoop_dir = r"C:\hadoop"
if os.path.exists(hadoop_dir):
    os.environ["HADOOP_HOME"] = hadoop_dir
    os.environ["hadoop.home.dir"] = hadoop_dir
    os.environ["PATH"] = os.path.join(hadoop_dir, "bin") + ";" + os.environ.get("PATH", "")

from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType

def run_ingestion_verification():
    # Initialize SparkSession with specified resource limits and settings
    spark = SparkSession.builder \
        .appName("MovieLens32M_Ingestion") \
        .config("spark.driver.memory", "6g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.sql.shuffle.partitions", "40") \
        .config("spark.driver.maxResultSize", "2g") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem") \
        .getOrCreate()

    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    # Explicit schema definition prevents Spark from reading the entire file twice to infer types
    ratings_schema = StructType([
        StructField("userId", IntegerType(), False),
        StructField("movieId", IntegerType(), False),
        StructField("rating", FloatType(), False),
        StructField("timestamp", LongType(), False)
    ])

    ratings_path = "./data/raw/ratings.csv"
    if not os.path.exists(ratings_path):
        print(f"Error: {ratings_path} not found. Please verify data download.")
        spark.stop()
        return

    print("\nReading data/raw/ratings.csv into PySpark DataFrame...")
    ratings_df = spark.read \
        .option("header", "true") \
        .schema(ratings_schema) \
        .csv(ratings_path)

    print("\n--- 1. Verified PySpark Schema ---")
    ratings_df.printSchema()

    print("\n--- 2. Physical Execution Plan (Lazy Evaluation) ---")
    ratings_df.explain(True)

    print("\n--- 3. Data Preview (First 5 Rows) ---")
    ratings_df.show(5)

    print("\n--- 4. Verification Check: Row Count ---")
    total_count = ratings_df.count()
    print(f"Successfully loaded and verified {total_count:,} rating interactions without memory overflow!")

    spark.stop()

if __name__ == "__main__":
    run_ingestion_verification()
