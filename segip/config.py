class Config:
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://segip_user:segip_pass@localhost:3306/segip_db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False