import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.environ["COGNODB_URI"],
    auth=(os.environ["COGNODB_USER"], os.environ["COGNODB_PASSWORD"])
)

def test_connection():
    with driver.session() as session:
        result = session.run("RETURN 'hello cognodb' AS message")
        print(result.single()["message"])

test_connection()
driver.close()