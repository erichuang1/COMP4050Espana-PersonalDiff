# from Backend.server.src.models import models
from src.db_instance import db
from src.main import create_app
from src import models  
from insert_data import insert_data
import sys
if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        # db.drop_all()
        # Create the tables in the database using the ORM Models 
        db.create_all()
        # Ensure the tables are created via migration (not using create_all)
        # print("Inserting data into the database...")
        # Insert test data into the database
        insert_data()
    print("Database Intialisation finished!")
    # sys.exit(0)  # Force the script to exit cleanly
