import os
import sys

# Ensure HADOOP_HOME is configured on Windows
hadoop_dir = r"C:\hadoop"
if os.path.exists(hadoop_dir):
    os.environ["HADOOP_HOME"] = hadoop_dir
    os.environ["hadoop.home.dir"] = hadoop_dir
    os.environ["PATH"] = os.path.join(hadoop_dir, "bin") + ";" + os.environ.get("PATH", "")

from pyspark.sql import SparkSession
from pyspark.sql.functions import col

def export_parquet_to_postgres():
    pg_host = os.getenv("POSTGRES_HOST", "localhost")
    pg_port = os.getenv("POSTGRES_PORT", "5432")
    pg_db = os.getenv("POSTGRES_DB", "recommender_db")
    pg_user = os.getenv("POSTGRES_USER", "recommender_user")
    pg_password = os.getenv("POSTGRES_PASSWORD", "recommender_password")

    jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"

    spark = SparkSession.builder \
        .appName("Export_Recommendations_To_PostgreSQL") \
        .config("spark.driver.memory", "4g") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem") \
        .getOrCreate()

    parquet_path = "./data/processed/recommendations"
    if not os.path.exists(parquet_path):
        # Fallback to single parquet file if exists
        parquet_path = "./data/processed/recommendations.parquet"

    if not os.path.exists(parquet_path):
        print(f"Error: Parquet file not found at {parquet_path}")
        spark.stop()
        return

    print(f"Reading Parquet recommendations from {parquet_path}...")
    df = spark.read.parquet(parquet_path)

    # Standardize column names to match Django Recommendation table
    cols = df.columns
    if "userId" in cols:
        df = df.withColumnRenamed("userId", "user_id")
    if "movieId" in cols:
        df = df.withColumnRenamed("movieId", "movie_id")

    print(f"Writing {df.count():,} rows to PostgreSQL table api_recommendation via JDBC...")
    jdbc_properties = {
        "user": pg_user,
        "password": pg_password,
        "driver": "org.postgresql.Driver",
        "batchsize": "10000"
    }

    df.select("user_id", "movie_id", "score", "rank").write.jdbc(
        url=jdbc_url,
        table="api_recommendation",
        mode="append",
        properties=jdbc_properties
    )

    print("Export complete.")
    spark.stop()

if __name__ == "__main__":
    export_parquet_to_postgres()
