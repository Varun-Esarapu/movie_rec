import os
import sys

# Ensure HADOOP_HOME is configured on Windows
hadoop_dir = r"C:\hadoop"
if os.path.exists(hadoop_dir):
    os.environ["HADOOP_HOME"] = hadoop_dir
    os.environ["hadoop.home.dir"] = hadoop_dir
    os.environ["PATH"] = os.path.join(hadoop_dir, "bin") + ";" + os.environ.get("PATH", "")

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, count, explode, row_number
from pyspark.sql.window import Window
from pyspark.sql.types import StructType, StructField, IntegerType, FloatType, LongType
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator

def run_als_pipeline(export_to_jdbc=False, max_users=None):
    # Initialize SparkSession with requested resources and PostgreSQL driver
    spark = SparkSession.builder \
        .appName("MovieLens32M_ALS_Training") \
        .config("spark.driver.memory", "6g") \
        .config("spark.executor.memory", "6g") \
        .config("spark.sql.shuffle.partitions", "40") \
        .config("spark.driver.maxResultSize", "2g") \
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem") \
        .getOrCreate()

    sc = spark.sparkContext
    sc.setLogLevel("WARN")

    ratings_schema = StructType([
        StructField("userId", IntegerType(), False),
        StructField("movieId", IntegerType(), False),
        StructField("rating", FloatType(), False),
        StructField("timestamp", LongType(), False)
    ])

    ratings_path = "./data/raw/ratings.csv"
    if not os.path.exists(ratings_path):
        print(f"Error: {ratings_path} not found.")
        spark.stop()
        return

    print("\n[1/5] Ingesting 32M ratings dataset with explicit schema...")
    df = spark.read \
        .option("header", "true") \
        .schema(ratings_schema) \
        .csv(ratings_path)

    print("\n[2/5] Filtering sparse matrix: users with >= 15 ratings, movies with >= 20 ratings...")
    user_counts = df.groupBy("userId").agg(count("rating").alias("user_count")).filter(col("user_count") >= 15)
    movie_counts = df.groupBy("movieId").agg(count("rating").alias("movie_count")).filter(col("movie_count") >= 20)

    clean_df = df.join(user_counts, "userId").join(movie_counts, "movieId").select("userId", "movieId", "rating")

    print("\n[3/5] Splitting into Train (80%) and Validation (20%) sets...")
    (train_data, val_data) = clean_df.randomSplit([0.8, 0.2], seed=42)

    print("\n[4/5] Training Spark MLlib ALS Matrix Factorization Model...")
    als = ALS(
        userCol="userId",
        itemCol="movieId",
        ratingCol="rating",
        rank=16,
        maxIter=10,
        regParam=0.1,
        coldStartStrategy="drop",
        nonnegative=True,
        implicitPrefs=False
    )
    model = als.fit(train_data)

    print("Evaluating model on validation data...")
    predictions = model.transform(val_data)
    evaluator = RegressionEvaluator(metricName="rmse", labelCol="rating", predictionCol="prediction")
    rmse = evaluator.evaluate(predictions)
    print(f"Validation Root Mean Squared Error (RMSE): {rmse:.4f}")

    print("\n[5/5] Generating Top-20 recommendations...")
    if max_users:
        print(f"Generating for subset of {max_users:,} distinct users...")
        target_users = clean_df.select("userId").distinct().limit(max_users)
        user_recs = model.recommendForUserSubset(target_users, 20)
    else:
        print("Generating for all users...")
        user_recs = model.recommendForAllUsers(20)

    # Explode recommendations array into (userId, movieId, score)
    flattened_recs = user_recs.select(
        col("userId"),
        explode(col("recommendations")).alias("rec")
    ).select(
        col("userId"),
        col("rec.movieId").alias("movieId"),
        col("rec.rating").alias("score")
    )

    # Add rank per user based on score descending
    user_window = Window.partitionBy("userId").orderBy(col("score").desc())
    ranked_recs = flattened_recs.withColumn("rank", row_number().over(user_window))

    # Export to Parquet
    parquet_output_dir = "./data/processed/recommendations"
    os.makedirs(parquet_output_dir, exist_ok=True)
    print(f"Writing Parquet recommendation artifacts to: {parquet_output_dir}...")
    ranked_recs.write \
        .mode("overwrite") \
        .parquet(parquet_output_dir)

    print(f"Parquet export complete: {parquet_output_dir}")

    # Optional JDBC direct write to PostgreSQL
    if export_to_jdbc:
        pg_host = os.getenv("POSTGRES_HOST", "localhost")
        pg_port = os.getenv("POSTGRES_PORT", "5432")
        pg_db = os.getenv("POSTGRES_DB", "recommender_db")
        pg_user = os.getenv("POSTGRES_USER", "recommender_user")
        pg_password = os.getenv("POSTGRES_PASSWORD", "recommender_password")
        jdbc_url = f"jdbc:postgresql://{pg_host}:{pg_port}/{pg_db}"

        print(f"Exporting recommendations directly to PostgreSQL table via JDBC ({jdbc_url})...")
        jdbc_df = ranked_recs.select(
            col("userId").alias("user_id"),
            col("movieId").alias("movie_id"),
            col("score"),
            col("rank")
        )

        jdbc_properties = {
            "user": pg_user,
            "password": pg_password,
            "driver": "org.postgresql.Driver",
            "batchsize": "10000"
        }

        try:
            jdbc_df.write.jdbc(
                url=jdbc_url,
                table="api_recommendation",
                mode="append",
                properties=jdbc_properties
            )
            print("Successfully exported recommendations to PostgreSQL via JDBC.")
        except Exception as e:
            print(f"JDBC export failed or PostgreSQL offline: {e}")

    spark.stop()

if __name__ == "__main__":
    # By default, runs for 10,000 users for high performance local training & testing
    run_als_pipeline(export_to_jdbc=False, max_users=10000)
